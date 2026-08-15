import { z } from "zod";

export const CommandEventSchema = z.object({
  id: z.number().nullish(),
  session_id: z.string(),
  src_ip: z.string(),
  command: z.string(),
  category: z.string().default("other"),
  classification_method: z.string().nullish(),
  files_served: z.array(z.string()).default([]),
  mitre_tag: z.string().nullish(),
  mitre_name: z.string().nullish(),
  event_risk_score: z.number().default(10),
  session_risk_score: z.number().nullish(),
  skill_level: z.string().nullish(),
  inferred_intent: z.string().nullish(),
  timestamp: z.string(),
});

export type CommandEvent = z.infer<typeof CommandEventSchema>;

export const SessionSummarySchema = z.object({
  session_id: z.string(),
  src_ip: z.string(),
  start_time: z.string(),
  last_active: z.string(),
  total_commands: z.number().default(0),
  categories_triggered: z.array(z.string()).default([]),
  risk_score: z.number().default(0),
  inferred_intent: z.string().default("Reconnaissance"),
  skill_level: z.string().default("Opportunistic"),
  goal_summary: z.string().default("Initial reconnaissance probing"),
  ai_summary: z.string().default(""),
  pivot_depth: z.number().default(1),
});

export type SessionSummary = z.infer<typeof SessionSummarySchema>;

export const OverviewMetricsSchema = z.object({
  total_sessions: z.number().default(0),
  active_attackers: z.number().default(0),
  total_commands: z.number().default(0),
  assets_deployed: z.number().default(0),
  avg_risk_score: z.number().default(0),
  highest_risk_score: z.number().default(0),
  top_intent: z.string().default("None"),
  ollama_status: z.string().default("Active"),
  cowrie_status: z.string().default("Active"),
});

export type OverviewMetrics = z.infer<typeof OverviewMetricsSchema>;

export const DeceptionAssetSchema = z.object({
  id: z.number().optional().nullable(),
  session_id: z.string(),
  category: z.string(),
  file_path: z.string(),
  canary_type: z.string(),
  content_summary: z.string(),
  exposure_count: z.number().default(1),
  created_at: z.string(),
});

export type DeceptionAsset = z.infer<typeof DeceptionAssetSchema>;

export const MitreStatSchema = z.object({
  mitre_tag: z.string(),
  mitre_name: z.string(),
  count: z.number().default(0),
  last_seen: z.string().optional().nullable(),
  sample_command: z.string().optional().nullable(),
});

export type MitreStat = z.infer<typeof MitreStatSchema>;

export const AttackPathNodeDataSchema = z.object({
  label: z.string(),
  nodeType: z.string(),
  ip: z.string(),
  service: z.string(),
  status: z.string(),
  icon: z.string(),
});

export const AttackPathNodeSchema = z.object({
  id: z.string(),
  type: z.string().default("custom"),
  position: z.object({
    x: z.number(),
    y: z.number(),
  }),
  data: AttackPathNodeDataSchema,
});

export type AttackPathNode = z.infer<typeof AttackPathNodeSchema>;

export const AttackPathEdgeSchema = z.object({
  id: z.string(),
  source: z.string(),
  target: z.string(),
  label: z.string(),
  animated: z.boolean().default(false),
  style: z.record(z.string(), z.any()).optional(),
  data: z.record(z.string(), z.any()).optional(),
});

export type AttackPathEdge = z.infer<typeof AttackPathEdgeSchema>;

export const AttackPathGraphSchema = z.object({
  nodes: z.array(AttackPathNodeSchema).default([]),
  edges: z.array(AttackPathEdgeSchema).default([]),
});

export type AttackPathGraph = z.infer<typeof AttackPathGraphSchema>;
