"use client";

import React, { useState } from "react";
import { Play, X, Zap, Key, Shield, FileText, Users, Compass, Check } from "lucide-react";

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
      description: "End-to-end campaign: Bastion → GitLab (.env) → AWS S3 → PostgreSQL → Treasury → HR.",
      icon: Compass,
      badge: "RECOMMENDED",
    },
    {
      id: "git",
      name: "Git & Developer Credential Hunter",
      description: "Hunts for production .env files, database connection strings, and git commit history.",
      icon: Key,
      badge: "CREDENTIALS",
    },
    {
      id: "aws",
      name: "AWS Cloud Infrastructure Reconnaissance",
      description: "Targets AWS CLI credentials, S3 backup buckets, and EC2 topology JSON.",
      icon: Shield,
      badge: "CLOUD RECON",
    },
    {
      id: "finance",
      name: "Financial Data & SWIFT Wire Scout",
      description: "Exfiltrates 2026 payroll spreadsheets, operating budgets, and wire transfer memos.",
      icon: FileText,
      badge: "FINANCIAL",
    },
    {
      id: "hr",
      name: "HR & Employee PII Exfiltration",
      description: "Harvests confidential staff directory, executive contracts, and corporate org charts.",
      icon: Users,
      badge: "PII RECON",
    },
  ];

  const handleLaunch = async () => {
    setIsSubmitting(true);
    setStatusMessage("Streaming telemetry to honeypot bus...");
    try {
      await onTrigger(selectedScenario, delay);
      setStatusMessage("Scenario active! Observing live telemetry.");
      setTimeout(() => {
        setIsSubmitting(false);
        setStatusMessage(null);
        onClose();
      }, 1000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to trigger simulation";
      setStatusMessage(`Error: ${msg}`);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150 font-mono">
      <div className="relative w-full max-w-xl rounded-lg border border-[#222730] bg-[#14171C] p-5 shadow-2xl space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#222730] pb-3">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-[#4A9EFF]" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#E8EAED]">
              Automated Adversary Campaign Simulator
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-[#8B92A0] hover:text-[#E8EAED] hover:bg-[#1E232B]"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Scenario Grid */}
        <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
          {scenarios.map((sc) => {
            const Icon = sc.icon;
            const isSelected = selectedScenario === sc.id;
            return (
              <div
                key={sc.id}
                onClick={() => setSelectedScenario(sc.id)}
                className={`p-3 rounded border transition-all cursor-pointer flex items-start gap-3 ${
                  isSelected
                    ? "border-[#4A9EFF] bg-[#191D24] text-[#E8EAED]"
                    : "border-[#222730] bg-[#101318] hover:bg-[#14171C] text-[#8B92A0]"
                }`}
              >
                <div className="p-1.5 rounded bg-[#0B0D10] border border-[#222730] shrink-0 mt-0.5">
                  <Icon className="h-4 w-4 text-[#4A9EFF]" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-[#E8EAED]">{sc.name}</span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-[#0B0D10] border border-[#222730] text-[#D4A94E]">
                      {sc.badge}
                    </span>
                  </div>
                  <p className="text-[10px] text-[#8B92A0] mt-0.5 font-sans leading-relaxed">
                    {sc.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Speed Slider & Action Bar */}
        <div className="pt-3 border-t border-[#222730] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-[#8B92A0]">
            <span>Delay:</span>
            <input
              type="range"
              min="0.1"
              max="1.5"
              step="0.1"
              value={delay}
              onChange={(e) => setDelay(parseFloat(e.target.value))}
              className="accent-[#4A9EFF] cursor-pointer w-20"
            />
            <span className="text-[#4A9EFF] font-bold tabular-nums">{delay}s</span>
          </div>

          <div className="flex items-center gap-2">
            {statusMessage && (
              <span className="text-[11px] text-[#36B37E] font-medium animate-pulse flex items-center gap-1">
                <Check className="h-3 w-3" />
                {statusMessage}
              </span>
            )}

            <button
              onClick={onClose}
              className="px-3 py-1.5 rounded border border-[#222730] bg-[#101318] text-[#8B92A0] hover:text-[#E8EAED] hover:bg-[#1E232B] transition-all"
            >
              Cancel
            </button>

            <button
              onClick={handleLaunch}
              disabled={isSubmitting}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded border border-[#4A9EFF]/40 bg-[#4A9EFF]/20 hover:bg-[#4A9EFF]/30 text-[#4A9EFF] hover:text-white font-bold transition-all disabled:opacity-50"
            >
              <Play className="h-3 w-3 fill-current" />
              {isSubmitting ? "Executing..." : "Run Campaign"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
