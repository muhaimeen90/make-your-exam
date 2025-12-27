import os
import google.generativeai as genai
from datetime import datetime
import uuid
import fitz # PyMuPDF
import io


# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# In-memory storage for document contents (replaces caching)
# Structure: { document_id: { "content": text, "timestamp": datetime } }
document_store = {}

def estimate_tokens(text):
    """
    Estimates the number of tokens in a text string.
    Rule of thumb: 1 token ~= 4 characters.
    """
    if not text:
        return 0
    return len(text) // 4

def estimate_image_tokens(num_images):
    """
    Estimates tokens for images.
    Gemini 1.5 Flash uses approx 258 tokens per image.
    """
    return num_images * 258


def upload_to_cache(text_content, pdf_paths=None, ttl_minutes=60):
    """
    Stores text content in memory instead of using Gemini's cache.
    Returns a unique document ID.
    """
    try:
        # Generate a unique document ID
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        
        # Store the document content in memory
        document_store[doc_id] = {
            "content": text_content,
            "pdfs": pdf_paths or [],
            "timestamp": datetime.now()
        }
        
        # Check document size
        text_tokens = estimate_tokens(text_content)
        
        # Estimate image tokens (we need to know total pages)
        total_pages = 0
        for path in (pdf_paths or []):
            try:
                doc = fitz.open(path)
                total_pages += doc.page_count
                doc.close()
            except:
                pass
                
        image_tokens = estimate_image_tokens(total_pages)
        total_tokens = text_tokens + image_tokens
        
        print(f"Document size: {len(text_content)} chars, {total_pages} pages (~{total_tokens} tokens)")
        
        # Warn if document is very large (e.g. > 800k tokens)
        # Gemini 1.5 Pro has 1M-2M context, but Flash is smaller or we want to be safe.
        SAFE_LIMIT = 800000
        if total_tokens > SAFE_LIMIT:
            print(f"WARNING: Document exceeds safe token limit ({total_tokens} > {SAFE_LIMIT}).")
            # We could reject here, but for now let's just warn and maybe truncate if needed in future.
            # For this user request, we just want to prevent "too much pdf".
        
        return doc_id
    except Exception as e:
        print(f"Error storing document: {e}")
        return "error_creating_cache"

