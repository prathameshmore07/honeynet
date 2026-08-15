"use client";

import React from "react";
import { Shield, Radio, Activity, Cpu, Terminal, Play } from "lucide-react";

interface HeaderProps {
  wsConnected: boolean;
  ollamaStatus: string;
  cowrieStatus: string;
  onOpenSimulator: () => void;
}

export function Header({
  wsConnected,
  ollamaStatus,
  cowrieStatus,
  onOpenSimulator,
}: HeaderProps) {
  return (
    <header className="border-b border-slate-800 bg-[#0c1222]/90 backdrop-blur-md sticky top-0 z-40 px-6 py-3.5">
      <div className="max-w-[1720px] mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Branding & Status */}
        <div className="flex items-center gap-4">
          <div className="h-10 w-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.2)]">
            <Shield className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                HoneyNet <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">SOC 2.0</span>
              </h1>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-900 border border-slate-700 text-slate-300">
                <span
                  className={`h-2 w-2 rounded-full ${
                    wsConnected ? "bg-emerald-400 animate-pulse" : "bg-rose-500"
                  }`}
                />
                {wsConnected ? "LIVE STREAM ACTIVE" : "DISCONNECTED"}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              AI-Driven Adaptive Cyber Deception & Autonomous Honeytoken Infrastructure
            </p>
          </div>
        </div>

        {/* System Badges & Simulator Trigger */}
        <div className="flex items-center flex-wrap gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-300">
            <Radio className="h-3.5 w-3.5 text-cyan-400" />
            <span>Cowrie SSH:</span>
            <span className="font-semibold text-emerald-400">{cowrieStatus}</span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-300">
            <Cpu className="h-3.5 w-3.5 text-purple-400" />
            <span>Ollama AI:</span>
            <span className="font-semibold text-purple-300">{ollamaStatus}</span>
          </div>

          <button
            onClick={onOpenSimulator}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 text-white text-xs font-semibold shadow-lg shadow-cyan-950/40 border border-cyan-400/30 transition-all active:scale-95"
          >
            <Play className="h-3.5 w-3.5 fill-white" />
            Launch Attack Simulator
          </button>
        </div>
      </div>
    </header>
  );
}
