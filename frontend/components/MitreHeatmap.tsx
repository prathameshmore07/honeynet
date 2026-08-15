"use client";

import React from "react";
import { ShieldCheck, Crosshair, AlertCircle } from "lucide-react";

export interface MitreStat {
  mitre_tag: string;
  mitre_name: string;
  count: number;
  last_seen?: string;
  sample_command?: string;
}

interface MitreHeatmapProps {
  stats: MitreStat[];
}

const TACTICS_MATRIX = [
  {
    tactic: "Initial Access",
    techniques: [
      { id: "T1078", name: "Valid Accounts" },
      { id: "T1190", name: "Exploit Public-Facing App" },
    ],
  },
  {
    tactic: "Execution",
    techniques: [
      { id: "T1059.004", name: "Unix Shell" },
      { id: "T1053", name: "Scheduled Task/Job" },
    ],
  },
  {
    tactic: "Discovery",
    techniques: [
      { id: "T1082", name: "System Info Discovery" },
      { id: "T1083", name: "File & Directory Discovery" },
      { id: "T1087", name: "Account Discovery" },
      { id: "T1018", name: "Remote System Discovery" },
    ],
  },
  {
    tactic: "Credential Access",
    techniques: [
      { id: "T1552.001", name: "Credentials In Files (.env)" },
      { id: "T1552.004", name: "Private Keys" },
    ],
  },
  {
    tactic: "Lateral Movement",
    techniques: [
      { id: "T1021.004", name: "SSH Lateral Movement" },
      { id: "T1530", name: "Cloud Storage (S3)" },
    ],
  },
  {
    tactic: "Collection & Exfil",
    techniques: [
      { id: "T1005", name: "Data from Local System" },
      { id: "T1560", name: "Archive Collected Data" },
      { id: "T1041", name: "Exfiltration Over C2" },
    ],
  },
];

export function MitreHeatmap({ stats }: MitreHeatmapProps) {
  const statMap = new Map<string, MitreStat>();
  stats.forEach((s) => statMap.set(s.mitre_tag, s));

  const getHeatmapColor = (count: number) => {
    if (count === 0) return "bg-slate-900/40 border-slate-800/80 text-slate-500 opacity-60";
    if (count >= 5) return "bg-rose-950/80 border-rose-600/80 text-rose-300 shadow-[0_0_12px_rgba(244,63,94,0.3)]";
    if (count >= 2) return "bg-amber-950/80 border-amber-600/80 text-amber-300 shadow-[0_0_10px_rgba(245,158,11,0.25)]";
    return "bg-cyan-950/80 border-cyan-600/80 text-cyan-300";
  };

  return (
    <div className="flex flex-col rounded-xl border border-slate-800 bg-[#0a0f1d] shadow-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-2">
          <Crosshair className="h-4 w-4 text-rose-400" />
          <span className="text-sm font-semibold text-white">MITRE ATT&CK Matrix & Technique Heatmap</span>
        </div>
        <span className="text-xs font-mono text-slate-400">
          {stats.length} Active Technique(s) Triggered
        </span>
      </div>

      {/* Grid of Tactics */}
      <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 bg-[#080d1a]">
        {TACTICS_MATRIX.map((tact, idx) => (
          <div key={idx} className="flex flex-col gap-2">
            <div className="text-[11px] font-bold tracking-wider uppercase text-slate-400 border-b border-slate-800 pb-1">
              {tact.tactic}
            </div>

            <div className="flex flex-col gap-1.5">
              {tact.techniques.map((tech) => {
                const stat = statMap.get(tech.id);
                const count = stat ? stat.count : 0;
                return (
                  <div
                    key={tech.id}
                    className={`group p-2.5 rounded-lg border text-xs transition-all ${getHeatmapColor(count)}`}
                    title={stat?.sample_command ? `Sample command: ${stat.sample_command}` : tech.name}
                  >
                    <div className="flex items-center justify-between font-mono text-[10px]">
                      <span className="font-bold">{tech.id}</span>
                      {count > 0 && (
                        <span className="px-1.5 py-0.2 rounded-full bg-slate-950/80 font-bold">
                          {count}x
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] font-medium mt-1 leading-tight line-clamp-2">
                      {tech.name}
                    </div>
                    {stat?.sample_command && (
                      <div className="mt-1 pt-1 border-t border-slate-800/80 text-[10px] font-mono text-slate-400 truncate">
                        $ {stat.sample_command}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
