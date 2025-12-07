'use client';
import React, { useState, useRef, useEffect } from 'react';

interface TooltipProps {
    title: string;
    description: string;
    example?: string;
    children: React.ReactNode;
    delay?: number; // Hover delay in ms (default 500ms)
    position?: 'top' | 'bottom' | 'left' | 'right' | 'auto';
}

export const Tooltip: React.FC<TooltipProps> = ({
    title,
    description,
    example,
    children,
    delay = 500,
    position = 'auto'
}) => {
    const [isVisible, setIsVisible] = useState(false);
    const [calculatedPosition, setCalculatedPosition] = useState(position);
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);
    const tooltipRef = useRef<HTMLDivElement>(null);
    const triggerRef = useRef<HTMLDivElement>(null);

    const handleMouseEnter = () => {
        timeoutRef.current = setTimeout(() => {
            setIsVisible(true);
            if (position === 'auto') {
                calculatePosition();
            }
        }, delay);
    };

    const handleMouseLeave = () => {
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
        }
        setIsVisible(false);
    };

    const calculatePosition = () => {
        if (!triggerRef.current) return;

        const rect = triggerRef.current.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        // Determine best position based on available space
        const spaceAbove = rect.top;
        const spaceBelow = viewportHeight - rect.bottom;
        const spaceLeft = rect.left;
        const spaceRight = viewportWidth - rect.right;

        if (spaceBelow > 200) {
            setCalculatedPosition('bottom');
        } else if (spaceAbove > 200) {
            setCalculatedPosition('top');
        } else if (spaceRight > 300) {
            setCalculatedPosition('right');
        } else if (spaceLeft > 300) {
            setCalculatedPosition('left');
        } else {
            setCalculatedPosition('bottom');
        }
    };

    useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, []);

    const getPositionClasses = () => {
        const pos = position === 'auto' ? calculatedPosition : position;

        switch (pos) {
            case 'top':
                return 'bottom-full left-1/2 -translate-x-1/2 mb-2';
            case 'bottom':
                return 'top-full left-1/2 -translate-x-1/2 mt-2';
            case 'left':
                return 'right-full top-1/2 -translate-y-1/2 mr-2';
            case 'right':
                return 'left-full top-1/2 -translate-y-1/2 ml-2';
            default:
                return 'top-full left-1/2 -translate-x-1/2 mt-2';
        }
    };

    const getArrowClasses = () => {
        const pos = position === 'auto' ? calculatedPosition : position;

        switch (pos) {
            case 'top':
                return 'top-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-[#1a1d23]';
            case 'bottom':
                return 'bottom-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-[#1a1d23]';
            case 'left':
                return 'left-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent border-l-[#1a1d23]';
            case 'right':
                return 'right-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent border-r-[#1a1d23]';
            default:
                return 'bottom-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-[#1a1d23]';
        }
    };

    return (
        <div
            ref={triggerRef}
            className="relative inline-block"
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
        >
            {/* Trigger element */}
            <div className="cursor-help border-b border-dotted border-gray-500 inline-block">
                {children}
            </div>

            {/* Tooltip */}
            {isVisible && (
                <div
                    ref={tooltipRef}
                    className={`absolute z-[9999] ${getPositionClasses()} animate-in fade-in duration-200`}
                    role="tooltip"
                >
                    {/* Arrow */}
                    <div className={`absolute w-0 h-0 border-[6px] ${getArrowClasses()}`} />

                    {/* Tooltip content */}
                    <div className="bg-[#1a1d23] border border-[#2a2d33] rounded-lg shadow-2xl p-4 max-w-xs min-w-[280px]">
                        {/* Title */}
                        <div className="text-[#5794F2] font-bold text-sm mb-2 flex items-center gap-2">
                            <span className="text-xs">ℹ️</span>
                            {title}
                        </div>

                        {/* Description */}
                        <div className="text-gray-300 text-xs leading-relaxed mb-2">
                            {description}
                        </div>

                        {/* Example (if provided) */}
                        {example && (
                            <div className="mt-3 pt-3 border-t border-gray-700">
                                <div className="text-[10px] text-gray-500 uppercase mb-1">Example:</div>
                                <div className="text-xs text-amber-400 font-mono">
                                    {example}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};
