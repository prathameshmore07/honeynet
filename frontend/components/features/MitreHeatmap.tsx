"use client";

import React from "react";
import { Crosshair } from "lucide-react";
import { MitreStat } from "@/lib/schemas";

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
    ],
  },
  {
    tactic: "Credential Access",
    techniques: [
      { id: "T1552.001", name: "Credentials In Files (.env)" },
      { id: "T1552.004", name: "Private Keys (id_rsa)" },
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
    ],
  },
];

export function MitreHeatmap({ stats }: MitreHeatmapProps) {
  const statMap = new Map<string, MitreStat>();
  stats.forEach((s) => statMap.set(s.mitre_tag, s));

  const getHeatmapStyles = (count: number) => {
    if (count === 0) return "bg-[#101318]/50 border-[#222730] text-[#8B92A0] opacity-40";
    if (count >= 5) return "bg-[#E85D4E]/15 border-[#E85D4E]/50 text-[#E85D4E]";
    if (count >= 2) return "bg-[#D4A94E]/15 border-[#D4A94E]/50 text-[#D4A94E]";
    return "bg-[#4A9EFF]/15 border-[#4A9EFF]/50 text-[#4A9EFF]";
  };

  return (
    <div className="flex flex-col rounded-lg border border-[#222730] bg-[#14171C] shadow-lg overflow-hidden font-mono">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[#222730] bg-[#101318]">
        <div className="flex items-center gap-2">
          <Crosshair className="h-4 w-4 text-[#D4A94E]" />
          <span className="text-xs font-bold uppercase tracking-wider text-[#E8EAED]">
            MITRE ATT&CK Enterprise Matrix Heatmap
          </span>
        </div>
        <span className="text-[11px] text-[#8B92A0] tabular-nums">
          {stats.length} technique(s) active
        </span>
      </div>

      {/* Grid */}
      <div className="p-3.5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-2.5 bg-[#0E1116]">
        {TACTICS_MATRIX.map((tact, idx) => (
          <div key={idx} className="flex flex-col gap-1.5">
            <div className="text-[10px] font-bold uppercase tracking-wider text-[#8B92A0] border-b border-[#222730] pb-1">
              {tact.tactic}
            </div>

            <div className="flex flex-col gap-1.5">
              {tact.techniques.map((tech) => {
                const stat = statMap.get(tech.id);
                const count = stat ? stat.count : 0;
                return (
                  <div
                    key={tech.id}
                    className={`p-2 rounded border text-xs transition-all ${getHeatmapStyles(count)}`}
                    title={stat?.sample_command ? `Command: ${stat.sample_command}` : tech.name}
                  >
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="font-bold">{tech.id}</span>
                      {count > 0 && (
                        <span className="px-1 py-0.2 rounded bg-[#0B0D10] font-bold tabular-nums">
                          {count}x
                        </span>
                      )}
                    </div>
                    <div className="text-[10px] font-sans font-medium mt-1 leading-snug line-clamp-2">
                      {tech.name}
                    </div>
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
