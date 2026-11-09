import React from 'react';

interface VnptLogoProps {
  className?: string;
  size?: number;
  height?: number;
  variant?: 'blue' | 'white';
}

/**
 * Hiển thị logo VNPT từ thư mục /public (chuẩn Vite web static asset)
 * Không phụ thuộc vào đường dẫn tương đối import của TypeScript
 */
export const VnptLogo: React.FC<VnptLogoProps> = ({
  className = '',
  size = 46,
  height,
}) => {
  const calculatedHeight = height || size;

  return (
    <img
      src="/logo-vnpt.jpg"
      alt="VNPT Logo"
      style={{
        height: `${calculatedHeight}px`,
        width: 'auto',
        objectFit: 'contain',
      }}
      className={`inline-block select-none ${className}`}
    />
  );
};
