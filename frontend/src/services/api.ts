import axios from 'axios';
import { getCurrentLanguage } from '../i18n/translations';

// Detect if running in Electron desktop app
const isElectron = () => {
  try {
    return typeof window !== 'undefined' && (
      (window as any).navigator?.userAgent?.includes('Electron') ||
      typeof (window as any).require !== 'undefined'
    );
  } catch { return false; }
};

// Detect if running in mobile app (Capacitor/Cordova or file:// protocol)
const isMobile = () => {
  try {
    if (typeof window === 'undefined') return false;
    return typeof (window as any).Capacitor !== 'undefined' ||
           typeof (window as any).cordova !== 'undefined' ||
           /file:\/\//.test(window.location.href);
  } catch { return false; }
};

// For Electron/mobile: use localhost (backend runs locally)
// For web: use relative URL (same origin)
export const normalizeServerBase = (input: string): string => {
  let raw = input.trim().replace(/\/+$/, '');
  if (!raw) return '';

  if (!/^https?:\/\//i.test(raw)) {
    // Host/IP without a scheme is treated as a local HTTP backend.
    // Add port 8000 only when the user did not provide one.
    if (!raw.includes(':')) raw += ':8000';
    raw = `http://${raw}`;
  }

  try {
    return new URL(raw).origin;
  } catch {
    return raw;
  }
};

const getApiBase = () => {
  if (isElectron() || isMobile()) {
    const savedUrl = localStorage.getItem('geoshield_server_url');
    if (savedUrl) {
      const base = normalizeServerBase(savedUrl);
      if (base) return `${base}/api`;
    }
    return 'http://localhost:8000/api';
  }
  return '/api';
};

const api = axios.create({
  timeout: 20000,
});

// Dynamically set baseURL on every request so saved server URL changes
// take effect without requiring a full page reload.
api.interceptors.request.use((config) => {
  config.baseURL = getApiBase();
  return config;
});

// Allow mobile app to change server URL
export const setServerUrl = (url: string) => {
  const normalized = normalizeServerBase(url);
  if (normalized) {
    localStorage.setItem('geoshield_server_url', normalized);
  } else {
    localStorage.removeItem('geoshield_server_url');
  }
  window.location.reload();
};

export const getServerUrl = () => {
  return localStorage.getItem('geoshield_server_url') || '';
};

export const getAlertWebSocketUrl = (district: string = 'all') => {
  let serverBase = '';

  if (isElectron() || isMobile()) {
    const savedUrl = localStorage.getItem('geoshield_server_url');
    serverBase = savedUrl ? normalizeServerBase(savedUrl) : 'http://localhost:8000';
  } else if (typeof window !== 'undefined') {
    serverBase = window.location.origin;
  }

  const url = new URL(serverBase || 'http://localhost:8000');
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  url.pathname = `/ws/alerts/${encodeURIComponent(district || 'all')}`;
  url.search = '';

  const token = getStoredToken();
  if (token) {
    url.searchParams.set('token', token);
  }
  return url.toString();
};

export const isMobileApp = isMobile;

// --- JWT token management ---
const TOKEN_KEY = 'geoshield_token';

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// Attach JWT token to every request automatically
api.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, clear token so user is logged out
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const requestUrl = String(error.config?.url || '');
      // Invalid login should stay on the login screen so the user sees the
      // backend error instead of getting an unexpected full-page reload.
      if (!requestUrl.includes('/auth/login')) {
        clearStoredToken();
        window.location.reload();
      }
    }
    return Promise.reject(error);
  }
);

// --- Interfaces ---
export interface Station {
  id: number;
  station_id: string;
  name: string;
  latitude: number;
  longitude: number;
  state: string;
  district: string;
  village: string;
  elevation: number;
  slope_angle: number;
  soil_type: string;
  vegetation_cover: number;
  is_active: boolean;
  latest_reading: {
    rainfall_mm: number;
    soil_moisture: number;
    ground_displacement: number;
    timestamp: string;
    source?: string | null;
    external_id?: string | null;
  } | null;
  risk: {
    level: string;
    score: number;
    probability: number;
  } | null;
}

