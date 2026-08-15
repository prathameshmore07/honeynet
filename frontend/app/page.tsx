"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { Header } from "@/components/Header";
import { MetricsOverview } from "@/components/MetricsOverview";
import { LiveCommandFeed, CommandEventItem } from "@/components/LiveCommandFeed";
import { AttackPathGraph } from "@/components/AttackPathGraph";
import { MitreHeatmap, MitreStat } from "@/components/MitreHeatmap";
import { AttackerProfileCard, SessionData } from "@/components/AttackerProfileCard";
import { AssetInventory, DeceptionAsset } from "@/components/AssetInventory";
import { SimulatorModal } from "@/components/SimulatorModal";
import { Node, Edge } from "@xyflow/react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export default function SOCDashboard() {
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [isSimulatorOpen, setIsSimulatorOpen] = useState<boolean>(false);

  // Data States
  const [events, setEvents] = useState<CommandEventItem[]>([]);
  const [sessions, setSessions] = useState<SessionData[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [assets, setAssets] = useState<DeceptionAsset[]>([]);
  const [mitreStats, setMitreStats] = useState<MitreStat[]>([]);
  const [overviewMetrics, setOverviewMetrics] = useState({
    total_sessions: 0,
    active_attackers: 0,
    total_commands: 0,
    assets_deployed: 0,
    avg_risk_score: 0,
    highest_risk_score: 0,
    top_intent: "None",
    ollama_status: "Checking...",
    cowrie_status: "Active",
  });

  const [graphData, setGraphData] = useState<{ nodes: Node[]; edges: Edge[] }>({
    nodes: [],
    edges: [],
  });

  const wsRef = useRef<WebSocket | null>(null);

  // 1. Initial REST API Data Load
  const fetchAllData = useCallback(async () => {
    try {
      const [overviewRes, eventsRes, sessionsRes, assetsRes, mitreRes] = await Promise.allSettled([
        fetch(`${API_BASE}/api/overview`).then((r) => r.json()),
        fetch(`${API_BASE}/api/events?limit=150`).then((r) => r.json()),
        fetch(`${API_BASE}/api/sessions`).then((r) => r.json()),
        fetch(`${API_BASE}/api/assets`).then((r) => r.json()),
        fetch(`${API_BASE}/api/mitre-matrix`).then((r) => r.json()),
      ]);

      if (overviewRes.status === "fulfilled") setOverviewMetrics(overviewRes.value);
      if (eventsRes.status === "fulfilled") setEvents(eventsRes.value);
      if (sessionsRes.status === "fulfilled") {
        setSessions(sessionsRes.value);
        if (sessionsRes.value.length > 0 && !selectedSessionId) {
          setSelectedSessionId(sessionsRes.value[0].session_id);
        }
      }
      if (assetsRes.status === "fulfilled") setAssets(assetsRes.value);
      if (mitreRes.status === "fulfilled") setMitreStats(mitreRes.value);
    } catch (err) {
      console.warn("REST API polling notice:", err);
    }
  }, [selectedSessionId]);

  // 2. Fetch Attack Path Graph for Selected Session
  const fetchAttackPath = useCallback(async (sessionId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/attack-path/${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        setGraphData(data);
      }
    } catch (err) {
      console.warn("Attack path fetch notice:", err);
    }
  }, []);

  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  useEffect(() => {
    if (selectedSessionId) {
      fetchAttackPath(selectedSessionId);
    }
  }, [selectedSessionId, fetchAttackPath]);

  // 3. WebSocket Real-Time Telemetry Stream
  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout;

    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(`${WS_BASE}/ws/live`);
        wsRef.current = ws;

        ws.onopen = () => {
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === "command_event") {
              const newEvt: CommandEventItem = msg.data;
              setEvents((prev) => [newEvt, ...prev.slice(0, 199)]);

              // Update overview stats
              setOverviewMetrics((prev) => ({
                ...prev,
                total_commands: prev.total_commands + 1,
                highest_risk_score: Math.max(prev.highest_risk_score, newEvt.session_risk_score || 0),
              }));

              // Refresh active session and attack path
              fetchAllData();
            } else if (msg.type === "asset_created") {
              fetchAllData();
            }
          } catch (e) {
            console.error("WS parse error:", e);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimeout = setTimeout(connectWebSocket, 2500);
        };

        ws.onerror = () => {
          setWsConnected(false);
        };
      } catch (e) {
        reconnectTimeout = setTimeout(connectWebSocket, 2500);
      }
    };

    connectWebSocket();

    return () => {
      clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, [fetchAllData]);

  // 4. Trigger Attack Simulator from Dashboard
  const handleTriggerSimulation = async (scenario: string, delay: number) => {
    const res = await fetch(`${API_BASE}/api/simulator/trigger`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario, delay }),
    });
    if (!res.ok) {
      throw new Error(`Simulation failed: ${res.statusText}`);
    }
  };

  const selectedSessionData =
    sessions.find((s) => s.session_id === selectedSessionId) || (sessions[0] ?? null);

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black">
      {/* Top Navbar */}
      <Header
        wsConnected={wsConnected}
        ollamaStatus={overviewMetrics.ollama_status}
        cowrieStatus={overviewMetrics.cowrie_status}
        onOpenSimulator={() => setIsSimulatorOpen(true)}
      />

      {/* Main SOC Dashboard Grid */}
      <main className="flex-1 max-w-[1720px] w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* KPI Metrics Strip */}
        <MetricsOverview
          totalSessions={overviewMetrics.total_sessions}
          activeAttackers={overviewMetrics.active_attackers}
          totalCommands={overviewMetrics.total_commands}
          assetsDeployed={overviewMetrics.assets_deployed}
          avgRiskScore={overviewMetrics.avg_risk_score}
          highestRiskScore={overviewMetrics.highest_risk_score}
          topIntent={overviewMetrics.top_intent}
        />

        {/* Core Live Terminal & Attacker Profiling Intelligence */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-7 xl:col-span-8">
            <LiveCommandFeed
              events={events}
              onClear={() => setEvents([])}
              selectedSession={selectedSessionId}
              onSelectSession={(sId) => setSelectedSessionId(sId || null)}
            />
          </div>

          <div className="lg:col-span-5 xl:col-span-4">
            <AttackerProfileCard
              session={selectedSessionData}
              onSelectSession={(sId) => setSelectedSessionId(sId)}
              allSessions={sessions}
            />
          </div>
        </div>

        {/* Interactive React Flow Lateral Movement Graph */}
        <div className="w-full">
          <AttackPathGraph
            graphData={graphData}
            selectedSession={selectedSessionId}
          />
        </div>

        {/* MITRE ATT&CK Matrix & Deception Asset Inventory */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          <div className="xl:col-span-6">
            <MitreHeatmap stats={mitreStats} />
          </div>

          <div className="xl:col-span-6">
            <AssetInventory assets={assets} />
          </div>
        </div>
      </main>

      {/* Attack Simulator Modal */}
      <SimulatorModal
        isOpen={isSimulatorOpen}
        onClose={() => setIsSimulatorOpen(false)}
        onTrigger={handleTriggerSimulation}
      />
    </div>
  );
}
