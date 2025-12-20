// frontend/src/components/LoadingSkeleton.tsx
import React from 'react';
import styled, { css, keyframes } from 'styled-components';

// Define types for props to ensure type safety
interface LoadingSkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
  count?: number;
  className?: string;
}

// Animation for the shimmer effect to indicate loading
const shimmer = keyframes`
  0% {
    background-position: -200%;
  }
  100% {
    background-position: 200%;
  }
`;

// Styled component for the skeleton with dark mode support and responsive design
const Skeleton = styled.div<{
  width: string | number;
  height: string | number;
  borderRadius: string | number;
}>`
  background: ${({ theme }) =>
    theme.mode === 'dark'
      ? 'linear-gradient(90deg, #333 0%, #444 50%, #333 100%)'
      : 'linear-gradient(90deg, #f0f0f0 0%, #e0e0e0 50%, #f0f0f0 100%)'};
  background-size: 200% 100%;
  animation: ${shimmer} 1.5s ease-in-out infinite;
  width: ${({ width }) => (typeof width === 'number' ? `${width}px` : width)};
  height: ${({ height }) => (typeof height === 'number' ? `${height}px` : height)};
  border-radius: ${({ borderRadius }) =>
    typeof borderRadius === 'number' ? `${borderRadius}px` : borderRadius};
  margin-bottom: 10px;

  // Responsive design: adjust dimensions for smaller screens
  @media (max-width: 768px) {
    width: ${({ width }) => (typeof width === 'number' ? `${width * 0.9}px` : '90%')};
    height: ${({ height }) => (typeof height === 'number' ? `${height * 0.9}px` : '90%')};
  }
`;

// Wrapper for multiple skeleton items with flexbox for responsive layouts
const SkeletonWrapper = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 10px;

  @media (min-width: 768px) {
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: space-between;
  }
`;

/**
 * LoadingSkeleton component to display animated placeholders during data loading.
 * Supports dark mode, responsive design, and customizable dimensions.
 * @param props - Component props for customization
 * @returns JSX.Element - Rendered skeleton components
 */
const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  width = '100%',
  height = 20,
  borderRadius = 4,
  count = 1,
  className,
}) => {
  // Create an array of skeleton elements based on the count prop
  const skeletons = Array.from({ length: count }).map((_, index) => (
    <Skeleton
      key={`skeleton-${index}`}
      width={width}
      height={height}
      borderRadius={borderRadius}
      role="status"
      aria-label="Loading content"
    />
  ));

  // Return a single skeleton or a wrapper with multiple skeletons based on count
  return count > 1 ? (
    <SkeletonWrapper className={className}>{skeletons}</SkeletonWrapper>
  ) : (
    <>{skeletons}</>
  );
};

export default LoadingSkeleton;