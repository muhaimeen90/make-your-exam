import React, { useState, useRef, useEffect } from 'react';
import ReactCrop, { centerCrop, makeAspectCrop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import { X, Check, Scissors } from 'lucide-react';

// Helper to center the crop initially
function centerAspectCrop(mediaWidth, mediaHeight, aspect) {
    return centerCrop(
        makeAspectCrop(
            {
                unit: '%',
                width: 90,
            },
            aspect,
            mediaWidth,
            mediaHeight,
        ),
        mediaWidth,
        mediaHeight,
    )
}

const CropperModal = ({ imageUrl, isOpen, onClose, onConfirm }) => {
    const [crop, setCrop] = useState();
    const [completedCrop, setCompletedCrop] = useState();
    const [aspect, setAspect] = useState(undefined) // Free crop by default
    const imgRef = useRef(null);

    useEffect(() => {
        if (isOpen) {
            setCrop(undefined); // Reset crop when modal opens
            setCompletedCrop(undefined);
        }
    }, [isOpen]);

    function onImageLoad(e) {
        if (aspect) {
            const { width, height } = e.currentTarget
            setCrop(centerAspectCrop(width, height, aspect))
        }
    }

    const handleConfirm = () => {
        // If no crop is selected but confirm is clicked, maybe just return full image or nothing?
        // But typically user should select something.
        // If completedCrop is there, we normalize it to percents for backend portability?
        // Or keep pixels? The library gives pixels and percents.
        // Backend (PyMuPDF) works best with normalized coordinates (0.0 to 1.0).

        if (!completedCrop || !imgRef.current) {
            onConfirm(null); // No crop applied
            return;
        }

        const image = imgRef.current;
        const { width, height } = image;

        // Calculate normalized coordinates
        // x, y, width, height as fraction of total image size
        const normalizedCrop = {
            x: completedCrop.x / width,
            y: completedCrop.y / height,
            width: completedCrop.width / width,
            height: completedCrop.height / height
        };

        onConfirm(normalizedCrop);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-white max-w-4xl w-full max-h-[90vh] flex flex-col border-thick shadow-hard-lg overflow-hidden animate-in fade-in zoom-in duration-200">

                {/* Header */}
                <div className="p-4 bg-[var(--memphis-yellow)] border-b-2 border-black flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <Scissors size={20} className="text-black" />
                        <h2 className="font-black uppercase text-lg">Crop Question</h2>
                    </div>
                    <button onClick={onClose} className="p-1 hover:bg-black hover:text-white transition-colors border-2 border-transparent hover:border-black rounded-none">
                        <X size={24} />
                    </button>
                </div>

                {/* content */}
                <div className="flex-1 overflow-auto p-6 bg-slate-100 flex items-center justify-center">
                    <ReactCrop
                        crop={crop}
                        onChange={(_, percentCrop) => setCrop(percentCrop)}
                        onComplete={(c) => setCompletedCrop(c)}
                        aspect={aspect}
                        className="max-h-[70vh]"
                    >
                        <img
                            ref={imgRef}
                            alt="Crop me"
                            src={imageUrl}
                            onLoad={onImageLoad}
                            style={{ maxHeight: '70vh', width: 'auto' }}
                        />
                    </ReactCrop>
                </div>

                {/* Footer */}
                <div className="p-4 border-t-2 border-black bg-white flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 font-bold border-2 border-transparent hover:bg-slate-100 transition-colors uppercase text-sm"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleConfirm}
                        className="px-6 py-2 bg-black text-white font-bold border-2 border-black shadow-hard-sm hover:translate-x-1 transition-transform flex items-center gap-2 uppercase text-sm"
                    >
                        <Check size={18} />
                        Confirm Crop
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CropperModal;
