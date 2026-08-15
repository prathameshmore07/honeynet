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
  Info,
  Layers,
  X,
  ShieldAlert,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { AttackPathGraph as GraphType } from "@/lib/schemas";

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

function ForensicsNode({ data }: NodeProps) {
  const Icon = ICON_MAP[data.icon as string] || Server;
  const status = (data.status as string) || "dormant";

  const getStatusStyles = () => {
    switch (status) {
      case "compromised":
        return "border-[#E85D4E] bg-[#1A1315] text-[#E85D4E]";
      case "targeted":
        return "border-[#D4A94E] bg-[#1A1712] text-[#D4A94E]";
      case "discovered":
        return "border-[#4A9EFF] bg-[#111720] text-[#4A9EFF]";
      default:
        return "border-[#222730] bg-[#14171C] text-[#8B92A0] opacity-50";
    }
  };

  const getBadgeVariant = (): "risk" | "mitre" | "info" | "neutral" => {
    switch (status) {
      case "compromised":
        return "risk";
      case "targeted":
        return "mitre";
      case "discovered":
        return "info";
      default:
        return "neutral";
    }
  };

  return (
    <div
      tabIndex={0}
      role="button"
      aria-label={`Topology node ${data.label}, status ${status}`}
      className={`relative px-3.5 py-2.5 rounded-lg border transition-all min-w-[190px] cursor-pointer focus:outline-none focus:ring-1 focus:ring-[#4A9EFF] ${getStatusStyles()}`}
    >
      <Handle type="target" position={Position.Left} className="w-2 h-2 bg-[#4A9EFF] border-[#0B0D10]" />

      <div className="flex items-center justify-between gap-2">
        <div className="p-1.5 rounded bg-[#101318] border border-[#222730]">
          <Icon className="h-3.5 w-3.5" />
        </div>
        <Badge variant={getBadgeVariant()}>{status.toUpperCase()}</Badge>
      </div>

      <div className="mt-2 font-mono">
        <div className="text-xs font-bold text-[#E8EAED] tracking-tight">{data.label as string}</div>
        <div className="text-[10px] text-[#8B92A0] truncate">{data.ip as string}</div>
        <div className="text-[9px] text-[#8B92A0] mt-0.5 truncate">{data.service as string}</div>
      </div>

      <Handle type="source" position={Position.Right} className="w-2 h-2 bg-[#4A9EFF] border-[#0B0D10]" />
    </div>
  );
}

interface AttackPathGraphProps {
  graphData: GraphType;
  selectedSession: string | null;
}

export function AttackPathGraph({ graphData, selectedSession }: AttackPathGraphProps) {
  const [activeNode, setActiveNode] = useState<{
    label?: string;
    ip?: string;
    service?: string;
    status?: string;
  } | null>(null);

  const nodeTypes = useMemo(() => ({ custom: ForensicsNode }), []);

  const onNodeClick = (_: unknown, node: Node) => {
    setActiveNode(node.data as typeof activeNode);
  };

  return (
    <div className="relative flex flex-col h-[520px] rounded-lg border border-[#222730] bg-[#0E1116] shadow-xl overflow-hidden">
      {/* Forensic Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[#222730] bg-[#101318] z-10 font-mono">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-[#4A9EFF]" />
          <span className="text-xs font-bold uppercase tracking-wider text-[#E8EAED]">
            Lateral Movement & Lateral Pivoting Graph (React Flow)
          </span>
          {selectedSession && (
            <span className="text-[10px] text-[#8B92A0]">[{selectedSession}]</span>
          )}
        </div>

        <div className="flex items-center gap-3 text-[11px]">
          <span className="flex items-center gap-1.5 text-[#E85D4E]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#E85D4E]" /> Compromised
          </span>
          <span className="flex items-center gap-1.5 text-[#D4A94E]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#D4A94E]" /> Targeted
          </span>
          <span className="flex items-center gap-1.5 text-[#4A9EFF]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#4A9EFF]" /> Discovered
          </span>
          <span className="flex items-center gap-1.5 text-[#8B92A0]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#222730]" /> Dormant
          </span>
        </div>
      </div>

      {/* React Flow Canvas */}
      <div className="flex-1 w-full h-full">
        <ReactFlow
          nodes={graphData.nodes as Node[]}
          edges={graphData.edges as Edge[]}
          nodeTypes={nodeTypes}
          onNodeClick={onNodeClick}
          fitView
          attributionPosition="bottom-left"
          minZoom={0.5}
          maxZoom={1.5}
        >
          <Background color="#1A1E26" gap={20} size={1} />
          <Controls />
        </ReactFlow>
      </div>

      {/* Forensic Node Inspection Drawer */}
      {activeNode && (
        <div className="absolute right-4 top-14 w-80 p-4 rounded-lg border border-[#222730] bg-[#14171C]/95 shadow-2xl backdrop-blur-md z-20 font-mono text-xs animate-in fade-in">
          <div className="flex items-center justify-between border-b border-[#222730] pb-2">
            <div className="flex items-center gap-2">
              <Info className="h-4 w-4 text-[#4A9EFF]" />
              <span className="font-bold text-[#E8EAED]">{activeNode.label}</span>
            </div>
            <button
              onClick={() => setActiveNode(null)}
              className="text-[#8B92A0] hover:text-[#E8EAED] p-1 rounded hover:bg-[#1E232B]"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="mt-3 space-y-2 text-[11px]">
            <div>
              <span className="text-[#8B92A0]">IP / Endpoint:</span>
              <p className="text-[#4A9EFF] font-bold mt-0.5">{activeNode.ip}</p>
            </div>
            <div>
              <span className="text-[#8B92A0]">Service Emulation:</span>
              <p className="text-[#E8EAED]">{activeNode.service}</p>
            </div>
            <div>
              <span className="text-[#8B92A0]">Adversary Status:</span>
              <p className="font-bold uppercase tracking-wider text-[#D4A94E] mt-0.5">
                {activeNode.status}
              </p>
            </div>
            <div className="pt-2 border-t border-[#222730]">
              <span className="text-[#8B92A0]">Autonomous Canary Surface:</span>
              <div className="mt-1 p-2 rounded bg-[#0B0D10] border border-[#222730] text-[#36B37E]">
                ✓ Synthetic Deception Token Armed
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