export interface DashboardStats {
  total_stations: number;
  active_stations: number;
  risk_distribution: { low: number; moderate: number; high: number; critical: number };
  active_alerts: number;
  pending_reports: number;
  recent_reports_24h: number;
  road_status: { open: number; partially_blocked: number; blocked: number };
  affected_population: number;
  total_villages: number;
  high_risk_villages: number;
  average_risk_score: number;
  last_updated: string;
}

export interface Alert {
  id: number;
  station_id: string;
  risk_level: string;
  title: string;
  message: string;
  status: string;
  affected_population: number;
  latitude: number;
  longitude: number;
  created_at: string;
}

export interface HeatmapPoint {
  lat: number;
  lng: number;
  risk_score: number;
  risk_level: string;
  station_name: string;
  station_id: string;
  state: string;
  district: string;
}

export interface Road {
  id: number;
  road_name: string;
  road_type: string;
  start_lat: number;
  start_lng: number;
  end_lat: number;
  end_lng: number;
  status: string;
  blockage_reason: string | null;
  alternative_route: string | null;
}

export interface Village {
  id: number;
  name: string;
  state: string;
  district: string;
  latitude: number;
  longitude: number;
  population: number;
  risk_zone: string;
  nearest_hospital_km: number;
  nearest_police_km: number;
}

export interface Report {
  id: number;
  report_type: string;
  description: string;
  latitude: number;
  longitude: number;
  reporter_name: string | null;
  submitted_by?: string | null;
  status: string;
  attachment_filename?: string | null;
  created_at: string;
}

export interface WeatherData {
  temperature: number;
  humidity: number;
  rainfall_1h: number;
  rainfall_24h: number;
  rainfall_7d: number;
  wind_speed: number;
  wind_direction: number;
  pressure: number;
  visibility: number;
  forecast_rainfall_24h: number;
  forecast_rainfall_48h: number;
  timestamp: string;
}

export interface DataSourceMetadata {
  mode: 'live' | 'cached' | 'fallback' | 'unavailable';
  provider: string;
  observed_at: string | null;
  served_at: string;
  age_seconds: number | null;
  max_age_seconds: number;
  is_stale: boolean;
  fallback_reason: string | null;
  detail: string;
}

export interface WeatherResponse {
  station_id: string;
  data: WeatherData | null;
  source: DataSourceMetadata;
}

export interface WeatherForecastPoint {
  timestamp: string;
  temperature: number;
  rainfall_1h: number;
  forecast_rainfall_24h?: number;
  humidity: number;
}

export interface WeatherForecastResponse {
  station_id: string;
  hours: number;
  series_kind: 'forecast' | 'demo_history';
  forecast: WeatherForecastPoint[];
  source: DataSourceMetadata;
}

export interface PredictResult {
  location: { latitude: number; longitude: number };
  nearest_station: { station_id: string; name: string; distance_km: number } | null;
  risk_assessment: {
    risk_score: number;
    risk_level: string;
    landslide_probability: number;
    contributing_factors: string[];
    predicted_time_window_hours: number;
    recommendation: string;
    probabilities: Record<string, number>;
  };
  model_info: {
    type: string;
    training_samples: number;
    training_source: string;
    features: number;
    terrain_enriched: boolean;
  };
  timestamp: string;
}

export interface TimelineEntry {
  timestamp: string;
  alerts: { id: number; station_id: string; risk_level: string; title: string; status: string; affected_population: number; created_at: string }[];
  total_affected: number;
  max_risk: string;
}

// --- Auth ---
export const loginAPI = (email: string, password: string) => {
  const params = new URLSearchParams();
  params.append('email', email);
  params.append('password', password);
  return api.post<{ token: string; user: { email: string; name: string; role: string } }>('/auth/login', params);
};

