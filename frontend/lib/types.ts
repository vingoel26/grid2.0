export type EnforcementAction = "AUTO_ENFORCE" | "HUMAN_REVIEW" | "LOG_ONLY";
export type ReviewStatus = "PENDING" | "CONFIRMED" | "REJECTED";

export interface Violation {
  id: string;
  violation_id: string;
  violation_type: string;
  violation_code: string;
  fine_inr: number;
  camera_id: string;
  camera_name?: string | null;
  raw_confidence: number;
  final_confidence: number;
  enforcement_action: EnforcementAction;
  vehicle_type?: string | null;
  plate_number?: string | null;
  plate_confidence?: number | null;
  vehicle_bbox?: number[] | null;
  evidence_image_path?: string | null;
  evidence_thumbnail_path?: string | null;
  evidence_video_path?: string | null;
  evidence_hash?: string | null;
  location_lat?: number | null;
  location_lng?: number | null;
  location_name?: string | null;
  status: ReviewStatus;
  reviewed_by?: string | null;
  review_notes?: string | null;
  reviewed_at?: string | null;
  gemini_verdict?: string | null;
  gemini_explanation?: string | null;
  model_version?: string | null;
  pipeline_latency_ms?: number | null;
  occurred_at: string;
  created_at: string;
}

export interface ViolationList {
  total: number;
  page: number;
  page_size: number;
  items: Violation[];
}

export interface Challan {
  id: string;
  challan_number: string;
  violation_id: string;
  
  owner_name?: string | null;
  owner_phone?: string | null;
  owner_email?: string | null;
  owner_address?: string | null;
  
  status: string;
  sent_via?: string | null;
  sent_at?: string | null;
  delivered_at?: string | null;
  
  pdf_path?: string | null;
  
  payment_due_date?: string | null;
  payment_status: string;
  payment_ref?: string | null;
  
  created_at: string;
  updated_at: string;
}

export interface ChallanList {
  total: number;
  page: number;
  page_size: number;
  items: Challan[];
}

export interface Summary {
  total_today: number;
  total_all_time: number;
  auto_enforced: number;
  pending_review: number;
  avg_latency_ms: number;
  by_type: Record<string, number>;
  by_action: Record<string, number>;
  pct_change_vs_yesterday: number;
}

export interface HourlyPoint { hour: string; count: number; }
export interface HeatmapPoint {
  lat: number; lng: number; count: number; camera_id: string; camera_name?: string | null;
}

export interface Camera {
  id: string;
  name: string;
  location_lat?: number | null;
  location_lng?: number | null;
  rtsp_url?: string | null;
  expected_flow_direction: number;
  stop_line_polygon?: number[][] | null;
  intersection_polygon?: number[][] | null;
  no_parking_zones?: number[][][] | null;
  is_active: boolean;
  created_at: string;
}
