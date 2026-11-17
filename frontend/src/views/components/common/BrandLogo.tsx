import React from 'react';

interface BrandLogoProps {
  className?: string;
  size?: number;
  height?: number;
  variant?: 'blue' | 'white';
}

/**
 * Hiển thị logo từ thư mục /public (chuẩn Vite web static asset)
 * Không phụ thuộc vào đường dẫn tương đối import của TypeScript
 */
export const BrandLogo: React.FC<BrandLogoProps> = ({
  className = '',
  size = 46,
  height,
}) => {
  const calculatedHeight = height || size;

  return (
    <img
      src="/logo-brand.jpg"
      alt="Brand Logo"
      style={{
        height: `${calculatedHeight}px`,
        width: 'auto',
        objectFit: 'contain',
      }}
      className={`inline-block select-none ${className}`}
    />
  );
};
