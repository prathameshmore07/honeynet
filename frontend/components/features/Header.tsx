"use client";

import React from "react";
import { Shield, Play, Activity, Server, Cpu } from "lucide-react";
import { Badge } from "@/components/ui/Badge";

interface HeaderProps {
  wsConnected: boolean;
  latencyMs: number | null;
  ollamaStatus: string;
  cowrieStatus: string;
  onOpenSimulator: () => void;
}

export function Header({
  wsConnected,
  latencyMs,
  ollamaStatus,
  cowrieStatus,
  onOpenSimulator,
}: HeaderProps) {
  return (
    <header className="border-b border-[#222730] bg-[#101318]/95 backdrop-blur-md sticky top-0 z-40 px-6 py-3">
      <div className="max-w-[1780px] mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Branding & Status */}
        <div className="flex items-center gap-3.5">
          <div className="h-9 w-9 rounded-lg bg-[#191D24] border border-[#222730] flex items-center justify-center text-[#4A9EFF] shadow-inner">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-base font-bold tracking-tight text-[#E8EAED] font-mono flex items-center gap-2">
                HONEYNET <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#191D24] text-[#4A9EFF] border border-[#222730]">FORENSICS LAB</span>
              </h1>
              <Badge variant={wsConnected ? "success" : "risk"}>
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    wsConnected ? "bg-[#36B37E] animate-pulse" : "bg-[#E85D4E]"
                  }`}
                />
                {wsConnected ? "TELEMETRY ACTIVE" : "OFFLINE"}
                {wsConnected && latencyMs !== null && (
                  <span className="text-[10px] text-[#8B92A0] ml-1">({latencyMs}ms)</span>
                )}
              </Badge>
            </div>
            <p className="text-[11px] text-[#8B92A0]">
              Autonomous Cyber Deception & Forensic Intent Attribution Core
            </p>
          </div>
        </div>

        {/* System Badges & Actions */}
        <div className="flex items-center flex-wrap gap-2.5">
          <div className="flex items-center gap-2 px-2.5 py-1 rounded border border-[#222730] bg-[#14171C] text-xs font-mono text-[#8B92A0]">
            <Server className="h-3.5 w-3.5 text-[#4A9EFF]" />
            <span>Cowrie SSH:</span>
            <span className="text-[#36B37E] font-medium">{cowrieStatus}</span>
          </div>

          <div className="flex items-center gap-2 px-2.5 py-1 rounded border border-[#222730] bg-[#14171C] text-xs font-mono text-[#8B92A0]">
            <Cpu className="h-3.5 w-3.5 text-[#D4A94E]" />
            <span>Ollama AI:</span>
            <span className="text-[#E8EAED] font-medium">{ollamaStatus}</span>
          </div>

          <button
            onClick={onOpenSimulator}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded border border-[#4A9EFF]/40 bg-[#4A9EFF]/15 hover:bg-[#4A9EFF]/25 text-[#4A9EFF] hover:text-white text-xs font-mono font-semibold transition-all active:scale-95 cursor-pointer"
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            Trigger Simulation
          </button>
        </div>
      </div>
    </header>
  );
}