// --- Dashboard ---
export const getDashboardStats = () => api.get<DashboardStats>('/dashboard/stats');
export const getRiskHeatmap = () => api.get<HeatmapPoint[]>('/dashboard/risk-heatmap');
export const getRainfallTrend = () => api.get<{ timestamp: string; avg_rainfall: number }[]>('/dashboard/rainfall-trend');
export const getRiskTrend = () => api.get<{ timestamp: string; avg_risk: number }[]>('/dashboard/risk-trend');
export const getStateSummary = () => api.get<{ state: string; stations: number; avg_risk_score: number; critical_count: number }[]>('/dashboard/state-summary');

export interface ReadinessResponse {
  status: string;
  database: string;
  ml_training_data: string;
  synthetic_model_fallback: boolean;
  environment: string;
  timestamp: string;
}
export const getReadiness = () => api.get<ReadinessResponse>('/health/ready');

export interface UserAccount {
  id: number;
  email: string;
  name: string;
  role: 'admin' | 'field_officer' | 'district_admin' | 'citizen';
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
  last_login_at: string | null;
}

export const getUsers = () => api.get<UserAccount[]>('/users');
export const createUser = (data: { email: string; name: string; password: string; role: UserAccount['role'] }) =>
  api.post<UserAccount>('/users', data);
export const setUserStatus = (id: number, isActive: boolean) =>
  api.put<UserAccount>(`/users/${id}/status`, { is_active: isActive });
export const resetUserPassword = (id: number, password: string) =>
  api.put(`/users/${id}/password`, { password });

// --- Sensors ---
export const getStations = () => api.get<Station[]>('/sensors/stations');
export const getManagedStations = () => api.get<ManagedStation[]>('/sensors/stations/manage');
export const getStation = (id: string) => api.get(`/sensors/stations/${id}`);
export const getStationHistory = (id: string, hours = 24) => api.get(`/sensors/stations/${id}/history?hours=${hours}`);
export const getAllLatestReadings = () =>
  api.get<{ station_id: string; rainfall_mm: number; soil_moisture: number; ground_displacement: number; timestamp: string }[]>('/sensors/readings/latest');

export interface StationCreatePayload {
  station_id: string;
  name: string;
  latitude: number;
  longitude: number;
  state: string;
  district: string;
  village?: string;
  elevation?: number;
  slope_angle?: number;
  soil_type?: string;
  vegetation_cover?: number;
}

export interface ManagedStation extends StationCreatePayload {
  id: number;
  is_active: boolean;
}

export const createStation = (data: StationCreatePayload) =>
  api.post('/sensors/stations', data);

export const updateStation = (stationId: string, data: Partial<StationCreatePayload> & { is_active?: boolean }) =>
  api.put(`/sensors/stations/${stationId}`, data);


// --- Alerts ---
export const getAlerts = (params?: { status?: string; risk_level?: string }) =>
  api.get<Alert[]>('/alerts', { params: { ...params, lang: getCurrentLanguage() } });
export const getActiveAlerts = () => api.get<Alert[]>('/alerts/active');
export const getAlertStats = () => api.get<{ total: number; active: number; acknowledged: number; resolved: number; critical_active: number; high_active: number }>('/alerts/stats');
export const acknowledgeAlert = (id: number) => api.put(`/alerts/${id}/acknowledge`);
export const resolveAlert = (id: number) => api.put(`/alerts/${id}/resolve`);
export const getAlertTimeline = (hours: number = 72, riskLevel?: string) =>
  api.get<{ timeline: TimelineEntry[]; summary: { total_alerts: number; total_hours: number; critical_count: number; high_count: number; moderate_count: number; low_count: number; total_affected_population: number } }>('/alerts/timeline', { params: { hours, risk_level: riskLevel } });
