"use client";

import React from "react";
import { Users, Terminal, Layers, ShieldAlert } from "lucide-react";
import { StatItem } from "@/components/ui/StatItem";
import { OverviewMetrics } from "@/lib/schemas";

interface MetricsOverviewProps {
  metrics: OverviewMetrics;
}

export function MetricsOverview({ metrics }: MetricsOverviewProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
      <StatItem
        label="Adversary Sessions"
        value={metrics.total_sessions}
        subLabel={`${metrics.active_attackers} active IP address(es)`}
        icon={<Users className="h-4 w-4" />}
        variant="info"
      />
      <StatItem
        label="Ingested Commands"
        value={metrics.total_commands}
        subLabel="Streamed via Cowrie JSON bus"
        icon={<Terminal className="h-4 w-4" />}
        variant="default"
      />
      <StatItem
        label="Canary Assets Deployed"
        value={metrics.assets_deployed}
        subLabel={`Primary Target: ${metrics.top_intent}`}
        icon={<Layers className="h-4 w-4" />}
        variant="mitre"
      />
      <StatItem
        label="Forensic Threat Severity"
        value={`${metrics.avg_risk_score}/100`}
        subLabel={`Peak Incident Score: ${metrics.highest_risk_score}/100`}
        icon={<ShieldAlert className="h-4 w-4" />}
        variant={metrics.highest_risk_score >= 70 ? "risk" : "mitre"}
      />
    </div>
  );
}
