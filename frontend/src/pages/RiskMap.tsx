import { useEffect, useState, useCallback } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline, useMapEvents } from 'react-leaflet';
import { useNavigate } from 'react-router-dom';
import {
  getStations, getRiskHeatmap, getRoads, getVillages, predictAtLocation, exportGeoJSON, exportCSV,
  Station, HeatmapPoint, Road, Village, PredictResult,
} from '../services/api';
import { t } from '../i18n/translations';
import {
  MapPin, Navigation, Building2,
  MousePointerClick, X, Loader2, AlertTriangle, AlertCircle, Download,
} from 'lucide-react';

const RISK_COLORS: Record<string, string> = {
  low: '#22c55e',
  moderate: '#f59e0b',
  high: '#f97316',
  very_high: '#ea580c',
  critical: '#ef4444',
};

const ROAD_COLORS: Record<string, string> = {
  open: '#22c55e',
  partially_blocked: '#f59e0b',
  blocked: '#ef4444',
};

const VILLAGE_COLORS: Record<string, string> = {
  safe: '#22c55e',
  low_risk: '#22c55e',
  medium_risk: '#f59e0b',
  high_risk: '#ef4444',
};

const NER_CENTER: [number, number] = [25.5, 92.5];

function MapClickHandler({ onMapClick }: { onMapClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

export default function RiskMap() {
  const navigate = useNavigate();
  const [stations, setStations] = useState<Station[]>([]);
  const [heatmap, setHeatmap] = useState<HeatmapPoint[]>([]);
  const [roads, setRoads] = useState<Road[]>([]);
  const [villages, setVillages] = useState<Village[]>([]);
  const [showRoads, setShowRoads] = useState(true);
  const [showVillages, setShowVillages] = useState(true);
  const [showStations, setShowStations] = useState(true);
  const [tileError, setTileError] = useState(false);

  // Click-to-predict state
  const [predictMode, setPredictMode] = useState(false);
  const [predictLoading, setPredictLoading] = useState(false);
  const [predictResult, setPredictResult] = useState<PredictResult | null>(null);
  const [predictError, setPredictError] = useState('');
  const [predictMarker, setPredictMarker] = useState<{ lat: number; lng: number } | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [stationsRes, heatRes, roadsRes, villagesRes] = await Promise.all([
          getStations(), getRiskHeatmap(), getRoads(), getVillages(),
        ]);
        setStations(stationsRes.data);
        setHeatmap(heatRes.data);
        setRoads(roadsRes.data);
        setVillages(villagesRes.data);
      } catch (e) {
        console.error('Map fetch error:', e);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleMapClick = useCallback(async (lat: number, lng: number) => {
    if (!predictMode) return;
    setPredictMarker({ lat, lng });
    setPredictLoading(true);
    setPredictError('');
    setPredictResult(null);
    try {
      const res = await predictAtLocation({ latitude: lat, longitude: lng });
      setPredictResult(res.data);
    } catch (e: any) {
      setPredictError('Prediction failed. Please try again.');
    } finally {
      setPredictLoading(false);
    }
  }, [predictMode]);

  const getRiskRadius = (score: number) => Math.max(6, score / 5);

  const saveDownload = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  const handleGeoJSONExport = async () => {
    try {
      const response = await exportGeoJSON();
      saveDownload(
        new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/geo+json' }),
        'geoshield-risk-data.geojson',
      );
    } catch {
      setPredictError('GeoJSON export failed.');
    }
  };

  const handleCSVExport = async () => {
    try {
      const response = await exportCSV();
      saveDownload(response.data, 'geoshield-risk-data.csv');
    } catch {
      setPredictError('CSV export failed.');
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Map Controls */}
      <div className="p-4 border-b border-dark-700 bg-dark-900/50">
        <div className="flex items-center gap-4 flex-wrap">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <MapPin className="w-5 h-5 text-green-400" />
            {t('map')}
          </h2>
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => { setPredictMode(!predictMode); setPredictResult(null); setPredictMarker(null); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1 ${
                predictMode
                  ? 'bg-purple-600/30 text-purple-300 border border-purple-500/50 shadow-lg shadow-purple-600/20'
                  : 'bg-dark-800 text-dark-400 border border-dark-700 hover:text-white'
              }`}
            >
              <MousePointerClick className="w-3 h-3" />
              {predictMode ? 'Predicting...' : (t('predictOnMap') || 'Click to Predict')}
            </button>

            <button
              onClick={() => setShowStations(!showStations)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                showStations ? 'bg-green-600/20 text-green-400 border border-green-600/30' : 'bg-dark-800 text-dark-400 border border-dark-700'
              }`}
            >
              <Navigation className="w-3 h-3 inline mr-1" />
              Stations ({stations.length})
            </button>
            <button
              onClick={() => setShowRoads(!showRoads)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                showRoads ? 'bg-blue-600/20 text-blue-400 border border-blue-600/30' : 'bg-dark-800 text-dark-400 border border-dark-700'
              }`}
            >
              🛣️ Roads
            </button>
            <button
              onClick={handleGeoJSONExport}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-dark-800 text-cyan-300 border border-dark-700 hover:border-cyan-600/50 transition-all flex items-center gap-1"
              title="Export all station risk data as GeoJSON"
            >
              <Download className="w-3 h-3" /> GeoJSON
            </button>
            <button
              onClick={handleCSVExport}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-dark-800 text-emerald-300 border border-dark-700 hover:border-emerald-600/50 transition-all flex items-center gap-1"
              title="Export all station risk data as CSV"
            >
              <Download className="w-3 h-3" /> CSV
            </button>

            <button
              onClick={() => setShowVillages(!showVillages)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                showVillages ? 'bg-purple-600/20 text-purple-400 border border-purple-600/30' : 'bg-dark-800 text-dark-400 border border-dark-700'
              }`}
            >
              <Building2 className="w-3 h-3 inline mr-1" />
              Villages
            </button>
          </div>
        </div>
        {predictMode && (
          <div className="mt-2 text-xs text-purple-300 bg-purple-600/10 border border-purple-600/20 rounded-lg px-3 py-2">
            🖱️ Click anywhere on the map to get AI risk prediction with RF+GB ensemble model and real NER terrain data
          </div>
        )}
      </div>

      {/* Map */}
      <div className="flex-1 relative" style={{ minHeight: '500px' }}>
        <MapContainer
          center={NER_CENTER}
          zoom={7}
          className="h-full w-full"
          style={{ background: '#1e293b' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            className="dark-tiles"
            eventHandlers={{ tileerror: () => setTileError(true) }}
          />
          <MapClickHandler onMapClick={handleMapClick} />

          {showStations && heatmap.map((point, i) => (
            <CircleMarker
              key={`heat-${i}`}
              center={[point.lat, point.lng]}
              radius={getRiskRadius(point.risk_score)}
              fillColor={RISK_COLORS[point.risk_level] || '#22c55e'}
              color={RISK_COLORS[point.risk_level] || '#22c55e'}
              weight={2}
              opacity={0.8}
              fillOpacity={0.4}
            >
              <Popup>
                <div className="text-sm">
                  <p className="font-bold">{point.station_name}</p>
                  <p className="text-gray-500">{point.state} • {point.district}</p>
                  <p className={`font-bold mt-1 ${
                    point.risk_level === 'critical' ? 'text-red-600' :
                    point.risk_level === 'very_high' ? 'text-orange-600' :
                    point.risk_level === 'high' ? 'text-orange-500' :
                    point.risk_level === 'moderate' ? 'text-yellow-600' : 'text-green-600'
                  }`}>
                    Risk: {point.risk_score}/100 ({(point.risk_level || '').toUpperCase().replace('_', ' ')})
                  </p>
                  <button
                    onClick={() => navigate(`/station/${point.station_id}`)}
                    className="mt-2 text-xs text-blue-600 hover:underline"
                  >
                    View Details →
                  </button>
                </div>
              </Popup>
            </CircleMarker>
          ))}

          {predictMarker && (
            <CircleMarker
              center={[predictMarker.lat, predictMarker.lng]}
              radius={10}
              fillColor="#a855f7"
              color="#a855f7"
              weight={3}
              opacity={1}
              fillOpacity={0.6}
            >
              <Popup>
                <div className="text-sm">
                  <p className="font-bold text-purple-600">🎯 AI Prediction Point</p>
                  <p className="text-gray-500">{predictMarker.lat.toFixed(4)}°N, {predictMarker.lng.toFixed(4)}°E</p>
                </div>
              </Popup>
            </CircleMarker>
          )}

          {showRoads && roads.map((road, i) => (
            <Polyline
              key={`road-${i}`}
              positions={[[road.start_lat, road.start_lng], [road.end_lat, road.end_lng]]}
              color={ROAD_COLORS[road.status] || '#64748b'}
              weight={road.road_type === 'national_highway' ? 3 : 2}
              dashArray={road.status === 'blocked' ? '5,10' : undefined}
            >
              <Popup>
                <div className="text-sm">
                  <p className="font-bold">{road.road_name}</p>
                  <p className="text-gray-500">{road.road_type.replace('_', ' ')}</p>
                  <p className={`font-bold mt-1 ${
                    road.status === 'blocked' ? 'text-red-600' :
                    road.status === 'partially_blocked' ? 'text-yellow-600' : 'text-green-600'
                  }`}>
                    Status: {road.status.replace('_', ' ').toUpperCase()}
                  </p>
                  {road.blockage_reason && <p className="text-xs text-gray-500 mt-1">{road.blockage_reason}</p>}
                </div>
              </Popup>
            </Polyline>
          ))}

          {showVillages && villages.map((village, i) => (
            <CircleMarker
              key={`village-${i}`}
              center={[village.latitude, village.longitude]}
              radius={Math.max(4, Math.min(10, village.population / 50000))}
              fillColor={VILLAGE_COLORS[village.risk_zone] || '#64748b'}
              color="#ffffff"
              weight={1}
              opacity={0.6}
              fillOpacity={0.6}
            >
              <Popup>
                <div className="text-sm">
                  <p className="font-bold">{village.name}</p>
                  <p className="text-gray-500">{village.state} • {village.district}</p>
                  <p className="mt-1">👥 Population: {village.population.toLocaleString()}</p>
                  <p className={`font-bold ${
                    village.risk_zone.includes('high') ? 'text-red-600' :
                    village.risk_zone.includes('medium') ? 'text-yellow-600' : 'text-green-600'
                  }`}>
                    Zone: {village.risk_zone.replace('_', ' ').toUpperCase()}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">🏥 {village.nearest_hospital_km}km | 🚔 {village.nearest_police_km}km</p>
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>

        {tileError && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-amber-600/90 text-white text-xs px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
            ⚠️ Map tiles failed to load
            <button onClick={() => setTileError(false)} className="ml-2 underline">Dismiss</button>
          </div>
        )}

        {/* Click-to-Predict Result Panel */}
        {predictMode && (predictLoading || predictResult || predictError) && (
          <div className="absolute top-4 right-4 z-[1000] w-72 sm:w-80 glass rounded-xl border border-purple-600/30 shadow-2xl overflow-hidden">
            <div className="bg-purple-600/20 px-4 py-3 flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <MousePointerClick className="w-4 h-4 text-purple-400" />
                AI Risk Prediction
              </h3>
              <button onClick={() => { setPredictResult(null); setPredictMarker(null); }} className="text-dark-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-4">
              {predictLoading && (
                <div className="flex items-center gap-3 py-4">
                  <Loader2 className="w-5 h-5 text-purple-400 animate-spin" />
                  <span className="text-sm text-dark-300">Analyzing terrain & weather data...</span>
                </div>
              )}
              {predictError && (
                <div className="flex items-center gap-2 py-2 text-red-400 text-sm">
                  <AlertCircle className="w-4 h-4" /> {predictError}
                </div>
              )}
              {predictResult && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-dark-400">Risk Score</span>
                    <span className={`text-lg font-bold ${
                      predictResult.risk_assessment.risk_level === 'critical' ? 'text-red-400' :
                      predictResult.risk_assessment.risk_level === 'very_high' ? 'text-red-300' :
                      predictResult.risk_assessment.risk_level === 'high' ? 'text-orange-400' :
                      predictResult.risk_assessment.risk_level === 'moderate' ? 'text-amber-400' : 'text-green-400'
                    }`}>
                      {predictResult.risk_assessment.risk_score}/100
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-dark-400">Risk Level</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                      predictResult.risk_assessment.risk_level === 'critical' ? 'bg-red-600/20 text-red-400' :
                      predictResult.risk_assessment.risk_level === 'very_high' ? 'bg-red-500/20 text-red-300' :
                      predictResult.risk_assessment.risk_level === 'high' ? 'bg-orange-600/20 text-orange-400' :
                      predictResult.risk_assessment.risk_level === 'moderate' ? 'bg-amber-600/20 text-amber-400' : 'bg-green-600/20 text-green-400'
                    }`}>
                      {(predictResult.risk_assessment.risk_level || '').toUpperCase().replace('_', ' ')}
                    </span>
                  </div>
                  {predictResult.nearest_station && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-dark-400">Nearest Station</span>
                      <span className="text-xs text-white">{predictResult.nearest_station.name} ({predictResult.nearest_station.distance_km}km)</span>
                    </div>
                  )}
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-dark-400">Probability</span>
                    <span className="text-xs text-white">{((predictResult.risk_assessment.landslide_probability || 0) * 100).toFixed(1)}%</span>
                  </div>
                  {predictResult.risk_assessment.contributing_factors && predictResult.risk_assessment.contributing_factors.length > 0 && (
                    <div>
                      <span className="text-xs text-dark-400 block mb-1">Contributing Factors:</span>
                      {predictResult.risk_assessment.contributing_factors.map((f: string, i: number) => (
                        <div key={i} className="text-xs text-amber-300 flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3" /> {f}
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="pt-2 border-t border-dark-700">
                    <p className="text-xs text-dark-300 leading-relaxed">{predictResult.risk_assessment.recommendation}</p>
                  </div>
                  {/* Terrain Data from nearest-neighbor lookup */}
                  {(predictResult.risk_assessment as any).terrain_data && (
                    <div className="pt-2 border-t border-dark-700">
                      <p className="text-[10px] text-dark-500 font-semibold mb-1">TERRAIN DATA (Real NER)</p>
                      <div className="grid grid-cols-2 gap-1">
                        <span className="text-[10px] text-dark-400">Slope: {(predictResult.risk_assessment as any).terrain_data.slope}°</span>
                        <span className="text-[10px] text-dark-400">Elev: {(predictResult.risk_assessment as any).terrain_data.elevation}m</span>
                        <span className="text-[10px] text-dark-400">NDVI: {(predictResult.risk_assessment as any).terrain_data.ndvi}</span>
                        <span className="text-[10px] text-dark-400">Soil: {(predictResult.risk_assessment as any).terrain_data.soil_moisture}</span>
                      </div>
                      <p className="text-[9px] text-green-400 mt-1">Source: {(predictResult.risk_assessment as any).terrain_data.source}</p>
                    </div>
                  )}
                  {/* Feature Importance */}
                  {(predictResult.risk_assessment as any).feature_importance && (
                    <div className="pt-2 border-t border-dark-700">
                      <p className="text-[10px] text-dark-500 font-semibold mb-1">WHY THIS SCORE?</p>
                      {Object.entries((predictResult.risk_assessment as any).feature_importance).slice(0, 5).map(([feat, imp]: [string, any]) => (
                        <div key={feat} className="flex items-center gap-2 mb-0.5">
                          <span className="text-[10px] text-dark-400 w-20 truncate">{feat.replace(/_/g, ' ')}</span>
                          <div className="flex-1 h-1.5 bg-dark-800 rounded-full overflow-hidden">
                            <div className="h-full bg-purple-500 rounded-full" style={{ width: `${imp}%` }} />
                          </div>
                          <span className="text-[10px] text-purple-400 w-8 text-right">{imp}%</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="pt-1">
                    <p className="text-[10px] text-dark-500">Model: {predictResult.model_info?.type || 'RF+GB VotingClassifier'} | Features: {predictResult.model_info?.features || 9}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="absolute bottom-4 left-4 z-[1000] glass rounded-xl p-3">
          <p className="text-xs font-semibold text-white mb-2">Risk Level</p>
          <div className="space-y-1">
            {[
              { level: t('lowLevel'), color: RISK_COLORS.low },
              { level: t('moderateLevel'), color: RISK_COLORS.moderate },
              { level: t('highLevel'), color: RISK_COLORS.high },
              { level: 'Very High', color: RISK_COLORS.very_high },
              { level: t('criticalLevel'), color: RISK_COLORS.critical },
            ].map(({ level, color }) => (
              <div key={level} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-xs text-dark-300">{level}</span>
              </div>
            ))}
          </div>
          <div className="mt-2 pt-2 border-t border-dark-700">
            <p className="text-xs font-semibold text-white mb-1">Roads</p>
            <div className="space-y-1">
              {[
                { label: 'Open', color: ROAD_COLORS.open },
                { label: 'Partially Blocked', color: ROAD_COLORS.partially_blocked },
                { label: 'Blocked', color: ROAD_COLORS.blocked },
              ].map(({ label, color }) => (
                <div key={label} className="flex items-center gap-2">
                  <div className="w-4 h-0.5" style={{ backgroundColor: color }} />
                  <span className="text-xs text-dark-300">{label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
