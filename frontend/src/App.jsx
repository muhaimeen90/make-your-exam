import React, { useState } from 'react';
import { Upload, Search, FileText, Layers, ShoppingCart, Trash2, FileDown, Plus, Scissors } from 'lucide-react';
import PageApprover from './components/PageApprover';

function App() {
  const [files, setFiles] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [cart, setCart] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [cacheId, setCacheId] = useState(null);

  const handleUpload = async (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length === 0) return;

    setIsProcessing(true);
    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();

      if (data.status === 'success') {
        setCacheId(data.cache_id);
        setFiles(data.files);
      }
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Upload failed. See console.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery || !cacheId) return;

    setIsProcessing(true);
    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, cache_id: cacheId })
      });
      const data = await response.json();

      if (data.results) {
        setSearchResults(data.results);
      }
    } catch (error) {
      console.error("Search failed:", error);
    } finally {
      setIsProcessing(false);
    }
  };

  const addToCart = (result, crop = null) => {
    const newItem = {
      id: Date.now(),
      source_pdf: result.source_filename || (files.length > 0 ? files[0].filename : ''),
      page_number: (result.page_number || result.page) - 1,
      order: cart.length,
      description: result.description,
      crop_box: crop
    };
    setCart([...cart, newItem]);
  };

  const removeFromCart = (id) => {
    setCart(cart.filter(item => item.id !== id));
  };

  const generatePDF = async () => {
    if (cart.length === 0) return;

    setIsProcessing(true);
    try {
      const sortedSelections = cart.sort((a, b) => a.order - b.order);

      const response = await fetch('/api/generate-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selections: sortedSelections.map(s => ({
            source_pdf: s.source_pdf,
            page_number: s.page_number,
            crop_box: s.crop_box ? [s.crop_box.x, s.crop_box.y, s.crop_box.width, s.crop_box.height] : null
          }))
        })
      });
      const data = await response.json();
      if (data.status === 'success') {
        window.open(data.download_url, '_blank');
        setCart([]);
      }
    } catch (error) {
      console.error("Generation failed", error);
      alert("PDF generation failed. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  const getImageUrl = (result) => {
    return result.image_url || null;
  };

  return (
    <div className="min-h-screen flex bg-[var(--memphis-bg)] font-sans text-[var(--memphis-black)]">
      {/* Sidebar */}
      <aside className="w-72 bg-[var(--memphis-bg)] border-r-2 border-black flex flex-col h-screen sticky top-0 z-10">
        {/* Brand */}
        <div className="p-6 border-b-2 border-black bg-[var(--memphis-yellow)]">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-black tracking-tight">make-your-exam</h1>
          </div>
        </div>



        {/* Cart */}
        <div className="flex-1 flex flex-col p-4 overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-black uppercase tracking-wider text-sm flex items-center gap-2">
              <ShoppingCart size={16} />
              Cart ({cart.length})
            </h3>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
            {cart.length === 0 ? (
              <div className="text-center py-8 text-slate-400 italic text-xs border-2 border-dashed border-slate-300 bg-slate-50">
                No questions selected
              </div>
            ) : (
              cart.map((item, idx) => (
                <div key={item.id} className="p-2 bg-white border-2 border-black shadow-hard-sm flex justify-between items-start group hover:bg-slate-50 transition-colors">
                  <div className="overflow-hidden">
                    <div className="font-bold text-xs flex items-center gap-2">
                      Q{idx + 1} - Page {item.page_number + 1}
                      {item.crop_box && <Scissors size={12} className="text-pink-500" />}
                    </div>
                    <div className="text-[10px] text-slate-500 truncate w-32" title={item.source_pdf}>{item.source_pdf}</div>
                  </div>
                  <button
                    onClick={() => removeFromCart(item.id)}
                    className="text-slate-400 hover:text-red-600 transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))
            )}
          </div>

          <button
            onClick={generatePDF}
            disabled={isProcessing || cart.length === 0}
            className="mt-4 w-full btn-accent py-3 text-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:shadow-none disabled:translate-y-0"
          >
            {isProcessing ? 'Generating...' : (
              <>
                <FileDown size={18} />
                GENERATE PDF
              </>
            )}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`flex-1 p-6 overflow-y-auto h-screen transition-all duration-500 ease-in-out ${searchResults.length > 0 ? '' : 'flex items-center justify-center'}`}>
        <div className={`max-w-6xl mx-auto space-y-6 w-full transition-all duration-700 ease-out ${searchResults.length > 0 ? 'translate-y-0 opacity-100' : 'scale-110'}`}>

          {/* Top Bar: Upload & Search */}
          <div className="grid grid-cols-12 gap-6">
            {/* Upload Area */}
            <div className="col-span-12 md:col-span-4">
              <div className="card-memphis bg-white h-full flex flex-col justify-center">
                <label className={`flex flex-col items-center justify-center w-full h-24 border-2 border-dashed border-black bg-slate-50 cursor-pointer hover:bg-[var(--memphis-yellow)] transition-colors group ${isProcessing ? 'opacity-50 pointer-events-none' : ''}`}>
                  <div className="flex flex-col items-center justify-center">
                    <Upload className="w-6 h-6 text-black mb-1 group-hover:scale-110 transition-transform" />
                    <p className="text-xs font-bold uppercase">Upload PDF</p>
                  </div>
                  <input type="file" className="hidden" multiple onChange={handleUpload} disabled={isProcessing} />
                </label>
                {files.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {files.map((f, i) => (
                      <div key={i} className="text-[10px] font-bold bg-black text-white px-2 py-1 truncate max-w-full shadow-hard-sm">
                        {f.original_name}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Search Area */}
            <div className="col-span-12 md:col-span-8">
              <div className="card-memphis bg-[var(--memphis-teal)] h-full flex flex-col justify-center relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10 pointer-events-none">
                  <Search size={120} className="text-white" />
                </div>
                <h2 className="text-2xl font-black text-black mb-3 drop-shadow-[2px_2px_0_rgba(255,255,255,1)] uppercase">Find Questions</h2>
                <div className="flex gap-0 relative z-10">
                  <textarea
                    placeholder="e.g. 'Find calculus questions from 2023' (Press Enter to search)"
                    className="flex-1 px-4 py-3 border-thick shadow-hard text-base font-medium focus:outline-none focus:bg-[var(--memphis-yellow)] transition-colors placeholder:text-slate-500 resize-none overflow-hidden min-h-[52px]"
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      e.target.style.height = 'auto';
                      e.target.style.height = e.target.scrollHeight + 'px';
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSearch();
                      }
                    }}
                  />
                  <button
                    onClick={handleSearch}
                    disabled={isProcessing || !cacheId}
                    className="px-6 bg-black text-white font-bold hover:bg-slate-800 transition-colors disabled:opacity-50 border-thick border-l-0 shadow-hard"
                  >
                    <Search size={20} />
                  </button>
                </div>
                {!cacheId && files.length > 0 && !isProcessing && (
                  <p className="text-xs font-bold text-red-900 bg-red-100 px-2 py-1 border-2 border-red-900 inline-block self-start mt-2">
                    Upload failed or cache not ready.
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Results Area */}
          <div className="min-h-[400px]">
            {searchResults.length > 0 && (
              <div className="flex items-center gap-4 mb-4">
                <div className="h-0.5 flex-1 bg-black"></div>
                <h3 className="text-sm font-black uppercase bg-[var(--memphis-pink)] text-white px-3 py-1 border-thick shadow-hard-sm">
                  Results ({searchResults.length})
                </h3>
                <div className="h-0.5 flex-1 bg-black"></div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-12">
              {searchResults.map((result, idx) => {
                const imageUrl = getImageUrl(result);
                const pageNum = result.page_number || result.page;

                return (
                  <div key={idx} className="group flex flex-col">
                    <div className="mb-2 flex justify-between items-end">
                      <span className="font-bold text-lg leading-tight bg-white border-2 border-black px-2 shadow-hard-sm inline-block max-w-[85%] break-words whitespace-normal">
                        {result.description}
                      </span>
                      <span className="text-[10px] font-bold bg-black text-white px-2 py-1">
                        Page {pageNum}
                      </span>
                    </div>

                    {imageUrl ? (
                      <PageApprover
                        imageUrl={imageUrl}
                        pageNumber={pageNum}
                        questionInfo={result}
                        onApprove={(crop) => addToCart(result, crop)}
                      />
                    ) : (
                      <div className="aspect-[1/1.4] bg-slate-100 border-thick flex items-center justify-center text-slate-400 font-bold text-xs">
                        Image not found
                      </div>
                    )}
                  </div>
                )
              })}

              {/* Empty State */}
              {searchResults.length === 0 && (
                <div className="col-span-full flex flex-col items-center justify-center py-12 opacity-60">
                  {files.length === 0 ? (
                    <div className="text-center">
                      <div className="w-16 h-16 bg-slate-200 rounded-full flex items-center justify-center mx-auto mb-4 border-2 border-black">
                        <Upload size={24} className="text-slate-500" />
                      </div>
                      <h3 className="text-lg font-bold text-slate-700">No Papers Uploaded</h3>
                      <p className="text-sm text-slate-500">Upload a PDF to start building your exam.</p>
                    </div>
                  ) : (
                    <div className="text-center">
                      <div className="w-16 h-16 bg-[var(--memphis-yellow)] rounded-full flex items-center justify-center mx-auto mb-4 border-thick shadow-hard-sm">
                        <Search size={24} className="text-black" />
                      </div>
                      <h3 className="text-lg font-bold text-black">Ready to Search</h3>
                      <p className="text-sm text-slate-600">Type a query above to find questions.</p>
                    </div>
                  )}
                </div>
              )}

              {isProcessing && (
                <div className="col-span-full flex justify-center py-12">
                  <div className="animate-bounce text-xl font-black bg-[var(--memphis-yellow)] px-6 py-3 border-thick shadow-hard">
                    PROCESSING...
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
