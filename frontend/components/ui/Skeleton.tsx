import React from "react";

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded bg-[#191D24] border border-[#222730]/60 ${className}`}
    />
  );
}
