"use client";

import React, { useState, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  Position,
  NodeProps,
  Edge,
  Node,
} from "@xyflow/react";
import {
  Server,
  GitBranch,
  Cloud,
  Database,
  Users,
  DollarSign,
  Laptop,
  Cpu,
  ShieldAlert,
  Info,
  Layers,
  X,
} from "lucide-react";

// Icon mapping for custom nodes
const ICON_MAP: Record<string, React.ElementType> = {
  server: Server,
  "git-branch": GitBranch,
  cloud: Cloud,
  database: Database,
  users: Users,
  "dollar-sign": DollarSign,
  laptop: Laptop,
  cpu: Cpu,
};

// Custom Node Component for React Flow
function SOCNode({ data }: NodeProps) {
  const Icon = ICON_MAP[data.icon as string] || Server;
  const status = (data.status as string) || "dormant";

  const getStatusStyles = () => {
    switch (status) {
      case "compromised":
        return "border-rose-500 bg-rose-950/80 text-rose-300 shadow-[0_0_16px_rgba(244,63,94,0.35)]";
      case "targeted":
        return "border-amber-500 bg-amber-950/80 text-amber-300 shadow-[0_0_14px_rgba(245,158,11,0.3)] animate-pulse";
      case "discovered":
        return "border-cyan-500 bg-cyan-950/80 text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.2)]";
      default:
        return "border-slate-800 bg-slate-900/60 text-slate-400 opacity-60";
    }
  };

  const getBadgeColor = () => {
    switch (status) {
      case "compromised":
        return "bg-rose-900 text-rose-200 border-rose-700";
      case "targeted":
        return "bg-amber-900 text-amber-200 border-amber-700";
      case "discovered":
        return "bg-cyan-900 text-cyan-200 border-cyan-700";
      default:
        return "bg-slate-800 text-slate-400 border-slate-700";
    }
  };

  return (
    <div
      className={`relative px-4 py-3 rounded-xl border-2 transition-all duration-300 min-w-[200px] cursor-pointer ${getStatusStyles()}`}
    >
      <Handle type="target" position={Position.Left} className="w-2.5 h-2.5 bg-cyan-400 border-slate-900" />
      
      <div className="flex items-center justify-between gap-3">
        <div className="p-2 rounded-lg bg-slate-950/80 border border-slate-800/80">
          <Icon className="h-4 w-4" />
        </div>
        <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${getBadgeColor()}`}>
          {status}
        </span>
      </div>

      <div className="mt-2.5">
        <div className="text-xs font-bold text-white tracking-wide">{data.label as string}</div>
        <div className="text-[11px] font-mono text-slate-400 truncate">{data.ip as string}</div>
        <div className="text-[10px] text-slate-400 mt-1 truncate">{data.service as string}</div>
      </div>

      <Handle type="source" position={Position.Right} className="w-2.5 h-2.5 bg-cyan-400 border-slate-900" />
    </div>
  );
}

interface AttackPathGraphProps {
  graphData: {
    nodes: Node[];
    edges: Edge[];
  };
  selectedSession: string | null;
}

export function AttackPathGraph({ graphData, selectedSession }: AttackPathGraphProps) {
  const [activeNode, setActiveNode] = useState<any | null>(null);

  const nodeTypes = useMemo(() => ({ custom: SOCNode }), []);

  const onNodeClick = (_: any, node: Node) => {
    setActiveNode(node.data);
  };

  return (
    <div className="relative flex flex-col h-[520px] rounded-xl border border-slate-800 bg-[#070b14] shadow-xl overflow-hidden">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/60 z-10">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-cyan-400" />
          <span className="text-sm font-semibold text-white">Dynamic Attack Path & Lateral Movement Graph</span>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="flex items-center gap-1.5 text-rose-400">
            <span className="h-2 w-2 rounded-full bg-rose-500" /> Compromised
          </span>
          <span className="flex items-center gap-1.5 text-amber-400">
            <span className="h-2 w-2 rounded-full bg-amber-500" /> Targeted
          </span>
          <span className="flex items-center gap-1.5 text-cyan-400">
            <span className="h-2 w-2 rounded-full bg-cyan-500" /> Discovered
          </span>
          <span className="flex items-center gap-1.5 text-slate-500">
            <span className="h-2 w-2 rounded-full bg-slate-600" /> Dormant
          </span>
        </div>
      </div>

      {/* React Flow Canvas */}
      <div className="flex-1 w-full h-full">
        <ReactFlow
          nodes={graphData.nodes}
          edges={graphData.edges}
          nodeTypes={nodeTypes}
          onNodeClick={onNodeClick}
          fitView
          attributionPosition="bottom-left"
          minZoom={0.5}
          maxZoom={1.5}
        >
          <Background color="#1e293b" gap={20} size={1} />
          <Controls />
        </ReactFlow>
      </div>

      {/* Interactive Node Detail Drawer */}
      {activeNode && (
        <div className="absolute right-4 top-16 w-80 p-4 rounded-xl border border-slate-700 bg-slate-900/95 shadow-2xl backdrop-blur-md z-20 transition-all animate-in fade-in slide-in-from-right-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <Info className="h-4 w-4 text-cyan-400" />
              <span className="text-xs font-bold text-white">{activeNode.label}</span>
            </div>
            <button
              onClick={() => setActiveNode(null)}
              className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="mt-3 space-y-2 text-xs">
            <div>
              <span className="text-slate-400">Endpoint / IP:</span>
              <p className="font-mono text-cyan-300 font-semibold">{activeNode.ip}</p>
            </div>
            <div>
              <span className="text-slate-400">Emulated Service:</span>
              <p className="text-slate-200">{activeNode.service}</p>
            </div>
            <div>
              <span className="text-slate-400">Security Infiltration State:</span>
              <p className="font-semibold uppercase tracking-wider text-xs mt-0.5 text-amber-400">
                {activeNode.status}
              </p>
            </div>
            <div className="pt-2 border-t border-slate-800">
              <span className="text-slate-400">Adaptive Honeypot Decoys:</span>
              <div className="mt-1 p-2 rounded bg-slate-950 border border-slate-800 font-mono text-[11px] text-emerald-400">
                ✓ Synthetic Honeynet Canary Active
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
