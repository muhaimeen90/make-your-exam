import os
from dotenv import load_dotenv

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.responses import StreamingResponse

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import shutil
import uuid
import fitz # PyMuPDF
import io
from ai import upload_to_cache, search_context, generate_pdf_instant

app = FastAPI(title="ExamForge API")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./storage/uploads")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./storage/generated")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Serve static files (uploaded PDFs/Images) for the frontend to access
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/generated", StaticFiles(directory=OUTPUT_DIR), name="generated")

# Store document metadata: { doc_id: { "files": [...uploaded files info...] } }
document_metadata = {}


class SearchQuery(BaseModel):
    query: str
    cache_id: str

class PageSelection(BaseModel):
    source_pdf: str  # Filename in UPLOAD_DIR
    page_number: int # 0-indexed
    crop_box: List[float] = None # [x, y, w, h] normalized (0-1)

class GenerateRequest(BaseModel):
    selections: List[PageSelection]

@app.get("/")
async def root():
    return {"message": "ExamForge API is running"}

@app.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Uploads PDFs, extracts text, and creates a Gemini Context Cache.
    Returns the cache_id and file metadata.
    """
    uploaded_files = []
    all_text_content = ""
    
    # Map to store page images: { "filename_pageIndex": "url_to_image" }
    # But simpler: just return the base URL pattern or a list of images per file.
    
    for file in files:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            print(f"Skipping non-PDF file: {file.filename}")
            continue

        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process PDF with PyMuPDF
        doc = fitz.open(file_path)
        file_text = ""
        
        # Create a directory for this file's page images to keep things organized
        # images_dir = os.path.join(UPLOAD_DIR, "images", file_id)
        # os.makedirs(images_dir, exist_ok=True)
        
        page_map = {}
        
        for page_num, page in enumerate(doc):
            # 1. Extract Text
            text = page.get_text()
            
            # Check for empty text (scanned page detection)
            if not text.strip():
                print(f"Warning: Page {page_num + 1} of {file.filename} appears to be empty or scanned image.")
                text = f"\n[WARNING: Page {page_num + 1} contains no extractable text - it may be an image or scanned document. The AI cannot read this page.]\n"
            
            # Add page marker for the AI to know where it is
            file_text += f"\n--- Page {page_num + 1} of {file.filename} ---\n{text}"
            
            # 2. Generate Image (High Res) - REMOVED for storage optimization
            # We now generate thumbnails on-the-fly via /thumbnail endpoint
            
            # URL to access this image (Dynamic)
            page_map[page_num + 1] = f"/thumbnail/{file_id}/{page_num}"
            
        page_count = doc.page_count
        doc.close()
        all_text_content += f"\n=== Document: {file.filename} ===\n{file_text}"
        
        uploaded_files.append({
            "filename": safe_filename,
            "original_name": file.filename,
            "id": file_id,
            "page_count": page_count,
            "pages": page_map
        })

    # Upload to Gemini Context Cache
    print("Uploading to Gemini Cache...")
    
    # Collect all PDF paths
    all_pdf_paths = []
    for f in uploaded_files:
        # We need absolute paths to the PDF files
        safe_filename = f["filename"]
        abs_path = os.path.join(UPLOAD_DIR, safe_filename)
        all_pdf_paths.append(abs_path)
            
    # Pass PDF paths instead of image paths
    cache_id = upload_to_cache(all_text_content, pdf_paths=all_pdf_paths)
    
    if not cache_id:
        # Fallback if cache creation fails (e.g. API key issue)
        print("Warning: Cache creation failed.")
        cache_id = "error_creating_cache"
    
    # Store file metadata for this document
    if cache_id != "error_creating_cache":
        document_metadata[cache_id] = {
            "files": uploaded_files
        }

    return {
        "status": "success",
        "cache_id": cache_id,
        "files": uploaded_files
    }

@app.get("/thumbnail/{file_id}/{page_num}")
async def get_thumbnail(file_id: str, page_num: int):
    """
    Generates a PNG thumbnail for a specific page of a PDF on-the-fly.
    """
    # Find the file with this ID
    # We don't have a direct DB, so we have to search the uploads dir or use metadata if available.
    # But wait, we saved files as {file_id}_{filename}.
    # Let's search for a file starting with file_id in UPLOAD_DIR.
    
    target_file = None
    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(file_id) and filename.endswith(".pdf"):
            target_file = os.path.join(UPLOAD_DIR, filename)
            break
            
    if not target_file:
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        doc = fitz.open(target_file)
        if page_num < 0 or page_num >= doc.page_count:
            doc.close()
            raise HTTPException(status_code=404, detail="Page not found")
            
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom
        img_data = pix.tobytes("png")
        doc.close()
        
        return StreamingResponse(io.BytesIO(img_data), media_type="image/png")
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        raise HTTPException(status_code=500, detail="Error generating thumbnail")

@app.post("/search")
async def search_documents(search_req: SearchQuery):
    """
    Searches the context cache for relevant questions.
    """
    print(f"Searching for: {search_req.query} in cache: {search_req.cache_id}")
    if search_req.cache_id == "error_creating_cache":
         return {"results": [], "error": "Cache was not created successfully."}

    results_json = search_context(search_req.query, search_req.cache_id)
    
    # ai.py returns a string (JSON), we need to parse it if it's a string, 
    # or if search_context already returns a dict/list.
    # Let's check ai.py. It returns response.text.
    # We should try to parse it here to ensure valid JSON for the frontend.
    import json
    import re
    
    try:
        # Clean up potential markdown code blocks ```json ... ```
        cleaned_json = re.sub(r"```json|```", "", results_json).strip()
        parsed_results = json.loads(cleaned_json)
        
        # Enrich results with image URLs
        print(f"Enriching results. cache_id: {search_req.cache_id}, metadata keys: {list(document_metadata.keys())}")
        if search_req.cache_id in document_metadata:
            files_info = document_metadata[search_req.cache_id]["files"]
            print(f"Found {len(files_info)} files in metadata")
            
            for result in parsed_results:
                page_num = result.get("page_number") or result.get("page")
                print(f"Processing result: page_num={page_num}, result={result}")
                
                # Find which file this page belongs to
                target_file_info = None
                source_filename = result.get("source_filename")
                
                if source_filename:
                    # Try to find exact match
                    for f_info in files_info:
                        if f_info["original_name"] == source_filename:
                            target_file_info = f_info
                            break
                
                # Fallback: If no filename returned or not found, use the first file (legacy behavior)
                # OR try to find which file has this page number if unique? No, that's risky.
                if not target_file_info and files_info:
                    print(f"Warning: Could not find file for {source_filename}, using first file.")
                    target_file_info = files_info[0]

                if target_file_info:
                    print(f"Mapped result to file: {target_file_info['original_name']}")
                    # Get the image URL for this page
                    if page_num and page_num in target_file_info.get("pages", {}):
                        result["image_url"] = target_file_info["pages"][page_num]
                        result["source_filename"] = target_file_info["original_name"]
                        print(f"Added image_url: {result['image_url']}")
                    else:
                        result["image_url"] = None
                        result["source_filename"] = target_file_info.get("original_name", "")
                        print(f"Page {page_num} not found in pages of {target_file_info['original_name']}")
        else:
            print(f"cache_id {search_req.cache_id} not found in metadata")
        
        return {"results": parsed_results}
    except Exception as e:
        print(f"Error parsing AI response: {e}")
        print(f"Raw response: {results_json}")
        return {"results": [], "error": "Failed to parse AI response"}


@app.post("/generate-pdf")
async def generate_pdf(req: GenerateRequest):
    """
    Creates a PDF from selected full pages.
    Pages are added in the order they appear in the selections list.
    """
    try:
        output_filename = f"exam_{uuid.uuid4()}.pdf"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # Create new PDF document
        output_doc = fitz.open()
        
        for sel in req.selections:
            # Resolve full path for source PDF
            # The frontend sends 'original_name', but we stored it as '{uuid}_{original_name}'
            # We need to find the file in UPLOAD_DIR that ends with _{original_name}
            full_path = None
            
            # First check if it exists exactly (legacy or if we start sending safe names)
            if os.path.exists(os.path.join(UPLOAD_DIR, sel.source_pdf)):
                full_path = os.path.join(UPLOAD_DIR, sel.source_pdf)
            else:
                # Search for it
                for f in os.listdir(UPLOAD_DIR):
                    if f.endswith(f"_{sel.source_pdf}"):
                        full_path = os.path.join(UPLOAD_DIR, f)
                        break
            
            if not full_path or not os.path.exists(full_path):
                print(f"Error: Source file {sel.source_pdf} not found in {UPLOAD_DIR}")
                raise HTTPException(status_code=404, detail=f"Source file {sel.source_pdf} not found")
            
            # Open source PDF and extract the page
            src_doc = fitz.open(full_path)
            
            # Validate page number
            if sel.page_number < 0 or sel.page_number >= src_doc.page_count:
                src_doc.close()
                raise HTTPException(status_code=400, detail=f"Invalid page number {sel.page_number}")
            
            page = src_doc[sel.page_number]
            
            # Apply crop if specified
            if sel.crop_box:
                # crop_box is [x, y, w, h] normalized (0-1)
                try:
                    rect = page.rect
                    x, y, w, h = sel.crop_box
                    
                    if w > 0 and h > 0:
                        x0 = rect.x0 + (x * rect.width)
                        y0 = rect.y0 + (y * rect.height)
                        x1 = rect.x0 + ((x + w) * rect.width)
                        y1 = rect.y0 + ((y + h) * rect.height)
                        
                        crop_rect = fitz.Rect(x0, y0, x1, y1)
                        page.set_cropbox(crop_rect)
                except Exception as e:
                    print(f"Error checking cropbox: {e}")
                    # Continue without cropping if error
            
            # Copy the full page to output document
            output_doc.insert_pdf(src_doc, from_page=sel.page_number, to_page=sel.page_number)
            
            src_doc.close()
        
        # Save the output PDF
        output_doc.save(output_path)
        output_doc.close()
        
        return {
            "status": "success",
            "download_url": f"/generated/{output_filename}"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