def search_context(query, doc_id):
    """
    Searches the stored document using Gemini's generative model.
    Sends the full document content with each request instead of using cache.
    """
    # Check if document exists in store
    if doc_id is None or doc_id == "error_creating_cache":
        print(f"Searching for: {query} in doc: {doc_id}")
        print("Warning: Document was not stored successfully. Cannot perform search.")
        return "[]"
    
    if doc_id not in document_store:
        print(f"Error: Document ID {doc_id} not found in store")
        return "[]"
    
    try:
        print(f"Searching for: {query} in document: {doc_id}")
        
        # Get the stored document content
        doc_data = document_store[doc_id]
        text_content = doc_data["content"]
        pdf_paths = doc_data.get("pdfs", [])
        
        # Load images from PDFs in-memory
        import PIL.Image
        images = []
        
        for path in pdf_paths:
            try:
                if os.path.exists(path):
                    doc = fitz.open(path)
                    for page in doc:
                        # Render page to image
                        pix = page.get_pixmap(matrix=fitz.Matrix(1, 1)) # Standard resolution for AI is fine
                        img_data = pix.tobytes("png")
                        images.append(PIL.Image.open(io.BytesIO(img_data)))
                    doc.close()
            except Exception as e:
                print(f"Error loading PDF {path}: {e}")


        
        # Create a generative model instance
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Check total tokens before sending
        # Prompt template is small, main bulk is text_content
        total_tokens = estimate_tokens(text_content) + estimate_image_tokens(len(images)) + estimate_tokens(query) + 500
        
        if total_tokens > 1000000: # 1M token limit for Flash
             print(f"Error: Prompt too large ({total_tokens} tokens). limit is 1M.")
             return "[]" # Return empty results if too large

        
        # Create the prompt with the document content and search query
        prompt = f"""
You are analyzing exam documents. I have provided the full text content AND images of every page.
Use the images to understand diagrams, graphs, and layout. Use the text to read specific details.

DOCUMENT CONTENT:
{text_content}

TASK:
Find questions related to: "{query}".

CRITICAL QUALITY REQUIREMENTS:

1. **Universal Accuracy Check (The "Asking vs Answering" Rule)**:
   - You must distinguish between a page that **asks** a question and a page that provides space to **answer** it.
   - **INCLUDE** the page ONLY if it contains the **statement of the problem**. Look for:
     - Imperative commands (e.g., "Calculate", "Show that", "Explain", "Find").
     - Core data, equations, or diagrams defining the problem.
   - **EXCLUDE** the page if it is an "Answer Page":
     - Pages that only contain headers like "Question 3 continued" followed by blank lines, empty grids, or ruled space.
     - Pages that only contain working space without defining a new part of the question.

2. **Verify Relevance**: ONLY return pages that actually contain questions matching "{query}".
   - Ignore syllabus lists, table of contents, or headers that mention the topic but are not questions.

3. **Quote Verification (Anti-Hallucination)**:
   - You MUST extract the **exact text** of the question start to prove it exists on this page.
   - The quote MUST come from the **problem definition**, not a header or footer.
   - If you cannot find the exact text to quote, DO NOT return the result.

4. **Accurate Descriptions**: The description MUST precisely match the question content.
   - Include the main topic and specific subtopics.
   - Use the exact question number from the document.
   - Example: "Q4: Differentiation - chain rule"
   
5. **No Empty Results**: Never return a page if you cannot clearly identify a matching question.

6. **Group Sub-Questions**: Questions with parts (4a, 4b, 4c) should be ONE result.

7. **Source Identification**: You MUST identify which file the page belongs to.
   - Extract the filename from the header "--- Page X of [filename] ---".

Return a JSON list of objects, where each object has:
- "page_number": The page number (1-indexed) where the question appears.
- "source_filename": The name of the file containing this page (e.g., "exam_paper_1.pdf").
- "question_index": The question number or identifier exactly as shown in the document.
- "description": A precise summary including the topic and what the question asks.
- "quote": The exact text snippet from the start of the question to prove it exists.

EXAMPLE GOOD OUTPUT:
[
  {{"page_number": 3, "question_index": "Q4", "description": "Differentiation - chain rule", "quote": "4. (a) Differentiate y = x^2 sin(x) with respect to x."}},
  {{"page_number": 5, "question_index": "Q7", "description": "Graph interpretation", "quote": "7. The diagram shows the curve y = f(x). Find the coordinates..."}}
]

IMPORTANT: Only return the JSON array, no markdown formatting or code blocks.
If no relevant questions are found, return an empty array: []
"""
        
        # Generate content with the model (Multimodal)
        # Pass prompt string AND list of images
        content_parts = [prompt] + images
        response = model.generate_content(content_parts)
        
        print(f"AI Response received: {len(response.text)} characters")
        return response.text
        
    except Exception as e:
        print(f"Error searching context: {e}")
        return "[]"

def cleanup_old_documents(max_age_minutes=120):
    """
    Optional: Remove old documents from memory to prevent unlimited growth.
    Call this periodically if needed.
    """
    current_time = datetime.now()
    to_remove = []
    
    for doc_id, doc_data in document_store.items():
        age = (current_time - doc_data["timestamp"]).total_seconds() / 60
        if age > max_age_minutes:
            to_remove.append(doc_id)
    
    for doc_id in to_remove:
        del document_store[doc_id]
        print(f"Cleaned up old document: {doc_id}")
    
    return len(to_remove)

def generate_pdf_instant(query, doc_id):
    """
    Uses AI to find relevant pages for instant PDF generation.
    Returns a list of page numbers that match the query.
    """
    # First, use search_context to find matching pages
    results_json = search_context(query, doc_id)
    
    try:
        import json
        import re
        
        # Clean up potential markdown code blocks
        cleaned_json = re.sub(r"```json|```", "", results_json).strip()
        parsed_results = json.loads(cleaned_json)
        
        # Extract page numbers from results
        page_selections = []
        for result in parsed_results:
            page_num = result.get("page_number")
            if page_num:
                page_selections.append({
                    "page_number": page_num - 1,  # Convert to 0-indexed
                    "description": result.get("description", ""),
                    "question_index": result.get("question_index", "")
                })
        
        return page_selections
    except Exception as e:
        print(f"Error parsing instant PDF results: {e}")
        return []
