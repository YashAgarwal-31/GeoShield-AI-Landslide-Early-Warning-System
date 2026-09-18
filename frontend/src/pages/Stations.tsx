import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getStations,
  getAlertWebSocketUrl,
  Station,
} from '../services/api';
import { t } from '../i18n/translations';
import {
  Radio, Search, MapPin, Mountain, Droplets, TrendingUp,
  ChevronRight, Activity, Filter,
} from 'lucide-react';

const RISK_STYLES: Record<string, { bg: string; border: string; text: string; bar: string; icon: string }> = {
  critical: { bg: 'bg-red-600/10', border: 'border-red-600/30', text: 'text-red-400', bar: 'bg-red-500', icon: '🔴' },
  high: { bg: 'bg-orange-600/10', border: 'border-orange-600/30', text: 'text-orange-400', bar: 'bg-orange-500', icon: '🟠' },
  moderate: { bg: 'bg-amber-600/10', border: 'border-amber-600/30', text: 'text-amber-400', bar: 'bg-amber-500', icon: '🟡' },
  low: { bg: 'bg-green-600/10', border: 'border-green-600/30', text: 'text-green-400', bar: 'bg-green-500', icon: '🟢' },
};

export default function Stations() {
  const navigate = useNavigate();
  const [stations, setStations] = useState<Station[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('all');
  const [stateFilter, setStateFilter] = useState('all');

  const fetchStations = useCallback(async () => {
    try {
      const res = await getStations();
      setStations(res.data);
    } catch (e) {
      console.error('Stations fetch error:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStations();
    const interval = setInterval(fetchStations, 30000);
    return () => clearInterval(interval);
  }, [fetchStations]);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let stopped = false;

    const connect = () => {
      if (stopped) return;
      try {
        socket = new WebSocket(getAlertWebSocketUrl('all'));
      } catch {
        reconnectTimer = setTimeout(connect, 3000);
        return;
      }
      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if ([
            'sensor.reading',
            'alerts.reset',
            'station.created',
            'station.updated',
          ].includes(message.type)) {
            fetchStations();
          }
        } catch {
          // Polling fallback will keep the view fresh.
        }
      };
      socket.onerror = () => socket?.close();
      socket.onclose = (event) => {
        if (event.code !== 4401 && !stopped) reconnectTimer = setTimeout(connect, 3000);
      };
    };

    connect();
    return () => {
      stopped = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [fetchStations]);

  // Get unique states for filter
  const states = [...new Set(stations.map(s => s.state))].sort();

  // Filter stations
  const filtered = stations.filter(s => {
    if (search && !s.name.toLowerCase().includes(search.toLowerCase()) &&
        !s.station_id.toLowerCase().includes(search.toLowerCase()) &&
        !s.district.toLowerCase().includes(search.toLowerCase())) return false;
    if (riskFilter !== 'all' && s.risk?.level !== riskFilter) return false;
    if (stateFilter !== 'all' && s.state !== stateFilter) return false;
    return true;
  });

  // Stats
  const stats = {
    total: stations.length,
    critical: stations.filter(s => s.risk?.level === 'critical').length,
    high: stations.filter(s => s.risk?.level === 'high').length,
    moderate: stations.filter(s => s.risk?.level === 'moderate').length,
    low: stations.filter(s => s.risk?.level === 'low').length,
    avgRisk: stations.length > 0
      ? (stations.reduce((sum, s) => sum + (s.risk?.score || 0), 0) / stations.length).toFixed(1)
      : '0',
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-10 h-10 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Radio className="w-6 h-6 text-green-400" />
            {t('stations')}
          </h1>
          <p className="text-dark-400 text-sm mt-1">{t('regionSubtitle')}</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { label: t('totalStations'), value: stats.total, color: 'from-blue-500 to-cyan-500' },
          { label: t('criticalLevelShort'), value: stats.critical, color: 'from-red-600 to-red-500' },
          { label: t('highRiskLabel'), value: stats.high, color: 'from-orange-500 to-amber-500' },
          { label: t('moderateRisk'), value: stats.moderate, color: 'from-amber-500 to-yellow-500' },
          { label: t('lowRisk'), value: stats.low, color: 'from-green-500 to-emerald-500' },
        ].map((card, i) => (
          <div key={i} className="glass rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                <Activity className="w-4 h-4 text-white" />
              </div>
            </div>
            <p className="text-2xl font-bold text-white">{card.value}</p>
            <p className="text-xs text-dark-400">{card.label}</p>
          </div>
        ))}
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col gap-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t('searchStations')}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-dark-800 border border-dark-700 text-white text-sm placeholder-dark-500 focus:outline-none focus:border-green-600/50 transition-all"
            />
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {['all', 'critical', 'high', 'moderate', 'low'].map((level) => (
              <button
                key={level}
                onClick={() => setRiskFilter(level)}
                className={`px-3 py-2 rounded-lg text-xs font-medium transition-all whitespace-nowrap min-h-[40px] ${
                  riskFilter === level
                    ? 'bg-green-600/20 text-green-400 border border-green-600/30'
                    : 'bg-dark-800 text-dark-400 border border-dark-700 hover:text-white'
                }`}
              >
                {level === 'all' ? t('allLevels') : level === 'critical' ? t('criticalLevelShort') : level === 'high' ? t('highRisk') : level === 'moderate' ? t('moderateRisk') : t('lowRisk')}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-dark-400"><Filter className="w-3 h-3 inline mr-1" />{t('state')}:</span>
          <select
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value)}
            className="px-3 py-2 rounded-lg text-xs font-medium bg-dark-800 text-dark-400 border border-dark-700 hover:text-white focus:outline-none focus:border-green-600/50 transition-all min-h-[40px]"
          >
            <option value="all">{t('all')}</option>
            {states.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Results count */}
      <p className="text-xs text-dark-400">
        {filtered.length} {t('stations')} {t('found')}
      </p>

      {/* Station Grid */}
      {filtered.length === 0 ? (
        <div className="text-center py-12">
          <Radio className="w-12 h-12 text-dark-500 mx-auto mb-3" />
          <p className="text-dark-400">{t('noStationsFound')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((station) => {
            const risk = station.risk;
            const riskLevel = risk?.level || 'low';
            const riskScore = risk?.score || 0;
            const style = RISK_STYLES[riskLevel] || RISK_STYLES.low;
            return (
              <div
                key={station.station_id}
                className={`glass rounded-xl p-4 border ${style.border} ${style.bg} transition-all hover:scale-[1.02] cursor-pointer group`}
                onClick={() => navigate(`/station/${station.station_id}`)}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{style.icon}</span>
                    <div>
                      <h3 className="text-sm font-semibold text-white group-hover:text-green-400 transition-colors">
                        {station.name}
                      </h3>
                      <p className="text-xs text-dark-500">{station.station_id}</p>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-dark-500 group-hover:text-green-400 transition-colors" />
                </div>

                <div className="flex items-center gap-2 text-xs text-dark-400 mb-3">
                  <MapPin className="w-3 h-3" />
                  <span>{station.state} • {station.district}</span>
                </div>

                {/* Sensor readings */}
                <div className="grid grid-cols-3 gap-2 mb-3">
                  <div className="text-center p-1.5 rounded-lg bg-dark-800/50">
                    <Droplets className="w-3 h-3 text-blue-400 mx-auto mb-0.5" />
                    <p className="text-xs font-bold text-white">{station.latest_reading?.rainfall_mm || 0}</p>
                    <p className="text-[10px] text-dark-500">mm</p>
                  </div>
                  <div className="text-center p-1.5 rounded-lg bg-dark-800/50">
                    <Mountain className="w-3 h-3 text-emerald-400 mx-auto mb-0.5" />
                    <p className="text-xs font-bold text-white">{station.elevation}</p>
                    <p className="text-[10px] text-dark-500">m</p>
                  </div>
                  <div className="text-center p-1.5 rounded-lg bg-dark-800/50">
                    <TrendingUp className="w-3 h-3 text-orange-400 mx-auto mb-0.5" />
                    <p className="text-xs font-bold text-white">{station.slope_angle}°</p>
                    <p className="text-[10px] text-dark-500">{t('slope')}</p>
                  </div>
                </div>

                {/* Risk bar */}
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-dark-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-1000 ${style.bar}`}
                      style={{ width: `${Math.min(riskScore, 100)}%` }}
                    />
                  </div>
                  <span className={`text-[10px] font-bold ${style.text}`}>
                    {riskScore.toFixed(1)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
