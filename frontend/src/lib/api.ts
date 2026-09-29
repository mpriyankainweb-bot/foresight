export const DEFAULT_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';
export const MASTER_API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'foresight-secret-key-123';

export function getApiBaseUrl(): string {
  if (typeof window !== 'undefined' && !process.env.NEXT_PUBLIC_API_BASE_URL) {
    // Relative path works via Next.js proxy rewrites in browser
    return '';
  }
  return DEFAULT_API_BASE_URL;
}

export function getApiKey(): string {
  if (typeof window !== 'undefined') {
    const customKey = localStorage.getItem('foresight_api_key');
    if (customKey) return customKey;
  }
  return MASTER_API_KEY;
}

export interface HealthResponse {
  status: string;
  mode: string;
  memory_backend: string;
  llm_backend: string;
  version: string;
}

export interface SimilarIncidentItem {
  id: string;
  title: string;
  date: string;
  similarity_reason: string;
  fix_that_worked: string;
  fix_that_failed?: string | null;
  held_for_days?: number | null;
}

export interface MemoryCitationItem {
  id: string;
  text: string;
  score: number;
  tags: string[];
}

export interface DeployCheckRequest {
  service: string;
  title: string;
  description?: string;
  diff?: string;
  config_changes?: string[];
  environment?: string;
  author?: string;
  memory_enabled?: boolean;
}

export interface DeployCheckResponse {
  check_id: string;
  risk_score: number;
  verdict: 'SHIP' | 'CANARY' | 'HOLD';
  summary: string;
  reasons: string[];
  similar_incidents: SimilarIncidentItem[];
  canary_plan: string;
  rollback_plan: string;
  memory_citations: MemoryCitationItem[];
  memory_used: boolean;
}

export interface DeployOutcomeRequest {
  outcome: 'clean' | 'degraded' | 'incident';
  notes?: string;
}

export interface DeployOutcomeResponse {
  status: string;
  check_id: string;
  outcome: string;
}

export interface CreateIncidentRequest {
  service: string;
  title: string;
  alerts?: string;
  logs?: string;
}

export interface FixSuggestionItem {
  id: string;
  description: string;
  outcome: 'worked' | 'failed' | 'temporary';
  held_for_days?: number | null;
  confidence: number;
  source_incident_id?: string | null;
  reasoning: string;
}

export interface CreateIncidentResponse {
  incident_id: string;
  service: string;
  title: string;
  status: string;
  ranked_fix_suggestions: FixSuggestionItem[];
  memory_citations: MemoryCitationItem[];
  memory_used: boolean;
}

export interface LogFixAttemptRequest {
  description: string;
  outcome: 'worked' | 'failed' | 'temporary';
  held_for_days?: number | null;
  notes?: string;
}

export interface LogFixAttemptResponse {
  status: string;
  attempt_id: string;
  incident_id: string;
  outcome: string;
}

export interface ResolveIncidentRequest {
  root_cause?: string;
  resolution_notes?: string;
}

export interface PostmortemDraft {
  title: string;
  summary: string;
  root_cause: string;
  timeline: string[];
  fix_that_worked: string;
  fixes_that_failed: string[];
  temporary_fixes: string[];
  action_items: string[];
}

export interface ResolveIncidentResponse {
  status: string;
  incident_id: string;
  postmortem: PostmortemDraft;
}

export interface MemorySearchResultItem {
  id: string;
  content: string;
  created_at: string;
  tags: string[];
  score: number;
}

export interface MemorySearchResponse {
  query: string;
  count: number;
  memory_backend: string;
  results: MemorySearchResultItem[];
}

export interface LearningCurveDataPoint {
  date: string;
  memory_count: number;
  prediction_accuracy: number;
  mttr_minutes: number;
}

export interface TopRecurringCause {
  cause: string;
  count: number;
}

export interface TemporaryFixItem {
  incident_id: string;
  description: string;
  held_for_days: number;
}

