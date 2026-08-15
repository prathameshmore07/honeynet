"use client";

import React from "react";
import { UserCheck, ShieldAlert, Target, Brain, Compass, Award } from "lucide-react";

export interface SessionData {
  session_id: string;
  src_ip: string;
  start_time: string;
  last_active: string;
  total_commands: number;
  categories_triggered: string[];
  risk_score: number;
  inferred_intent?: string;
  skill_level?: string;
  goal_summary?: string;
  ai_summary?: string;
  pivot_depth?: number;
}

interface AttackerProfileCardProps {
  session: SessionData | null;
  onSelectSession: (sessionId: string) => void;
  allSessions: SessionData[];
}

export function AttackerProfileCard({
  session,
  onSelectSession,
  allSessions,
}: AttackerProfileCardProps) {
  if (!session && allSessions.length > 0) {
    session = allSessions[0];
  }

  if (!session) {
    return (
      <div className="flex flex-col items-center justify-center p-8 rounded-xl border border-slate-800 bg-[#0a0f1d] text-slate-500 h-full">
        <Brain className="h-8 w-8 text-slate-600 animate-pulse mb-2" />
        <span className="text-xs">No active attacker session selected.</span>
      </div>
    );
  }

  const riskScore = session.risk_score || 20;

  const getRiskGradient = (score: number) => {
    if (score >= 75) return "from-rose-500 to-red-600 text-rose-400";
    if (score >= 45) return "from-amber-500 to-orange-600 text-amber-400";
    return "from-cyan-500 to-teal-600 text-cyan-400";
  };

  const getSkillBadgeColor = (skill?: string) => {
    if (skill?.includes("APT") || skill?.includes("Sophisticated")) {
      return "bg-rose-950 text-rose-300 border-rose-800";
    }
    if (skill?.includes("Opportunistic")) {
      return "bg-amber-950 text-amber-300 border-amber-800";
    }
    return "bg-cyan-950 text-cyan-300 border-cyan-800";
  };

  return (
    <div className="flex flex-col rounded-xl border border-slate-800 bg-[#0a0f1d] shadow-xl overflow-hidden h-full">
      {/* Card Header with Session Selector */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-purple-400" />
          <span className="text-sm font-semibold text-white">Attacker Profile & Threat Intel</span>
        </div>

        {allSessions.length > 1 && (
          <select
            value={session.session_id}
            onChange={(e) => onSelectSession(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-slate-300 text-xs rounded-lg px-2 py-1 font-mono focus:outline-none focus:border-cyan-500"
          >
            {allSessions.map((s) => (
              <option key={s.session_id} value={s.session_id}>
                {s.session_id} ({s.src_ip})
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="p-4 space-y-4 text-xs bg-[#080d1a] flex-1 flex flex-col justify-between">
        {/* Top Info Badges */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-slate-400 text-[11px]">Threat Actor Identifier:</span>
              <div className="font-mono text-sm font-bold text-white flex items-center gap-2">
                {session.session_id}
                <span className="text-xs text-slate-400 font-normal">({session.src_ip})</span>
              </div>
            </div>

            <div className="text-right">
              <span className="text-slate-400 text-[11px]">Sophistication Tier:</span>
              <div>
                <span className={`inline-block px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${getSkillBadgeColor(session.skill_level)}`}>
                  {session.skill_level || "Opportunistic"}
                </span>
              </div>
            </div>
          </div>

          {/* Inferred Goal */}
          <div className="p-3 rounded-lg bg-slate-900/70 border border-slate-800">
            <div className="flex items-center gap-1.5 text-slate-400 font-semibold mb-1">
              <Target className="h-3.5 w-3.5 text-cyan-400" />
              <span>Inferred Campaign Objective</span>
            </div>
            <div className="text-slate-200 font-medium text-[11px] leading-relaxed">
              {session.goal_summary || "Initial reconnaissance and environment discovery on Bastion."}
            </div>
          </div>

          {/* AI Threat Summary */}
          <div className="p-3 rounded-lg bg-purple-950/20 border border-purple-900/40">
            <div className="flex items-center gap-1.5 text-purple-300 font-semibold mb-1">
              <Compass className="h-3.5 w-3.5 text-purple-400" />
              <span>AI SOC Narrative Assessment</span>
            </div>
            <div className="text-slate-300 text-[11px] leading-relaxed">
              {session.ai_summary || "Attacker actively executing commands. Autonomous deception canary assets were injected into file paths to entrap and profile TTPs."}
            </div>
          </div>
        </div>

        {/* Risk Score Progress Gauge */}
        <div className="pt-3 border-t border-slate-800 space-y-1.5">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-slate-400 flex items-center gap-1">
              <ShieldAlert className="h-3.5 w-3.5 text-rose-400" /> Composite Risk Index
            </span>
            <span className="font-bold text-white">{riskScore} / 100</span>
          </div>
          <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
            <div
              className={`h-full bg-gradient-to-r ${getRiskGradient(riskScore)} transition-all duration-500`}
              style={{ width: `${Math.min(100, Math.max(10, riskScore))}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-slate-500 font-mono pt-0.5">
            <span>Low (0)</span>
            <span>Elevated (45)</span>
            <span>Critical / Breach Imminent (100)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
