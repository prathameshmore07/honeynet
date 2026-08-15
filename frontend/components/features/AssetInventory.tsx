"use client";

import React, { useState } from "react";
import { Layers, FileText, Key, Database, Users, Shield, CheckCircle2 } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { DeceptionAsset } from "@/lib/schemas";

interface AssetInventoryProps {
  assets: DeceptionAsset[];
}

export function AssetInventory({ assets }: AssetInventoryProps) {
  const [filterCat, setFilterCat] = useState<string>("all");

  const categories = ["all", "git", "aws", "finance", "hr", "database"];

  const filteredAssets = assets.filter(
    (a) => filterCat === "all" || a.category === filterCat
  );

  const getCategoryIcon = (cat: string) => {
    switch (cat) {
      case "git":
        return <Key className="h-3.5 w-3.5 text-[#4A9EFF]" />;
      case "aws":
        return <Shield className="h-3.5 w-3.5 text-[#D4A94E]" />;
      case "finance":
        return <FileText className="h-3.5 w-3.5 text-[#E85D4E]" />;
      case "hr":
        return <Users className="h-3.5 w-3.5 text-[#36B37E]" />;
      case "database":
        return <Database className="h-3.5 w-3.5 text-[#4A9EFF]" />;
      default:
        return <FileText className="h-3.5 w-3.5 text-[#8B92A0]" />;
    }
  };

  return (
    <div className="flex flex-col rounded-lg border border-[#222730] bg-[#14171C] shadow-lg overflow-hidden font-mono">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 border-b border-[#222730] bg-[#101318]">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-[#D4A94E]" />
          <span className="text-xs font-bold uppercase tracking-wider text-[#E8EAED]">
            Deception Honeytoken & Evidence Vault
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#191D24] text-[#8B92A0] tabular-nums">
            {filteredAssets.length} active
          </span>
        </div>

        <div className="flex items-center gap-1 bg-[#0B0D10] p-0.5 rounded border border-[#222730]">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setFilterCat(cat)}
              className={`px-2 py-0.5 text-[10px] rounded uppercase transition-all ${
                filterCat === cat
                  ? "bg-[#D4A94E] text-black font-bold"
                  : "text-[#8B92A0] hover:text-[#E8EAED]"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto bg-[#0E1116]">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-[#222730] bg-[#101318] text-[#8B92A0] uppercase text-[9px]">
            <tr>
              <th className="px-3.5 py-2">Domain</th>
              <th className="px-3.5 py-2">Injected Path</th>
              <th className="px-3.5 py-2">Canary Type</th>
              <th className="px-3.5 py-2">Artifact Scope</th>
              <th className="px-3.5 py-2">Exposure</th>
              <th className="px-3.5 py-2 text-right">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#222730]/60 text-[#E8EAED]">
            {filteredAssets.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-[#8B92A0] font-sans">
                  No deception artifacts deployed yet. Run an attack scenario to observe real-time honeytoken provisioning.
                </td>
              </tr>
            ) : (
              filteredAssets.map((asset, idx) => (
                <tr key={idx} className="hover:bg-[#14171C] transition-colors">
                  <td className="px-3.5 py-2">
                    <div className="flex items-center gap-1.5">
                      {getCategoryIcon(asset.category)}
                      <span className="font-bold uppercase text-[10px] text-[#E8EAED]">
                        {asset.category}
                      </span>
                    </div>
                  </td>
                  <td className="px-3.5 py-2 font-bold text-[#4A9EFF] text-[11px]">
                    {asset.file_path}
                  </td>
                  <td className="px-3.5 py-2">
                    <Badge variant="mitre">{asset.canary_type}</Badge>
                  </td>
                  <td className="px-3.5 py-2 text-[#8B92A0] max-w-xs truncate font-sans text-[11px]">
                    {asset.content_summary}
                  </td>
                  <td className="px-3.5 py-2">
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#36B37E]">
                      <CheckCircle2 className="h-3 w-3" />
                      {asset.exposure_count}x
                    </span>
                  </td>
                  <td className="px-3.5 py-2 text-right text-[#8B92A0] text-[10px] tabular-nums">
                    {asset.created_at?.split("T")[1]?.slice(0, 8) || "RECENT"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
