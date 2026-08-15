"use client";

import React, { useState } from "react";
import { Layers, FileText, Key, Database, Users, Shield, CheckCircle2 } from "lucide-react";

export interface DeceptionAsset {
  id?: number;
  session_id: string;
  category: string;
  file_path: string;
  canary_type: string;
  content_summary: string;
  exposure_count: number;
  created_at: string;
}

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
        return <Key className="h-4 w-4 text-cyan-400" />;
      case "aws":
        return <Shield className="h-4 w-4 text-amber-400" />;
      case "finance":
        return <FileText className="h-4 w-4 text-emerald-400" />;
      case "hr":
        return <Users className="h-4 w-4 text-purple-400" />;
      case "database":
        return <Database className="h-4 w-4 text-blue-400" />;
      default:
        return <FileText className="h-4 w-4 text-slate-400" />;
    }
  };

  return (
    <div className="flex flex-col rounded-xl border border-slate-800 bg-[#0a0f1d] shadow-xl overflow-hidden">
      {/* Header & Filter */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-b border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-amber-400" />
          <span className="text-sm font-semibold text-white">Dynamic Deception Asset Inventory</span>
          <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
            {filteredAssets.length} Honeytokens Active
          </span>
        </div>

        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setFilterCat(cat)}
              className={`px-2 py-0.5 text-xs rounded-md font-mono uppercase transition-all ${
                filterCat === cat
                  ? "bg-amber-600 text-white font-bold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Asset Table */}
      <div className="overflow-x-auto bg-[#080d1a]">
        <table className="w-full text-left text-xs font-mono">
          <thead className="border-b border-slate-800 bg-slate-900/40 text-slate-400 uppercase text-[10px]">
            <tr>
              <th className="px-4 py-2.5">Category</th>
              <th className="px-4 py-2.5">Injected Deception Path</th>
              <th className="px-4 py-2.5">Canary Type</th>
              <th className="px-4 py-2.5">Description</th>
              <th className="px-4 py-2.5">Exposure</th>
              <th className="px-4 py-2.5 text-right">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {filteredAssets.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500 font-sans">
                  No deception assets deployed yet. Run an attack scenario to observe dynamic honeytoken generation.
                </td>
              </tr>
            ) : (
              filteredAssets.map((asset, idx) => (
                <tr key={idx} className="hover:bg-slate-900/50 transition-colors">
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-2">
                      {getCategoryIcon(asset.category)}
                      <span className="font-semibold text-white uppercase text-[11px]">
                        {asset.category}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 font-bold text-cyan-300">
                    {asset.file_path}
                  </td>
                  <td className="px-4 py-2.5 text-slate-400">
                    <span className="px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-[10px] text-amber-300">
                      {asset.canary_type}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-slate-300 max-w-xs truncate font-sans text-xs">
                    {asset.content_summary}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-950 border border-emerald-800 text-emerald-300 text-[10px] font-bold">
                      <CheckCircle2 className="h-3 w-3" />
                      {asset.exposure_count}x seen
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right text-slate-500 text-[11px]">
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
