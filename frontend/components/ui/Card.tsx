import React, { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  header?: ReactNode;
  footer?: ReactNode;
}

export function Card({ children, className = "", header, footer }: CardProps) {
  return (
    <div
      className={`rounded-lg border border-[#222730] bg-[#14171C] shadow-lg overflow-hidden flex flex-col ${className}`}
    >
      {header && (
        <div className="px-4 py-2.5 border-b border-[#222730] bg-[#101318] flex items-center justify-between">
          {header}
        </div>
      )}
      <div className="flex-1 p-4">{children}</div>
      {footer && (
        <div className="px-4 py-2.5 border-t border-[#222730] bg-[#101318]">
          {footer}
        </div>
      )}
    </div>
  );
}