export const getAlertHistory = (days: number = 30) =>
  api.get<{ date: string; critical: number; high: number; moderate: number; low: number; total: number }[]>('/alerts/history', { params: { days } });

// --- Reports ---
export const getReports = (params?: { status?: string }) => api.get<Report[]>('/reports', { params });
export const submitReport = (formData: FormData) => api.post('/reports', formData);
export const verifyReport = (id: number) => api.put(`/reports/${id}/verify`);
export const dismissReport = (id: number) => api.put(`/reports/${id}/dismiss`);
export const getReportAttachment = (id: number) =>
  api.get<Blob>(`/reports/${id}/attachment`, { responseType: 'blob' });

// --- Roads & Villages ---
export const getRoads = () => api.get<Road[]>('/roads');
export const getVillages = (riskZone?: string) => api.get<Village[]>('/villages', { params: riskZone ? { risk_zone: riskZone } : {} });

// --- Weather ---
export const getWeather = (stationId: string) => api.get<WeatherResponse>(`/weather/${stationId}`);
export const getWeatherForecast = (stationId: string, hours = 48) =>
  api.get<WeatherForecastResponse>(`/weather/${stationId}/forecast?hours=${hours}`);

// --- Simulator ---
export interface SimulationResult {
  status: string;
  simulation: {
    station: { id: string; name: string; state: string; district: string };
    intensity: string;
    sensor_reading: { rainfall_mm: number; soil_moisture: number; ground_displacement: number; pore_pressure: number };
  };
  risk_assessment: {
    risk_score: number;
    risk_level: string;
    landslide_probability: number;
    contributing_factors: string[];
    time_window_hours: number;
    recommendation: string;
  };
  alert: { id: number; title: string; affected_population: number } | null;
}
export const simulateLandslide = (data: { station_id?: string; intensity?: string }) =>
  api.post<SimulationResult>('/simulate/landslide', data);
export const simulateBatch = (count: number = 5) => api.post(`/simulate/batch?count=${count}`);
export const resetSimulation = () => api.post('/simulate/reset');

// --- Predict (Click-to-Predict on Map) ---
export const predictAtLocation = (data: {
  latitude: number; longitude: number;
  slope?: number; elevation?: number;
  rainfall_mm?: number; soil_moisture?: number; ndvi?: number;
}) => api.post<PredictResult>('/predict', data);

// --- Export ---
export const exportGeoJSON = () => api.get('/export/geojson');
export const exportCSV = () => api.get('/export/csv', { responseType: 'blob' });
export const exportRiskZones = () => api.get('/export/risk-zones');

// --- Satellite ---
export interface SatelliteStation {
  id: string; name: string; state: string;
  real_elevation: number;
  real_soil_moisture_0_7cm: number; real_soil_moisture_7_28cm: number;
  real_soil_moisture_28_100cm: number; real_soil_temperature: number;
  real_rainfall_current: number; real_rainfall_24h: number; real_rainfall_7d: number;
  real_temperature: number; real_humidity: number; real_wind_speed: number;
  estimated_ndvi: number;
}
export interface SatelliteSummary {
  total_stations: number;
  elevation: { min: number; max: number; avg: number; unit: string };
  soil_moisture_surface: { min: number; max: number; avg: number; unit: string };
  rainfall_24h: { min: number; max: number; avg: number; total: number; unit: string };
  rainfall_7d: { min: number; max: number; avg: number; total: number; unit: string };
  ndvi: { min: number; max: number; avg: number; description: string };
  temperature: { min: number; max: number; avg: number; unit: string };
  humidity: { min: number; max: number; avg: number; unit: string };
  source: DataSourceMetadata;
}
export interface SatelliteRiskZone {
  station_id: string; name: string; state: string; lat: number; lng: number;
  satellite_risk_score: number; risk_level: string;
  factors: { elevation_risk: number; soil_moisture_risk: number; rainfall_risk: number; vegetation_risk: number };
  snapshot_data: { elevation: number; soil_moisture: number; rainfall_24h: number; ndvi: number };
}
export const getSatelliteData = () => api.get<{ stations: SatelliteStation[]; total_stations: number; source: DataSourceMetadata }>('/satellite/data');
export const getStationSatelliteData = (id: string) => api.get<{ station: SatelliteStation; source: DataSourceMetadata }>(`/satellite/data/${id}`);
export const getSatelliteSummary = () => api.get<SatelliteSummary>('/satellite/summary');
export const getSatelliteRiskZones = () => api.get<{ risk_zones: SatelliteRiskZone[]; source: DataSourceMetadata }>('/satellite/risk-zones');

