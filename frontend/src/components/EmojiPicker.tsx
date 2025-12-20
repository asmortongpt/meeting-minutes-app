// frontend/src/components/EmojiPicker.tsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Smile } from 'lucide-react';
import { cn } from '@/lib/utils';

// Define types for emoji data and component props
interface Emoji {
  id: string;
  char: string;
  name: string;
}

interface EmojiCategory {
  id: string;
  name: string;
  emojis: Emoji[];
}

interface EmojiPickerProps {
  onEmojiSelect: (emoji: string) => void;
  className?: string;
  disabled?: boolean;
}

// Predefined emoji data with categories (subset for brevity, can be expanded or loaded from API)
const EMOJI_DATA: EmojiCategory[] = [
  {
    id: 'smileys',
    name: 'Smileys & Emotion',
    emojis: [
      { id: 'grinning', char: '😀', name: 'Grinning Face' },
      { id: 'smiling', char: '😊', name: 'Smiling Face with Smiling Eyes' },
      { id: 'laughing', char: '😂', name: 'Face with Tears of Joy' },
      { id: 'heart_eyes', char: '😍', name: 'Smiling Face with Heart-Eyes' },
    ],
  },
  {
    id: 'people',
    name: 'People & Body',
    emojis: [
      { id: 'wave', char: '👋', name: 'Waving Hand' },
      { id: 'thumbs_up', char: '👍', name: 'Thumbs Up' },
      { id: 'clap', char: '👏', name: 'Clapping Hands' },
    ],
  },
];

const EmojiPicker: React.FC<EmojiPickerProps> = ({
  onEmojiSelect,
  className = '',
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [categories, setCategories] = useState<EmojiCategory[]>([]);
  const [activeCategory, setActiveCategory] = useState<string>('smileys');
  const pickerRef = useRef<HTMLDivElement>(null);
  const touchStartRef = useRef<number>(0);

  // Load emoji data (simulated async for future API integration)
  useEffect(() => {
    setIsLoading(true);
    const timer = setTimeout(() => {
      setCategories(EMOJI_DATA);
      setIsLoading(false);
    }, 500);

    return () => clearTimeout(timer);
  }, []);

  // Close picker when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (pickerRef.current && !pickerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // Handle touch gestures for mobile swipe navigation
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    touchStartRef.current = e.touches[0].clientX;
  }, []);

  const handleTouchEnd = useCallback((e: React.TouchEvent) => {
    const touchEnd = e.changedTouches[0].clientX;
    const diff = touchStartRef.current - touchEnd;
    const threshold = 50; // Minimum swipe distance

    if (Math.abs(diff) > threshold) {
      const currentIndex = categories.findIndex((cat) => cat.id === activeCategory);
      if (diff > 0 && currentIndex < categories.length - 1) {
        // Swipe left, next category
        setActiveCategory(categories[currentIndex + 1].id);
      } else if (diff < 0 && currentIndex > 0) {
        // Swipe right, previous category
        setActiveCategory(categories[currentIndex - 1].id);
      }
    }
  }, [activeCategory, categories]);

  // Handle emoji selection with security in mind (sanitize input if needed)
  const handleEmojiClick = useCallback((emoji: string) => {
    try {
      onEmojiSelect(emoji);
      setIsOpen(false);
    } catch (error) {
      console.error('Error handling emoji selection:', error);
    }
  }, [onEmojiSelect]);

  // Animation variants for smooth transitions
  const pickerVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 10 },
  };

  // Loading skeleton component
  const LoadingSkeleton = () => (
    <div className="grid grid-cols-6 gap-2 p-4 animate-pulse">
      {Array.from({ length: 12 }).map((_, index) => (
        <div
          key={index}
          className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-md"
        />
      ))}
    </div>
  );

  return (
    <div className={cn('relative', className)} ref={pickerRef}>
      {/* Trigger Button with Accessibility */}
      <Button
        variant="outline"
        size="icon"
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        aria-label="Open emoji picker"
        className="cursor-pointer transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
      >
        <Smile className="h-5 w-5 text-gray-500 dark:text-gray-400" />
      </Button>

      {/* Emoji Picker Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial="hidden"
            animate="visible"
            exit="exit"
            variants={pickerVariants}
            transition={{ duration: 0.2 }}
            className="absolute right-0 mt-2 w-full max-w-xs sm:max-w-sm bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 overflow-hidden"
          >
            {/* Category Navigation */}
            <div className="flex overflow-x-auto border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
              {categories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => setActiveCategory(category.id)}
                  className={cn(
                    'px-4 py-2 text-sm font-medium transition-colors',
                    activeCategory === category.id
                      ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                      : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  )}
                  aria-label={`Switch to ${category.name} category`}
                >
                  {category.name}
                </button>
              ))}
            </div>

            {/* Emoji Grid with Touch Gestures */}
            <div
              className="max-h-60 sm:max-h-80 overflow-y-auto touch-pan-x"
              onTouchStart={handleTouchStart}
              onTouchEnd={handleTouchEnd}
            >
              {isLoading ? (
                <LoadingSkeleton />
              ) : (
                categories
                  .filter((cat) => cat.id === activeCategory)
                  .map((category) => (
                    <div key={category.id} className="p-4">
                      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        {category.name}
                      </h3>
                      <div className="grid grid-cols-6 sm:grid-cols-8 gap-2">
                        {category.emojis.map((emoji) => (
                          <motion.button
                            key={emoji.id}
                            whileHover={{ scale: 1.2 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={() => handleEmojiClick(emoji.char)}
                            className="w-10 h-10 flex items-center justify-center text-2xl cursor-pointer rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                            aria-label={`Select ${emoji.name}`}
                            role="img"
                          >
                            {emoji.char}
                          </motion.button>
                        ))}
                      </div>
                    </div>
                  ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default EmojiPicker;