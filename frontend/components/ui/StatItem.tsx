import React, { ReactNode } from "react";

interface StatItemProps {
  label: string;
  value: string | number;
  subLabel?: string;
  icon?: ReactNode;
  variant?: "default" | "risk" | "info" | "mitre";
}

export function StatItem({
  label,
  value,
  subLabel,
  icon,
  variant = "default",
}: StatItemProps) {
  const getTextColor = () => {
    switch (variant) {
      case "risk":
        return "text-[#E85D4E]";
      case "info":
        return "text-[#4A9EFF]";
      case "mitre":
        return "text-[#D4A94E]";
      default:
        return "text-[#E8EAED]";
    }
  };

  return (
    <div className="flex flex-col justify-between p-3.5 rounded-lg border border-[#222730] bg-[#14171C] hover:border-[#2F3642] transition-colors">
      <div className="flex items-center justify-between">
        <span className="text-[10px] uppercase font-mono tracking-wider text-[#8B92A0]">
          {label}
        </span>
        {icon && <span className="text-[#8B92A0]">{icon}</span>}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className={`text-xl font-bold font-mono tracking-tight ${getTextColor()}`}>
          {value}
        </span>
      </div>
      {subLabel && (
        <span className="text-[10px] font-mono text-[#8B92A0] mt-0.5 truncate">
          {subLabel}
        </span>
      )}
    </div>
  );
}
