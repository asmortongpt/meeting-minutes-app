// frontend/src/hooks/useTouch.ts

import { useEffect, useRef, useState } from 'react';

/**
 * Interface defining the touch coordinates and state
 */
interface TouchState {
  startX: number;
  startY: number;
  currentX: number;
  currentY: number;
  isSwiping: boolean;
  direction: 'left' | 'right' | 'up' | 'down' | 'none';
}

/**
 * Options for configuring touch gesture behavior
 */
interface TouchOptions {
  threshold: number; // Minimum distance in pixels for a swipe to be recognized
  preventDefault: boolean; // Whether to prevent default browser behavior on touch
  verticalThreshold?: number; // Optional separate threshold for vertical swipes
}

/**
 * Custom hook for handling touch gestures with swipe detection
 * @param options Configuration for touch behavior
 * @returns Object containing swipe state and event handlers
 */
const useTouch = (options: TouchOptions = { threshold: 50, preventDefault: true }) => {
  const [touchState, setTouchState] = useState<TouchState>({
    startX: 0,
    startY: 0,
    currentX: 0,
    currentY: 0,
    isSwiping: false,
    direction: 'none',
  });

  const touchRef = useRef<HTMLElement | null>(null);

  // Calculate swipe direction based on touch coordinates
  const calculateDirection = (
    startX: number,
    startY: number,
    currentX: number,
    currentY: number
  ): TouchState['direction'] => {
    const deltaX = currentX - startX;
    const deltaY = currentY - startY;
    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);
    const verticalThreshold = options.verticalThreshold || options.threshold;

    if (absX > options.threshold && absX > absY) {
      return deltaX > 0 ? 'right' : 'left';
    } else if (absY > verticalThreshold && absY > absX) {
      return deltaY > 0 ? 'down' : 'up';
    }
    return 'none';
  };

  // Handle touch start event
  const handleTouchStart = (e: TouchEvent) => {
    try {
      if (options.preventDefault) {
        e.preventDefault();
      }

      const touch = e.touches[0];
      setTouchState((prev) => ({
        ...prev,
        startX: touch.clientX,
        startY: touch.clientY,
        currentX: touch.clientX,
        currentY: touch.clientY,
        isSwiping: true,
        direction: 'none',
      }));
    } catch (error) {
      console.error('Error handling touch start:', error);
    }
  };

  // Handle touch move event
  const handleTouchMove = (e: TouchEvent) => {
    try {
      if (!touchState.isSwiping) return;

      if (options.preventDefault) {
        e.preventDefault();
      }

      const touch = e.touches[0];
      const currentX = touch.clientX;
      const currentY = touch.clientY;

      const direction = calculateDirection(
        touchState.startX,
        touchState.startY,
        currentX,
        currentY
      );

      setTouchState((prev) => ({
        ...prev,
        currentX,
        currentY,
        direction,
      }));
    } catch (error) {
      console.error('Error handling touch move:', error);
    }
  };

  // Handle touch end event
  const handleTouchEnd = (e: TouchEvent) => {
    try {
      if (options.preventDefault) {
        e.preventDefault();
      }

      setTouchState((prev) => ({
        ...prev,
        isSwiping: false,
      }));
    } catch (error) {
      console.error('Error handling touch end:', error);
    }
  };

  // Set up event listeners for touch events
  useEffect(() => {
    const element = touchRef.current;
    if (!element) return;

    element.addEventListener('touchstart', handleTouchStart, { passive: false });
    element.addEventListener('touchmove', handleTouchMove, { passive: false });
    element.addEventListener('touchend', handleTouchEnd, { passive: false });

    // Cleanup event listeners on unmount
    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
      element.removeEventListener('touchend', handleTouchEnd);
    };
  }, [touchState.isSwiping]);

  return {
    touchRef, // Ref to attach to the target element
    isSwiping: touchState.isSwiping, // Whether a swipe is currently in progress
    direction: touchState.direction, // Current swipe direction
    deltaX: touchState.currentX - touchState.startX, // Horizontal distance moved
    deltaY: touchState.currentY - touchState.startY, // Vertical distance moved
  };
};

export default useTouch;