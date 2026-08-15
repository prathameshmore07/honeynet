"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/features/Header";
import { MetricsOverview } from "@/components/features/MetricsOverview";
import { AttackPathGraph } from "@/components/features/AttackPathGraph";
import { AttackerProfileCard } from "@/components/features/AttackerProfileCard";
import { LiveCommandFeed } from "@/components/features/LiveCommandFeed";
import { MitreHeatmap } from "@/components/features/MitreHeatmap";
import { AssetInventory } from "@/components/features/AssetInventory";
import { SimulatorModal } from "@/components/features/SimulatorModal";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { api } from "@/lib/api";
import { useWebSocket } from "@/lib/useWebSocket";
import { CommandEvent } from "@/lib/schemas";

export default function SOCForensicsDashboard() {
  const queryClient = useQueryClient();
  const [isSimulatorOpen, setIsSimulatorOpen] = useState<boolean>(false);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [feedSessionFilter, setFeedSessionFilter] = useState<string | null>(null);
  const [localEvents, setLocalEvents] = useState<CommandEvent[]>([]);

  // 1. TanStack Query Hooks for Telemetry Data
  const { data: overview = {
    total_sessions: 0,
    active_attackers: 0,
    total_commands: 0,
    assets_deployed: 0,
    avg_risk_score: 0,
    highest_risk_score: 0,
    top_intent: "None",
    ollama_status: "Active",
    cowrie_status: "Active",
  } } = useQuery({
    queryKey: ["overview"],
    queryFn: api.getOverview,
    refetchInterval: 4000,
  });

  const { data: sessions = [] } = useQuery({
    queryKey: ["sessions"],
    queryFn: api.getSessions,
    refetchInterval: 4000,
  });

  const { data: initialEvents = [] } = useQuery({
    queryKey: ["events"],
    queryFn: () => api.getEvents(120),
  });

  const { data: assets = [] } = useQuery({
    queryKey: ["assets"],
    queryFn: api.getAssets,
    refetchInterval: 4000,
  });

  const { data: mitreStats = [] } = useQuery({
    queryKey: ["mitre"],
    queryFn: api.getMitreMatrix,
    refetchInterval: 4000,
  });

  // Default selected session
  useEffect(() => {
    if (sessions.length > 0 && !selectedSessionId) {
      setSelectedSessionId(sessions[0].session_id);
    }
  }, [sessions, selectedSessionId]);

  // Sync initial events into buffer (chronological order for terminal)
  useEffect(() => {
    if (initialEvents.length > 0 && localEvents.length === 0) {
      setLocalEvents([...initialEvents].reverse());
    }
  }, [initialEvents, localEvents.length]);

  // Active Session Attack Path
  const activeSessionKey = selectedSessionId || (sessions[0]?.session_id ?? "");
  const { data: graphData = { nodes: [], edges: [] } } = useQuery({
    queryKey: ["attackPath", activeSessionKey],
    queryFn: () => api.getAttackPath(activeSessionKey),
    enabled: true,
    refetchInterval: 4000,
  });

  // 2. Real-time WebSocket Ingestion (Append to bottom of terminal)
  const handleCommandEvent = useCallback((event: CommandEvent) => {
    setLocalEvents((prev) => [...prev.slice(-199), event]);
  }, []);

  const handleRefresh = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["overview"] });
    queryClient.invalidateQueries({ queryKey: ["sessions"] });
    queryClient.invalidateQueries({ queryKey: ["assets"] });
    queryClient.invalidateQueries({ queryKey: ["mitre"] });
    if (activeSessionKey) {
      queryClient.invalidateQueries({ queryKey: ["attackPath", activeSessionKey] });
    }
  }, [queryClient, activeSessionKey]);

  const { isConnected: wsConnected, latencyMs } = useWebSocket({
    onCommandEvent: handleCommandEvent,
    onRefreshNeeded: handleRefresh,
  });

  // 3. Trigger Simulator
  const handleTriggerSimulation = async (scenario: string, delay: number) => {
    await api.triggerSimulation(scenario, delay);
  };

  const selectedSessionData =
    sessions.find((s) => s.session_id === selectedSessionId) || (sessions[0] ?? null);

  return (
    <div className="min-h-screen bg-[#0B0D10] text-[#E8EAED] flex flex-col font-sans selection:bg-[#4A9EFF] selection:text-black">
      {/* Forensics Lab Status Header */}
      <Header
        wsConnected={wsConnected}
        latencyMs={latencyMs}
        ollamaStatus={overview.ollama_status}
        cowrieStatus={overview.cowrie_status}
        onOpenSimulator={() => setIsSimulatorOpen(true)}
      />

      {/* Main Forensics Workspace */}
      <main className="flex-1 max-w-[1780px] w-full mx-auto p-4 sm:p-5 space-y-4">
        {/* KPI Telemetry Strip */}
        <ErrorBoundary panelName="Metrics Overview">
          <MetricsOverview metrics={overview} />
        </ErrorBoundary>

        {/* HERO SECTION: Asymmetric Viewport (React Flow 60% Width + Dossier 40%) */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
          <div className="xl:col-span-7">
            <ErrorBoundary panelName="Lateral Movement Graph">
              <AttackPathGraph
                graphData={graphData}
                selectedSession={selectedSessionId}
              />
            </ErrorBoundary>
          </div>

          <div className="xl:col-span-5">
            <ErrorBoundary panelName="Attacker Attribution Dossier">
              <AttackerProfileCard
                session={selectedSessionData}
                onSelectSession={(sId) => setSelectedSessionId(sId)}
                allSessions={sessions}
              />
            </ErrorBoundary>
          </div>
        </div>

        {/* SECONDARY ROW: Live Terminal & MITRE Matrix */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
          <div className="xl:col-span-7">
            <ErrorBoundary panelName="Live Command Terminal">
              <LiveCommandFeed
                events={localEvents}
                onClear={() => setLocalEvents([])}
                selectedSession={feedSessionFilter}
                onSelectSession={(sId) => setFeedSessionFilter(sId || null)}
              />
            </ErrorBoundary>
          </div>

          <div className="xl:col-span-5">
            <ErrorBoundary panelName="MITRE ATT&CK Matrix">
              <MitreHeatmap stats={mitreStats} />
            </ErrorBoundary>
          </div>
        </div>

        {/* TERTIARY ROW: Deception Evidence Vault */}
        <div className="w-full">
          <ErrorBoundary panelName="Deception Honeytoken Vault">
            <AssetInventory assets={assets} />
          </ErrorBoundary>
        </div>
      </main>

      {/* Campaign Simulator Dialog */}
      <SimulatorModal
        isOpen={isSimulatorOpen}
        onClose={() => setIsSimulatorOpen(false)}
        onTrigger={handleTriggerSimulation}
      />
    </div>
  );
}
