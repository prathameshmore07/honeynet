import {
  OverviewMetricsSchema,
  OverviewMetrics,
  SessionSummarySchema,
  SessionSummary,
  CommandEventSchema,
  CommandEvent,
  DeceptionAssetSchema,
  DeceptionAsset,
  MitreStatSchema,
  MitreStat,
  AttackPathGraphSchema,
  AttackPathGraph,
} from "./schemas";
import { z } from "zod";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAndValidate<T>(url: string, schema: z.ZodType<T>): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`API Error ${res.status}: ${res.statusText}`);
  }
  const data = await res.json();
  const result = schema.safeParse(data);
  if (!result.success) {
    console.warn(`Zod Validation warning for ${url}:`, result.error);
    // Return parsed data if schema parsing failed gracefully
    return data as T;
  }
  return result.data;
}

export const api = {
  getOverview: (): Promise<OverviewMetrics> =>
    fetchAndValidate(`${API_BASE}/api/overview`, OverviewMetricsSchema),

  getSessions: (): Promise<SessionSummary[]> =>
    fetchAndValidate(`${API_BASE}/api/sessions`, z.array(SessionSummarySchema)),

  getEvents: (limit: number = 100): Promise<CommandEvent[]> =>
    fetchAndValidate(`${API_BASE}/api/events?limit=${limit}`, z.array(CommandEventSchema)),

  getAssets: (): Promise<DeceptionAsset[]> =>
    fetchAndValidate(`${API_BASE}/api/assets`, z.array(DeceptionAssetSchema)),

  getMitreMatrix: (): Promise<MitreStat[]> =>
    fetchAndValidate(`${API_BASE}/api/mitre-matrix`, z.array(MitreStatSchema)),

  getAttackPath: (sessionId: string): Promise<AttackPathGraph> =>
    fetchAndValidate(`${API_BASE}/api/attack-path/${sessionId}`, AttackPathGraphSchema),

  triggerSimulation: async (scenario: string, delay: number, ip?: string): Promise<{ status: string; message: string }> => {
    const res = await fetch(`${API_BASE}/api/simulator/trigger`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario, delay, ip }),
    });
    if (!res.ok) {
      throw new Error(`Simulator trigger failed: ${res.statusText}`);
    }
    return res.json();
  },
};
