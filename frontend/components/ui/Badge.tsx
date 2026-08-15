import React, { ReactNode } from "react";

type BadgeVariant = "default" | "risk" | "info" | "mitre" | "success" | "neutral";

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

export function Badge({ children, variant = "default", className = "" }: BadgeProps) {
  const getStyles = () => {
    switch (variant) {
      case "risk":
        return "bg-[#E85D4E]/10 border-[#E85D4E]/40 text-[#E85D4E]";
      case "info":
        return "bg-[#4A9EFF]/10 border-[#4A9EFF]/40 text-[#4A9EFF]";
      case "mitre":
        return "bg-[#D4A94E]/10 border-[#D4A94E]/40 text-[#D4A94E]";
      case "success":
        return "bg-[#36B37E]/10 border-[#36B37E]/40 text-[#36B37E]";
      case "neutral":
        return "bg-[#1E232B] border-[#2E3642] text-[#8B92A0]";
      default:
        return "bg-[#191D24] border-[#222730] text-[#E8EAED]";
    }
  };

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium border ${getStyles()} ${className}`}
    >
      {children}
    </span>
  );
}
