export interface VMResult {
  server_id: string;
  vcpu_usage: number;
  ram_usage: number;
  region: string;
  target_region: string;
  cost: number;
  carbon_intensity: number;
  carbon_saving: number;
  ml_anomaly: number;
  vm_status: "Healthy" | "Bad";
  final_action: string;
  estimated_savings: number;
  reason: string;
}

export interface DashboardSummary {
  totalVMs: number;
  anomalies: number;
  migrationRecs: number;
  totalSavings: number;
  totalCarbonReduction: number;
  highestCarbonRegion: string;
  healthyVMs: number;
  badVMs: number;
}
