"use client";

import React from "react";
import { Users, Terminal, Layers, AlertTriangle, TrendingUp, ShieldAlert } from "lucide-react";

interface MetricsOverviewProps {
  totalSessions: number;
  activeAttackers: number;
  totalCommands: number;
  assetsDeployed: number;
  avgRiskScore: number;
  highestRiskScore: number;
  topIntent: string;
}

export function MetricsOverview({
  totalSessions,
  activeAttackers,
  totalCommands,
  assetsDeployed,
  avgRiskScore,
  highestRiskScore,
  topIntent,
}: MetricsOverviewProps) {
  const cards = [
    {
      title: "Attack Sessions",
      value: totalSessions,
      subValue: `${activeAttackers} Active IP(s)`,
      icon: Users,
      color: "text-cyan-400",
      borderColor: "border-cyan-500/20",
      bgGradient: "from-cyan-950/30 to-slate-900/60",
    },
    {
      title: "Ingested Commands",
      value: totalCommands,
      subValue: "Real-time Cowrie Stream",
      icon: Terminal,
      color: "text-emerald-400",
      borderColor: "border-emerald-500/20",
      bgGradient: "from-emerald-950/30 to-slate-900/60",
    },
    {
      title: "Deception Assets Deployed",
      value: assetsDeployed,
      subValue: `Top Vector: ${topIntent}`,
      icon: Layers,
      color: "text-amber-400",
      borderColor: "border-amber-500/20",
      bgGradient: "from-amber-950/30 to-slate-900/60",
    },
    {
      title: "Threat Severity Index",
      value: `${avgRiskScore}/100`,
      subValue: `Peak Risk: ${highestRiskScore}/100`,
      icon: ShieldAlert,
      color: highestRiskScore > 70 ? "text-rose-400" : "text-amber-400",
      borderColor: highestRiskScore > 70 ? "border-rose-500/20" : "border-amber-500/20",
      bgGradient: highestRiskScore > 70 ? "from-rose-950/30 to-slate-900/60" : "from-amber-950/30 to-slate-900/60",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`relative overflow-hidden rounded-xl border ${card.borderColor} bg-gradient-to-br ${card.bgGradient} p-4 shadow-md backdrop-blur-sm transition-all hover:border-slate-700`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                {card.title}
              </span>
              <div className={`p-2 rounded-lg bg-slate-900/80 border border-slate-800 ${card.color}`}>
                <Icon className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight text-white font-mono">
                {card.value}
              </span>
            </div>
            <div className="mt-1 flex items-center gap-1.5 text-xs text-slate-400">
              <span>{card.subValue}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
