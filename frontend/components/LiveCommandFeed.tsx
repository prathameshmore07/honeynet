"use client";

import React, { useState, useEffect, useRef } from "react";
import { Terminal, Filter, Pause, Play, Trash2, ShieldAlert, Sparkles } from "lucide-react";

export interface CommandEventItem {
  id?: number;
  session_id: string;
  src_ip: string;
  command: string;
  category: string;
  classification_method?: string;
  files_served?: string[];
  mitre_tag?: string;
  mitre_name?: string;
  event_risk_score?: number;
  session_risk_score?: number;
  timestamp: string;
}

interface LiveCommandFeedProps {
  events: CommandEventItem[];
  onClear: () => void;
  selectedSession: string | null;
  onSelectSession: (sessionId: string) => void;
}

export function LiveCommandFeed({
  events,
  onClear,
  selectedSession,
  onSelectSession,
}: LiveCommandFeedProps) {
  const [filterCat, setFilterCat] = useState<string>("all");
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const feedEndRef = useRef<HTMLDivElement>(null);

  const categories = ["all", "finance", "git", "aws", "hr", "database", "other"];

  const filteredEvents = events.filter((e) => {
    const matchesCat = filterCat === "all" || e.category === filterCat;
    const matchesSearch =
      !searchQuery ||
      e.command.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.session_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.src_ip.includes(searchQuery);
    const matchesSession = !selectedSession || e.session_id === selectedSession;
    return matchesCat && matchesSearch && matchesSession;
  });

  useEffect(() => {
    if (!isPaused && feedEndRef.current) {
      feedEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [events, isPaused]);

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case "finance":
        return "bg-emerald-950/80 text-emerald-300 border-emerald-800/60";
      case "git":
        return "bg-cyan-950/80 text-cyan-300 border-cyan-800/60";
      case "aws":
        return "bg-amber-950/80 text-amber-300 border-amber-800/60";
      case "hr":
        return "bg-purple-950/80 text-purple-300 border-purple-800/60";
      case "database":
        return "bg-blue-950/80 text-blue-300 border-blue-800/60";
      default:
        return "bg-slate-800 text-slate-400 border-slate-700";
    }
  };

  const getRiskColor = (score?: number) => {
    const s = score || 10;
    if (s >= 75) return "text-rose-400 bg-rose-950/60 border-rose-800";
    if (s >= 40) return "text-amber-400 bg-amber-950/60 border-amber-800";
    return "text-cyan-400 bg-cyan-950/60 border-cyan-800";
  };

  return (
    <div className="flex flex-col h-[520px] rounded-xl border border-slate-800 bg-[#0a0f1d] shadow-xl overflow-hidden">
      {/* Feed Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-b border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-cyan-400" />
          <span className="text-sm font-semibold text-white">Live Telemetry Terminal</span>
          <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
            {filteredEvents.length} events
          </span>
          {selectedSession && (
            <span className="text-xs px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 flex items-center gap-1">
              Filter: {selectedSession}
              <button
                onClick={() => onSelectSession("")}
                className="ml-1 hover:text-white"
              >
                ✕
              </button>
            </span>
          )}
        </div>

        {/* Filter Pills & Actions */}
        <div className="flex items-center flex-wrap gap-2">
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setFilterCat(cat)}
                className={`px-2 py-0.5 text-xs rounded-md transition-all font-mono uppercase ${
                  filterCat === cat
                    ? "bg-cyan-600 text-white font-bold"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`p-1.5 rounded-lg border transition-all ${
              isPaused
                ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                : "bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700"
            }`}
            title={isPaused ? "Resume stream autoscroll" : "Pause stream autoscroll"}
          >
            {isPaused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
          </button>

          <button
            onClick={onClear}
            className="p-1.5 rounded-lg bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700 hover:text-rose-400 transition-all"
            title="Clear terminal buffer"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Terminal Output Area */}
      <div className="flex-1 p-4 overflow-y-auto font-mono text-xs space-y-2 bg-[#080d1a]">
        {filteredEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-2">
            <Terminal className="h-8 w-8 text-slate-600 animate-pulse" />
            <span>Awaiting attacker terminal input on port 2222...</span>
            <span className="text-[11px] text-slate-600">
              (Use the Attack Simulator above or run 'ssh root@localhost -p 2222')
            </span>
          </div>
        ) : (
          filteredEvents.map((evt, idx) => (
            <div
              key={idx}
              onClick={() => onSelectSession(evt.session_id)}
              className="group p-2.5 rounded-lg bg-slate-900/50 hover:bg-slate-900 border border-slate-800/80 hover:border-slate-700 transition-all cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-2"
            >
              {/* Left Command & Session Info */}
              <div className="flex items-start md:items-center gap-3 overflow-hidden">
                <span className="text-slate-500 select-none text-[11px] shrink-0">
                  {evt.timestamp?.split("T")[1]?.slice(0, 8) || "LIVE"}
                </span>

                <span className="px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-[10px] text-slate-400 font-mono shrink-0">
                  {evt.src_ip}
                </span>

                <div className="flex items-center gap-1.5 overflow-hidden">
                  <span className="text-cyan-400 font-bold select-none">$</span>
                  <span className="text-slate-100 font-medium truncate group-hover:text-cyan-300 transition-colors">
                    {evt.command}
                  </span>
                </div>
              </div>

              {/* Right Tag Badges */}
              <div className="flex items-center flex-wrap gap-1.5 shrink-0">
                {/* Category Badge */}
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getCategoryBadge(
                    evt.category
                  )}`}
                >
                  {evt.category.toUpperCase()}
                </span>

                {/* MITRE Technique */}
                {evt.mitre_tag && (
                  <span className="px-1.5 py-0.5 rounded bg-slate-950 text-slate-300 border border-slate-800 text-[10px]" title={evt.mitre_name}>
                    {evt.mitre_tag}
                  </span>
                )}

                {/* Risk Score */}
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${getRiskColor(
                    evt.event_risk_score
                  )}`}
                >
                  +{evt.event_risk_score || 10}
                </span>
              </div>
            </div>
          ))
        )}
        <div ref={feedEndRef} />
      </div>
    </div>
  );
}
