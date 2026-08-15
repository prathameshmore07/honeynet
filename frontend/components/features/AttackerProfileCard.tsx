"use client";

import React from "react";
import { Brain, Target, Compass, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { SessionSummary } from "@/lib/schemas";

interface AttackerProfileCardProps {
  session: SessionSummary | null;
  onSelectSession: (sessionId: string) => void;
  allSessions: SessionSummary[];
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
      <div className="flex flex-col items-center justify-center p-6 rounded-lg border border-[#222730] bg-[#14171C] text-[#8B92A0] h-full min-h-[320px] font-mono text-xs">
        <Brain className="h-6 w-6 text-[#8B92A0]/60 mb-2 animate-pulse" />
        <span>No adversary profile selected.</span>
      </div>
    );
  }

  const riskScore = session.risk_score || 20;

  const getRiskColor = (score: number) => {
    if (score >= 70) return "text-[#E85D4E]";
    if (score >= 40) return "text-[#D4A94E]";
    return "text-[#4A9EFF]";
  };

  const getSkillVariant = (skill?: string): "risk" | "mitre" | "info" => {
    if (skill?.includes("APT") || skill?.includes("Sophisticated")) return "risk";
    if (skill?.includes("Opportunistic")) return "mitre";
    return "info";
  };

  return (
    <div className="flex flex-col rounded-lg border border-[#222730] bg-[#14171C] shadow-lg overflow-hidden h-full">
      {/* Dossier Header */}
      <div className="px-4 py-2.5 border-b border-[#222730] bg-[#101318] flex items-center justify-between font-mono">
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-[#4A9EFF]" />
          <span className="text-xs font-bold uppercase tracking-wider text-[#E8EAED]">
            Attacker Attribution & Forensic Dossier
          </span>
        </div>

        {allSessions.length > 1 && (
          <select
            value={session.session_id}
            onChange={(e) => onSelectSession(e.target.value)}
            className="bg-[#0B0D10] border border-[#222730] text-[#E8EAED] text-[11px] rounded px-2 py-0.5 font-mono focus:outline-none focus:border-[#4A9EFF]"
          >
            {allSessions.map((s) => (
              <option key={s.session_id} value={s.session_id}>
                {s.session_id} ({s.src_ip})
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="p-4 space-y-3.5 text-xs bg-[#14171C] flex-1 flex flex-col justify-between">
        <div className="space-y-3 font-mono">
          {/* Identity Strip */}
          <div className="flex items-center justify-between pb-2 border-b border-[#222730]">
            <div>
              <span className="text-[#8B92A0] text-[10px] uppercase">Session ID:</span>
              <div className="text-sm font-bold text-[#E8EAED]">
                {session.session_id}{" "}
                <span className="text-[11px] font-normal text-[#8B92A0]">[{session.src_ip}]</span>
              </div>
            </div>

            <div className="text-right">
              <span className="text-[#8B92A0] text-[10px] uppercase">Attribution Tier:</span>
              <div>
                <Badge variant={getSkillVariant(session.skill_level)}>
                  {session.skill_level || "Opportunistic"}
                </Badge>
              </div>
            </div>
          </div>

          {/* Inferred Goal */}
          <div className="p-3 rounded border border-[#222730] bg-[#101318]">
            <div className="flex items-center gap-1.5 text-[#4A9EFF] font-bold text-[11px] mb-1">
              <Target className="h-3.5 w-3.5" />
              <span>Inferred Adversary Objective</span>
            </div>
            <p className="text-[#E8EAED] font-sans text-xs leading-relaxed">
              {session.goal_summary || "Initial reconnaissance and environment discovery on Bastion."}
            </p>
          </div>

          {/* AI Narrative */}
          <div className="p-3 rounded border border-[#222730] bg-[#101318]">
            <div className="flex items-center gap-1.5 text-[#D4A94E] font-bold text-[11px] mb-1">
              <Compass className="h-3.5 w-3.5" />
              <span>AI Forensic Threat Briefing</span>
            </div>
            <p className="text-[#8B92A0] font-sans text-xs leading-relaxed">
              {session.ai_summary || "Adversary executing commands. Autonomous deception canary assets were injected to monitor lateral progression."}
            </p>
          </div>
        </div>

        {/* Risk Score Meter */}
        <div className="pt-3 border-t border-[#222730] font-mono space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-[#8B92A0] flex items-center gap-1.5">
              <ShieldAlert className="h-3.5 w-3.5 text-[#E85D4E]" />
              Threat Severity Index:
            </span>
            <span className={`font-bold tabular-nums ${getRiskColor(riskScore)}`}>
              {riskScore} / 100
            </span>
          </div>

          <div className="h-1.5 w-full bg-[#0B0D10] rounded-full overflow-hidden border border-[#222730]">
            <div
              className="h-full bg-[#4A9EFF] transition-all duration-300"
              style={{
                width: `${Math.min(100, Math.max(10, riskScore))}%`,
                backgroundColor: riskScore >= 70 ? "#E85D4E" : riskScore >= 40 ? "#D4A94E" : "#4A9EFF",
              }}
            />
          </div>

          <div className="flex justify-between text-[9px] text-[#8B92A0] font-mono">
            <span>Low (0)</span>
            <span>Elevated (45)</span>
            <span>Critical (100)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
