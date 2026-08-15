"use client";

import React, { useState, useEffect, useRef } from "react";
import { Terminal, Pause, Play, Trash2, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { CommandEvent } from "@/lib/schemas";

interface LiveCommandFeedProps {
  events: CommandEvent[];
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
  const [searchQuery, setSearchQuery] = useState<string>("" );
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

  const getCategoryVariant = (cat: string): "risk" | "mitre" | "info" | "neutral" => {
    switch (cat) {
      case "finance":
        return "risk";
      case "git":
        return "info";
      case "aws":
        return "mitre";
      case "hr":
        return "mitre";
      case "database":
        return "info";
      default:
        return "neutral";
    }
  };

  return (
    <div className="flex flex-col h-[520px] rounded-lg border border-[#222730] bg-[#0E1116] shadow-xl overflow-hidden font-mono">
      {/* Terminal Titlebar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 border-b border-[#222730] bg-[#101318]">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-[#4A9EFF]" />
          <span className="text-xs font-bold uppercase tracking-wider text-[#E8EAED]">
            Live Terminal Telemetry Bus
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#191D24] text-[#8B92A0] tabular-nums">
            {filteredEvents.length} events
          </span>
          {selectedSession && (
            <span className="text-[10px] px-2 py-0.5 rounded bg-[#4A9EFF]/10 text-[#4A9EFF] border border-[#4A9EFF]/30 flex items-center gap-1">
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
        <div className="flex items-center flex-wrap gap-2 text-xs">
          <div className="flex items-center gap-1 bg-[#0B0D10] p-0.5 rounded border border-[#222730]">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setFilterCat(cat)}
                className={`px-2 py-0.5 text-[10px] rounded uppercase transition-all ${
                  filterCat === cat
                    ? "bg-[#4A9EFF] text-black font-bold"
                    : "text-[#8B92A0] hover:text-[#E8EAED]"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`p-1.5 rounded border text-xs transition-all ${
              isPaused
                ? "bg-[#D4A94E]/20 text-[#D4A94E] border-[#D4A94E]/40"
                : "bg-[#14171C] text-[#8B92A0] border-[#222730] hover:text-[#E8EAED]"
            }`}
            title={isPaused ? "Resume autoscroll" : "Pause autoscroll"}
          >
            {isPaused ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
          </button>

          <button
            onClick={onClear}
            className="p-1.5 rounded bg-[#14171C] text-[#8B92A0] border border-[#222730] hover:text-[#E85D4E] transition-all"
            title="Clear buffer"
          >
            <Trash2 className="h-3 w-3" />
          </button>
        </div>
      </div>

      {/* Terminal Live Output */}
      <div
        aria-live="polite"
        className="flex-1 p-3.5 overflow-y-auto text-xs space-y-1.5 bg-[#0B0D10]"
      >
        {filteredEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-[#8B92A0] gap-2">
            <Terminal className="h-6 w-6 text-[#8B92A0]/50 animate-pulse" />
            <span className="text-xs">Awaiting attacker input on Cowrie port 2222...</span>
            <span className="text-[10px] text-[#8B92A0]/60">
              (Execute an attack scenario or connect with ssh root@localhost -p 2222)
            </span>
          </div>
        ) : (
          filteredEvents.map((evt, idx) => (
            <div
              key={idx}
              onClick={() => onSelectSession(evt.session_id)}
              className="group p-2 rounded bg-[#101318]/60 hover:bg-[#14171C] border border-[#222730]/60 hover:border-[#4A9EFF]/40 transition-all cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-2"
            >
              {/* Left Command & Session Info */}
              <div className="flex items-start md:items-center gap-2.5 overflow-hidden">
                <span className="text-[#8B92A0] text-[10px] tabular-nums shrink-0">
                  {evt.timestamp?.split("T")[1]?.slice(0, 8) || "LIVE"}
                </span>

                <span className="px-1.5 py-0.2 rounded bg-[#0B0D10] border border-[#222730] text-[9px] text-[#8B92A0] shrink-0">
                  {evt.src_ip}
                </span>

                <div className="flex items-center gap-1.5 overflow-hidden">
                  <span className="text-[#4A9EFF] font-bold select-none">$</span>
                  <span className="text-[#E8EAED] truncate group-hover:text-[#4A9EFF] transition-colors">
                    {evt.command}
                  </span>
                </div>
              </div>

              {/* Right Tag Badges */}
              <div className="flex items-center flex-wrap gap-1.5 shrink-0 text-[10px]">
                <Badge variant={getCategoryVariant(evt.category)}>
                  {evt.category.toUpperCase()}
                </Badge>

                {evt.mitre_tag && (
                  <Badge variant="mitre">{evt.mitre_tag}</Badge>
                )}

                <Badge variant="risk">+{evt.event_risk_score || 10}</Badge>
              </div>
            </div>
          ))
        )}

        {/* Blinking Cursor Prompt at bottom */}
        <div className="pt-2 flex items-center gap-2 text-[#8B92A0] text-[11px]">
          <span className="text-[#4A9EFF]">honeynet-forensics:~$</span>
          <span className="h-3.5 w-1.5 bg-[#4A9EFF] animate-cursor-blink inline-block" />
        </div>

        <div ref={feedEndRef} />
      </div>
    </div>
  );
}
