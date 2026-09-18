import { useEffect, useState } from 'react';
import { getSatelliteSummary, getSatelliteData, getSatelliteRiskZones, SatelliteSummary, SatelliteStation, SatelliteRiskZone, DataSourceMetadata } from '../services/api';
import DataSourceBadge from '../components/DataSourceBadge';
import { t } from '../i18n/translations';
import {
  Satellite, Mountain, Droplets, Leaf, Thermometer, Wind,
  CloudRain, TrendingUp, MapPin, RefreshCw, AlertTriangle,
} from 'lucide-react';

const RISK_COLORS: Record<string, string> = {
  low: '#22c55e',
  moderate: '#f59e0b',
  high: '#f97316',
  critical: '#ef4444',
};

export default function SatelliteData() {
  const [summary, setSummary] = useState<SatelliteSummary | null>(null);
  const [stations, setStations] = useState<SatelliteStation[]>([]);
  const [riskZones, setRiskZones] = useState<SatelliteRiskZone[]>([]);
  const [source, setSource] = useState<DataSourceMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'summary' | 'stations' | 'risk-zones'>('summary');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [summaryRes, stationsRes, riskZonesRes] = await Promise.all([
        getSatelliteSummary(),
        getSatelliteData(),
        getSatelliteRiskZones(),
      ]);
      setSummary(summaryRes.data);
      setStations(stationsRes.data.stations);
      setRiskZones(riskZonesRes.data.risk_zones);
      setSource(summaryRes.data.source || stationsRes.data.source);
    } catch (e) {
      console.error('Satellite data fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-dark-400 text-sm">Loading satellite-derived snapshot...</p>
          <p className="text-dark-500 text-xs mt-1">Checking provenance and freshness</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Satellite className="w-6 h-6 text-blue-400" />
            Satellite-Derived Data Snapshot
          </h1>
          <p className="text-dark-400 text-sm mt-1">
            Cached regional values with explicit source age and fallback status
          </p>
        </div>
        <button
          onClick={fetchData}
          className="px-3 py-2 rounded-xl bg-dark-800 border border-dark-700 text-dark-400 hover:text-white hover:border-blue-600/30 transition-all flex items-center gap-2 text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          {t('refresh')}
        </button>
      </div>

      {/* Data Source Badge */}
      <DataSourceBadge source={source} />

      {/* Tab Switcher */}
      <div className="flex bg-dark-800 rounded-xl p-1 border border-dark-700">
        {(['summary', 'stations', 'risk-zones'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === tab
                ? 'bg-green-600/20 text-green-400 border border-green-600/30'
                : 'text-dark-400 hover:text-white border border-transparent'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1).replace('-', ' ')}
          </button>
        ))}
      </div>

      {/* Summary Cards */}
      {activeTab === 'summary' && summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass rounded-xl p-4">
            <Mountain className="w-6 h-6 text-blue-400 mb-2" />
            <p className="text-xs text-dark-400">{t('elevationRange')}</p>
            <p className="text-xl font-bold text-white">{summary.elevation.min} - {summary.elevation.max}</p>
            <p className="text-xs text-dark-500">{t('avgLabel')}: {summary.elevation.avg}m</p>
          </div>
          <div className="glass rounded-xl p-4">
            <Droplets className="w-6 h-6 text-emerald-400 mb-2" />
            <p className="text-xs text-dark-400">{t('soilMoistureSurface')}</p>
            <p className="text-xl font-bold text-white">{summary.soil_moisture_surface.avg}</p>
            <p className="text-xs text-dark-500">{t('avgAcrossNERLabel')}</p>
          </div>
          <div className="glass rounded-xl p-4">
            <CloudRain className="w-6 h-6 text-cyan-400 mb-2" />
            <p className="text-xs text-dark-400">{t('rainfall24hTotal')}</p>
            <p className="text-xl font-bold text-white">{summary.rainfall_24h.total}</p>
            <p className="text-xs text-dark-500">{t('mmAcrossStations').replace('{n}', String(summary.total_stations))}</p>
          </div>
          <div className="glass rounded-xl p-4">
            <Leaf className="w-6 h-6 text-green-400 mb-2" />
            <p className="text-xs text-dark-400">{t('avgNdvi')}</p>
            <p className="text-xl font-bold text-white">{summary.ndvi.avg}</p>
            <p className="text-xs text-dark-500">{t('vegIndexLabel')}</p>
          </div>
        </div>
      )}

      {/* Additional Stats */}
      {activeTab === 'summary' && summary && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="glass rounded-xl p-4">
            <CloudRain className="w-5 h-5 text-blue-400 mb-2" />
            <p className="text-xs text-dark-400">{t('rainfall7Days')}</p>
            <p className="text-lg font-bold text-white">{summary.rainfall_7d.total} {t('mmTotal')}</p>
            <p className="text-xs text-dark-500">{t('maxRainfallOneStation').replace('{n}', String(summary.rainfall_7d.max))}</p>
          </div>
          <div className="glass rounded-xl p-4">
            <Thermometer className="w-5 h-5 text-red-400 mb-2" />
            <p className="text-xs text-dark-400">{t('temperatureLabel')}</p>
            <p className="text-lg font-bold text-white">{summary.temperature.min}°C - {summary.temperature.max}°C</p>
            <p className="text-xs text-dark-500">{t('avgLabel')}: {summary.temperature.avg}°C</p>
          </div>
          <div className="glass rounded-xl p-4">
            <Wind className="w-5 h-5 text-cyan-400 mb-2" />
            <p className="text-xs text-dark-400">{t('humidityLabel')}</p>
            <p className="text-lg font-bold text-white">{summary.humidity.min}% - {summary.humidity.max}%</p>
            <p className="text-xs text-dark-500">{t('avgLabel')}: {summary.humidity.avg}%</p>
          </div>
        </div>
      )}
      {activeTab === 'stations' && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <MapPin className="w-5 h-5 text-green-400" />
            {t('stationWiseData')}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {stations.map((station) => {
              // Calculate risk based on real data
              const smRisk = Math.min(1, station.real_soil_moisture_0_7cm / 0.6);
              const rainRisk = Math.min(1, station.real_rainfall_24h / 50);
              const elevRisk = Math.min(1, station.real_elevation / 3000);
              const ndviRisk = Math.max(0, 1 - station.estimated_ndvi);
              const riskScore = (smRisk * 0.3 + rainRisk * 0.25 + elevRisk * 0.25 + ndviRisk * 0.2) * 100;
              const riskLevel = riskScore >= 50 ? 'high' : riskScore >= 30 ? 'moderate' : 'low';

              return (
                <div key={station.id} className="glass rounded-xl p-4 hover:border-dark-600 transition-all">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="text-sm font-semibold text-white">{station.name}</h4>
                      <p className="text-[10px] text-dark-500">{station.state} - {station.id}</p>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      riskLevel === 'high' ? 'bg-red-600/20 text-red-400 border border-red-600/30' :
                      riskLevel === 'moderate' ? 'bg-amber-600/20 text-amber-400 border border-amber-600/30' :
                      'bg-green-600/20 text-green-400 border border-green-600/30'
                    }`}>
                      {riskLevel.toUpperCase()}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 mb-3">
                    <div className="text-center p-1.5 rounded-lg bg-dark-800/50">
                      <Mountain className="w-3 h-3 text-blue-400 mx-auto mb-0.5" />
                      <p className="text-xs font-bold text-white">{station.real_elevation}</p>
                      <p className="text-[9px] text-dark-500">m elev</p>
                    </div>
                    <div className="text-center p-1.5 rounded-lg bg-dark-800/50">
                      <Droplets className="w-3 h-3 text-emerald-400 mx-auto mb-0.5" />
                      <p className="text-xs font-bold text-white">{station.real_soil_moisture_0_7cm}</p>
                      <p className="text-[9px] text-dark-500">SM m³/m³</p>
                    </div>
                    <div className="text-center p-1.5 rounded-lg bg-dark-800/50">
                      <CloudRain className="w-3 h-3 text-cyan-400 mx-auto mb-0.5" />
                      <p className="text-xs font-bold text-white">{station.real_rainfall_24h}</p>
                      <p className="text-[9px] text-dark-500">mm rain</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    <div className="text-center p-1.5 rounded-lg bg-dark-800/50">
                      <Leaf className="w-3 h-3 text-green-400 mx-auto mb-0.5" />
                      <p className="text-xs font-bold text-white">{station.estimated_ndvi}</p>
                      <p className="text-[9px] text-dark-500">NDVI</p>
                    </div>
                    <div className="text-center p-1.5 rounded-lg bg-dark-800/50">
                      <Thermometer className="w-3 h-3 text-red-400 mx-auto mb-0.5" />
                      <p className="text-xs font-bold text-white">{station.real_temperature}°</p>
                      <p className="text-[9px] text-dark-500">temp</p>
                    </div>
                    <div className="text-center p-1.5 rounded-lg bg-dark-800/50">
                      <Wind className="w-3 h-3 text-cyan-400 mx-auto mb-0.5" />
                      <p className="text-xs font-bold text-white">{station.real_humidity}%</p>
                      <p className="text-[9px] text-dark-500">humid</p>
                    </div>
                  </div>

                  {/* Risk bar */}
                  <div className="mt-3">
                    <div className="h-1.5 bg-dark-800 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full transition-all duration-1000 ${
                        riskLevel === 'high' ? 'bg-red-500' :
                        riskLevel === 'moderate' ? 'bg-amber-500' : 'bg-green-500'
                      }`} style={{ width: `${Math.min(100, riskScore)}%` }} />
                    </div>
                    <div className="flex justify-between mt-1">
                      <span className="text-[9px] text-dark-500">{t('satelliteRiskLabel')}</span>
                      <span className="text-[9px] text-dark-400 font-medium">{riskScore.toFixed(1)}/100</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
      {activeTab === 'risk-zones' && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            {t('satelliteBasedRiskZones')}
          </h2>
          <p className="text-xs text-dark-400 mb-4">
            Demonstration risk calculated from the available cached snapshot
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {riskZones.map((zone) => (
              <div key={zone.station_id} className="glass rounded-xl p-4 hover:border-dark-600 transition-all">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="text-sm font-semibold text-white">{zone.name}</h4>
                    <p className="text-[10px] text-dark-500">{zone.state}</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    zone.risk_level === 'critical' ? 'bg-red-600/20 text-red-400 border border-red-600/30' :
                    zone.risk_level === 'high' ? 'bg-orange-600/20 text-orange-400 border border-orange-600/30' :
                    zone.risk_level === 'moderate' ? 'bg-amber-600/20 text-amber-400 border border-amber-600/30' :
                    'bg-green-600/20 text-green-400 border border-green-600/30'
                  }`}>
                    {zone.risk_level.toUpperCase()}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 mb-3">
                  <div className="text-center p-1.5 rounded-lg bg-dark-800/50">
                    <Mountain className="w-3 h-3 text-blue-400 mx-auto mb-0.5" />
                    <p className="text-xs font-bold text-white">{zone.snapshot_data.elevation}m</p>
                    <p className="text-[9px] text-dark-500">elev</p>
                  </div>
                  <div className="text-center p-1.5 rounded-lg bg-dark-800/50">
                    <Droplets className="w-3 h-3 text-emerald-400 mx-auto mb-0.5" />
                    <p className="text-xs font-bold text-white">{zone.snapshot_data.soil_moisture}</p>
                    <p className="text-[9px] text-dark-500">SM</p>
                  </div>
                  <div className="text-center p-1.5 rounded-lg bg-dark-800/50">
                    <CloudRain className="w-3 h-3 text-cyan-400 mx-auto mb-0.5" />
                    <p className="text-xs font-bold text-white">{zone.snapshot_data.rainfall_24h}mm</p>
                    <p className="text-[9px] text-dark-500">rain</p>
                  </div>
                  <div className="text-center p-1.5 rounded-lg bg-dark-800/50">
                    <Leaf className="w-3 h-3 text-green-400 mx-auto mb-0.5" />
                    <p className="text-xs font-bold text-white">{zone.snapshot_data.ndvi}</p>
                    <p className="text-[9px] text-dark-500">NDVI</p>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-dark-400">{t('elevationRisk')}</span>
                    <span className="text-white font-medium">{zone.factors.elevation_risk}%</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-dark-400">{t('soilMoistureRisk')}</span>
                    <span className="text-white font-medium">{zone.factors.soil_moisture_risk}%</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-dark-400">{t('rainfallRiskLabel')}</span>
                    <span className="text-white font-medium">{zone.factors.rainfall_risk}%</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-dark-400">{t('vegetationRisk')}</span>
                    <span className="text-white font-medium">{zone.factors.vegetation_risk}%</span>
                  </div>
                  <div className="flex justify-between text-xs border-t border-dark-700 pt-1">
                    <span className="text-dark-400 font-medium">{t('compositeScore')}</span>
                    <span className={`font-bold ${zone.risk_level === 'critical' ? 'text-red-400' : zone.risk_level === 'high' ? 'text-orange-400' : zone.risk_level === 'moderate' ? 'text-amber-400' : 'text-green-400'}`}>
                      {zone.satellite_risk_score}/100
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