export interface AnalyticsResponse {
  data_points: LearningCurveDataPoint[];
  current_accuracy: number;
  current_mttr_minutes: number;
  top_recurring_causes: TopRecurringCause[];
  temporary_fixes: TemporaryFixItem[];
}

export interface GenerateApiKeyResponse {
  api_key: string;
  name: string;
  created_at: string;
}

export interface DemoReplayResponse {
  status: string;
  total_retained: number;
  incidents_retained: number;
  deploys_retained: number;
  message: string;
}

export interface DemoResetResponse {
  status: string;
  message: string;
}

async function fetchApi<T>(path: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = getApiBaseUrl();
  let apiKey = getApiKey();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-API-Key': apiKey,
    ...(options.headers as Record<string, string> || {}),
  };

  const url = `${baseUrl}${path}`;
  let response: Response;

  try {
    response = await fetch(url, { ...options, headers });
  } catch (err: any) {
    throw new Error(`Failed to fetch from backend at ${baseUrl || 'server'}. Please verify the Foresight API server is running on port 8000.`);
  }

  if (response.status === 401 && typeof window !== 'undefined' && localStorage.getItem('foresight_api_key')) {
    // If custom localStorage key failed with 401, clear it and retry with master key
    localStorage.removeItem('foresight_api_key');
    headers['X-API-Key'] = MASTER_API_KEY;
    try {
      response = await fetch(url, { ...options, headers });
    } catch (err: any) {
      throw new Error(`Failed to fetch from backend at ${baseUrl || 'server'}. Please verify the Foresight API server is running on port 8000.`);
    }
  }

  if (!response.ok) {
    let errorData: any;
    try {
      errorData = await response.json();
    } catch {
      errorData = { error: { message: response.statusText || 'Network request failed' } };
    }
    const message = errorData?.error?.message || errorData?.detail?.error?.message || `API error (${response.status})`;
    throw new Error(message);
  }

  return response.json();
}

export const api = {
  getHealth: (): Promise<HealthResponse> => fetchApi<HealthResponse>('/health'),

  checkDeploy: (data: DeployCheckRequest): Promise<DeployCheckResponse> =>
    fetchApi<DeployCheckResponse>('/api/v1/deploys/check', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  recordOutcome: (checkId: string, data: DeployOutcomeRequest): Promise<DeployOutcomeResponse> =>
    fetchApi<DeployOutcomeResponse>(`/api/v1/deploys/${checkId}/outcome`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  createIncident: (data: CreateIncidentRequest): Promise<CreateIncidentResponse> =>
    fetchApi<CreateIncidentResponse>('/api/v1/incidents', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  logFixAttempt: (incidentId: string, data: LogFixAttemptRequest): Promise<LogFixAttemptResponse> =>
    fetchApi<LogFixAttemptResponse>(`/api/v1/incidents/${incidentId}/fix-attempts`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  resolveIncident: (incidentId: string, data: ResolveIncidentRequest): Promise<ResolveIncidentResponse> =>
    fetchApi<ResolveIncidentResponse>(`/api/v1/incidents/${incidentId}/resolve`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  searchMemory: (query: string): Promise<MemorySearchResponse> =>
    fetchApi<MemorySearchResponse>(`/api/v1/memory/search?q=${encodeURIComponent(query)}`),

  getAnalytics: (): Promise<AnalyticsResponse> =>
    fetchApi<AnalyticsResponse>('/api/v1/analytics/learning-curve'),

  generateApiKey: (name = 'default'): Promise<GenerateApiKeyResponse> =>
    fetchApi<GenerateApiKeyResponse>('/api/v1/keys', {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),

  replayDemo: (): Promise<DemoReplayResponse> =>
    fetchApi<DemoReplayResponse>('/api/v1/demo/replay', {
      method: 'POST',
    }),

  resetDemo: (): Promise<DemoResetResponse> =>
    fetchApi<DemoResetResponse>('/api/v1/demo/reset', {
      method: 'POST',
    }),
};
