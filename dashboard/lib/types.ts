export type BehaviorMode =
  | "honest"
  | "under_reporter"
  | "over_reporter"
  | "colluder";

export type RoutingStrategy = "round_robin" | "trust_aware";

export interface NodeMetrics {
  cpu_percent: number;
  memory_percent: number;
  active_requests: number;
  total_requests_last_5s: number;
  avg_response_time_ms: number;
  uptime_seconds: number;
}

export interface QuarantineStatus {
  is_quarantined: boolean;
  quarantine_count: number;
  quarantine_since: number | null;
  remaining_seconds: number | null;
}

export interface BootstrapStatus {
  honest_reports_count: number;
  is_in_bootstrap: boolean;
}

export interface CrossValidationResult {
  claimed_load: number;
  claimed_response_time: number;
  claimed_requests_5s?: number;
  observed_load?: number;
  expected_observed?: number;
  tolerance?: number;
  observed_avg: number | null;
  observed_p95: number | null;
  observed_count: number;
  discrepancy: number;
  has_sufficient_data: boolean;
}

export interface TrustEvent {
  node_id: string;
  event_type: string;
  timestamp: number;
  trust_score_before: number;
  trust_score_after: number;
  delta: number;
  discrepancy: number;
  is_quarantined: boolean;
  quarantine_count: number;
}

export interface NodeTrustDetails {
  node_id: string;
  trust_score: number | null;
  bootstrap: BootstrapStatus | null;
  quarantine: QuarantineStatus;
  cross_validation: CrossValidationResult | null;
  recent_history: TrustEvent[];
}

export interface NodeSummary {
  node_id: string;
  trust_score: number;
  is_quarantined: boolean;
  is_attacking: boolean;
  behavior_mode?: BehaviorMode;
}

export interface ScenarioConfig {
  scenario_id: string;
  name: string;
  description: string;
  total_nodes: number;
  target_nodes: number;
  duration_seconds: number;
  defense_enabled: boolean;
}

export interface ScenarioResult {
  scenario_id: string;
  repetition_number: number;
  random_seed: number;
  started_at: number;
  completed_at: number;
  duration_seconds: number;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  success_rate: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  detection_time_seconds: number | null;
  nodes_quarantined: string[];
  initial_trust_scores: Record<string, number>;
  final_trust_scores: Record<string, number>;
}

export interface ExperimentSummary {
  scenario_id: string;
  file_name: string;
  repetition_number: number;
  started_at: number;
  detection_time_seconds: number | null;
  success_rate: number;
  nodes_quarantined: string[];
}

export interface TrainInfo {
  train_id: string;
  name: string;
  source: string;
  destination: string;
  departure: string;
  total_seats: number;
  available_seats: number;
  price: number;
}

export interface BookingResult {
  id: string;
  timestamp: number;
  success: boolean;
  booking_id?: string;
  train_name?: string;
  passenger_name: string;
  response_time_ms: number;
  node_id?: string;
  error?: string;
}

export type LogLevel = "info" | "warn" | "error" | "success";

export interface ActivityLogEntry {
  id: string;
  timestamp: number;
  level: LogLevel;
  message: string;
}