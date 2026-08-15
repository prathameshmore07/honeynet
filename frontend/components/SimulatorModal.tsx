"use client";

import React, { useState } from "react";
import { Play, X, Zap, Shield, Key, FileText, Users, Compass, Check } from "lucide-react";

interface SimulatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTrigger: (scenario: string, delay: number) => Promise<void>;
}

export function SimulatorModal({ isOpen, onClose, onTrigger }: SimulatorModalProps) {
  const [selectedScenario, setSelectedScenario] = useState<string>("full_apt");
  const [delay, setDelay] = useState<number>(0.5);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const scenarios = [
    {
      id: "full_apt",
      name: "Full Multi-Stage APT Lateral Pivot Chain",
      description: "End-to-end campaign pivoting across Bastion → GitLab (.env) → AWS S3 → PostgreSQL → Treasury → HR.",
      icon: Compass,
      color: "border-rose-500/60 bg-rose-950/20 text-rose-300",
      badge: "RECOMMENDED FOR DEMO",
    },
    {
      id: "git",
      name: "Git & Production Credential Hunter",
      description: "Hunts for .env files, database JSON credentials, and git commit history secrets.",
      icon: Key,
      color: "border-cyan-500/60 bg-cyan-950/20 text-cyan-300",
      badge: "CREDENTIAL THEFT",
    },
    {
      id: "aws",
      name: "AWS Cloud Infrastructure Recon",
      description: "Targets AWS CLI credentials, S3 backup buckets, and EC2 topology json.",
      icon: Shield,
      color: "border-amber-500/60 bg-amber-950/20 text-amber-300",
      badge: "CLOUD RECON",
    },
    {
      id: "finance",
      name: "Financial & Wire Authorization Scout",
      description: "Exfiltrates 2026 payroll spreadsheets, operating budgets, and SWIFT transfer memos.",
      icon: FileText,
      color: "border-emerald-500/60 bg-emerald-950/20 text-emerald-300",
      badge: "FINANCIAL DATA",
    },
    {
      id: "hr",
      name: "HR & Employee PII Exfiltration",
      description: "Harvests confidential employee rosters, executive CTO offer letters, and org charts.",
      icon: Users,
      color: "border-purple-500/60 bg-purple-950/20 text-purple-300",
      badge: "PII HARVESTING",
    },
  ];

  const handleLaunch = async () => {
    setIsSubmitting(true);
    setStatusMessage("Triggering Honeypot telemetry stream...");
    try {
      await onTrigger(selectedScenario, delay);
      setStatusMessage("Simulation running! Watch the Live Terminal & Attack Path Graph.");
      setTimeout(() => {
        setIsSubmitting(false);
        setStatusMessage(null);
        onClose();
      }, 1200);
    } catch (err: any) {
      setStatusMessage(`Error: ${err.message || "Failed to trigger simulation"}`);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl rounded-2xl border border-slate-700 bg-[#0c1222] p-6 shadow-2xl space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Zap className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Live Attack Simulator Controls</h3>
              <p className="text-xs text-slate-400">
                Execute automated threat actor campaigns to test AI intent classification and lateral deception.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Scenario Selection Grid */}
        <div className="space-y-2.5 max-h-[340px] overflow-y-auto pr-1">
          {scenarios.map((sc) => {
            const Icon = sc.icon;
            const isSelected = selectedScenario === sc.id;
            return (
              <div
                key={sc.id}
                onClick={() => setSelectedScenario(sc.id)}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-start gap-3.5 ${
                  isSelected
                    ? `${sc.color} ring-1 ring-cyan-500 shadow-md`
                    : "border-slate-800/80 bg-slate-900/40 hover:bg-slate-900/80 text-slate-300"
                }`}
              >
                <div className="p-2 rounded-lg bg-slate-950/80 border border-slate-800 shrink-0 mt-0.5">
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-white">{sc.name}</span>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-950/80 border border-slate-800 text-cyan-300">
                      {sc.badge}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">{sc.description}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Speed Slider & Actions */}
        <div className="pt-2 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3 text-xs">
            <span className="text-slate-400 font-mono">Command Delay:</span>
            <input
              type="range"
              min="0.1"
              max="1.5"
              step="0.1"
              value={delay}
              onChange={(e) => setDelay(parseFloat(e.target.value))}
              className="accent-cyan-500 cursor-pointer w-24"
            />
            <span className="font-mono text-cyan-300 font-bold">{delay}s</span>
          </div>

          <div className="flex items-center gap-3">
            {statusMessage && (
              <span className="text-xs text-emerald-400 font-medium animate-pulse flex items-center gap-1">
                <Check className="h-3.5 w-3.5" />
                {statusMessage}
              </span>
            )}

            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg border border-slate-700 bg-slate-800 text-xs font-semibold text-slate-300 hover:bg-slate-700 transition-all"
            >
              Cancel
            </button>

            <button
              onClick={handleLaunch}
              disabled={isSubmitting}
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 text-white text-xs font-bold shadow-lg shadow-cyan-950/50 transition-all disabled:opacity-50"
            >
              <Play className="h-3.5 w-3.5 fill-white" />
              {isSubmitting ? "Launching..." : "Execute Campaign"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
