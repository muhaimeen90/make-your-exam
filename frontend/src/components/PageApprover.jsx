import React, { useState } from 'react';
import { Plus, Check, Scissors } from 'lucide-react';
import CropperModal from './CropperModal';

const PageApprover = ({ imageUrl, pageNumber, questionInfo, onApprove }) => {
    const [isApproved, setIsApproved] = useState(false);
    const [isCropperOpen, setIsCropperOpen] = useState(false);

    const handleApprove = (crop = null) => {
        setIsApproved(true);
        // We pass the existing questionInfo PLUS the crop data if it exists
        // actually onApprove in App.jsx takes (result), so we might want to attach crop to result?
        // Or App.jsx should change signature.
        // Let's assume App.jsx's addToCart takes the result object. 
        // We will pass the crop data as a second argument or merge it?
        // simpler: pass the crop data to onApprove, and let parent handle merging.
        onApprove(crop);
        setTimeout(() => setIsApproved(false), 2000);
    };

    return (
        <div className="relative group">
            <div className="border-thick shadow-hard bg-white overflow-hidden transition-transform hover:-translate-y-1 hover:shadow-hard-lg">
                {/* Image Container */}
                <div className="relative aspect-[1/1.4] bg-slate-100">
                    <img
                        src={imageUrl}
                        alt={`Page ${pageNumber}`}
                        className="w-full h-full object-contain"
                        loading="lazy"
                    />

                    {/* Overlay on Hover */}
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100 gap-2">
                        <button
                            onClick={() => setIsCropperOpen(true)}
                            className="btn-primary flex items-center gap-2 scale-90 group-hover:scale-100 transition-transform px-3"
                            title="Crop"
                        >
                            <Scissors size={20} />
                        </button>
                        <button
                            onClick={() => handleApprove(null)}
                            className="btn-primary flex items-center gap-2 scale-90 group-hover:scale-100 transition-transform"
                        >
                            <Plus size={20} />
                            Add Full
                        </button>
                    </div>
                </div>

                {/* Quote Preview (Optional) */}
                {questionInfo.quote && (
                    <div className="p-3 border-t-2 border-black bg-slate-50 text-xs font-mono text-slate-600 truncate">
                        "{questionInfo.quote}"
                    </div>
                )}
            </div>

            {/* Success Feedback */}
            {isApproved && (
                <div className="absolute top-4 right-4 bg-[var(--memphis-teal)] text-white p-2 border-2 border-black shadow-hard z-10 animate-bounce">
                    <Check size={24} strokeWidth={3} />
                </div>
            )}

            <CropperModal
                imageUrl={imageUrl}
                isOpen={isCropperOpen}
                onClose={() => setIsCropperOpen(false)}
                onConfirm={(crop) => {
                    setIsCropperOpen(false);
                    handleApprove(crop);
                }}
            />
        </div>
    );
};

export default PageApprover;