// --- Flood Data ---
export interface FloodDistrict {
  district: string;
  annual_flood_days: number;
  historical_events: number;
  flood_risk_score: number;
  river_systems: string[];
}
export interface FloodSummary {
  total_districts: number;
  avg_risk_score: number;
  max_risk_district: string;
  max_risk_score: number;
  total_historical_events: number;
  avg_annual_flood_days: number;
  high_risk_districts: number;
  data_source: string;
}
export interface FloodLandslideCorrelation {
  district: string;
  flood_risk: number;
  landslide_risk: number;
  compound_risk: number;
  river_systems: string[];
  has_landslide_data: boolean;
}
export const getFloodData = (minRisk?: number) =>
  api.get<{ data: FloodDistrict[]; total_districts: number }>('/flood/data', { params: minRisk ? { min_risk: minRisk } : {} });
export const getFloodSummary = () => api.get<FloodSummary>('/flood/summary');
export const getFloodCorrelation = () =>
  api.get<{ correlation: FloodLandslideCorrelation[]; insight: string }>('/flood/correlation');

// --- ML Enhanced (XGBoost + Terrain Lookup) ---
export interface MLPredictionResult {
  risk_score: number;
  risk_level: string;
  confidence: number;
  source: string;
  factors: { rainfall_risk: string; slope_risk: string; vegetation_risk: string };
  feature_importance: Record<string, number> | null;
  terrain_data: { slope: number; elevation: number; ndvi: number; soil_moisture: number; distance_to_road: number; source: string };
  latitude: number;
  longitude: number;
}
export interface MLHealth {
  status: string;
  model_loaded: boolean;
  model_type: string;
  terrain_lookup: boolean;
  version: string;
  training_source: string;
  training_samples: number;
  training_enabled: boolean;
}
export interface MLDistrictRisk {
  district: string;
  risk_level: string;
  risk_score: number;
  zone_count: number;
  critical_count: number;
  high_count: number;
  predictions: MLPredictionResult[];
}
export interface MLRiskGrid {
  grid: { lat: number; lng: number; risk_score: number; risk_level: string }[];
  bounds: { lat_min: number; lat_max: number; lon_min: number; lon_max: number };
  resolution: number;
  count: number;
}
export const getMLHealth = () => api.get<MLHealth>('/ml/health');
export const mlPredict = (data: { latitude: number; longitude: number; slope?: number; elevation?: number; rainfall_24hr?: number; soil_moisture?: number; ndvi?: number }) =>
  api.post<MLPredictionResult>('/ml/predict', data);
export const mlBatchPredict = (locations: { latitude: number; longitude: number }[]) =>
  api.post<{ predictions: MLPredictionResult[]; count: number }>('/ml/predict/batch', { locations });
export const getMLRiskGrid = (resolution: number = 10) =>
  api.get<MLRiskGrid>('/ml/risk/grid', { params: { resolution } });
export const getMLDistrictRisk = (district: string) =>
  api.get<MLDistrictRisk>(`/ml/risk/district/${district}`);
export const trainMLModel = () => api.post<{ message: string; details: any }>('/ml/train');

export default api;
export { api };
