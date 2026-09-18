import { useCallback, useEffect, useState } from 'react';
import {
  getDashboardStats, getRainfallTrend, getRiskTrend, getStateSummary,
  getRiskHeatmap, getStations, getAlerts, acknowledgeAlert, resolveAlert,
  getAlertWebSocketUrl, DashboardStats, HeatmapPoint, Station, Alert,
} from '../services/api';
import { t } from '../i18n/translations';
import { useAuth } from '../App';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area, BarChart, Bar, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import {
  Activity, AlertTriangle, Users, FileText, TrendingUp,
  Radio, Droplets, Mountain, MapPin, Clock, Shield, Zap,
  ChevronRight, Building2, Car, Eye, Cloud, Sun, Wind,
  Thermometer, BarChart3, Layers, Target, Bell, Map,
  Navigation, AlertCircle, CheckCircle, XCircle, Info,
} from 'lucide-react';

const RISK_COLORS: Record<string, string> = {
  low: '#22c55e',
  moderate: '#f59e0b',
  high: '#f97316',
  very_high: '#ea580c',
  critical: '#ef4444',
};

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [rainfall, setRainfall] = useState<{ timestamp: string; avg_rainfall: number }[]>([]);
  const [riskTrend, setRiskTrend] = useState<{ timestamp: string; avg_risk: number }[]>([]);
  const [stateData, setStateData] = useState<{ state: string; stations: number; avg_risk_score: number; critical_count: number }[]>([]);
  const [stations, setStations] = useState<Station[]>([]);
  const [alertsData, setAlertsData] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [activeTab, setActiveTab] = useState<'overview' | 'stations' | 'alerts'>('overview');

  useEffect(() => {
    const clock = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(clock);
  }, []);

  const fetchData = useCallback(async () => {
    try {
      // Fetch each endpoint independently so one failure doesn't break all
      const settle = <T,>(p: Promise<T>): Promise<T | null> => p.catch(() => null);
      const [statsRes, rainRes, riskRes, stateRes, stationsRes, alertsRes] = await Promise.all([
        settle(getDashboardStats()),
        settle(getRainfallTrend()),
        settle(getRiskTrend()),
        settle(getStateSummary()),
        settle(getStations()),
        settle(getAlerts({ status: 'active' })),
      ]);
      if (statsRes?.data) setStats(statsRes.data);
      if (rainRes?.data) setRainfall(rainRes.data);
      if (riskRes?.data) setRiskTrend(riskRes.data);
      if (stateRes?.data) setStateData(stateRes.data);
      if (stationsRes?.data) setStations(stationsRes.data);
      if (alertsRes?.data) setAlertsData(alertsRes.data);
    } catch (e) {
      console.error('Dashboard fetch error:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

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
            'alert.created',
            'alert.updated',
            'alerts.reset',
            'report.created',
            'report.updated',
          ].includes(message.type)) {
            fetchData();
          }
        } catch {
          // Ignore malformed/non-operational frames; polling remains the fallback.
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
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-20 h-20 border-4 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-6" />
          <div className="space-y-2">
            <p className="text-white font-semibold text-lg">{t('initializing')}</p>
            <p className="text-dark-400 text-sm">{t('connectingSensorsShort')}</p>
            <div className="flex items-center justify-center gap-2 mt-4">
              <div className="flex gap-1">
                {[0, 1, 2].map(i => (
                  <div key={i} className="w-2 h-2 rounded-full bg-green-500 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!stats) return <div className="p-8 text-dark-400">{t('failedToLoad')}</div>;

  const riskPieData = [
    { name: t('lowRisk'), value: stats.risk_distribution.low, color: RISK_COLORS.low },
    { name: t('moderateRisk'), value: stats.risk_distribution.moderate, color: RISK_COLORS.moderate },
    { name: t('highRisk'), value: stats.risk_distribution.high, color: RISK_COLORS.high },
    { name: t('criticalRisk'), value: stats.risk_distribution.critical, color: RISK_COLORS.critical },
  ].filter(d => d.value > 0);

  const radarData = stateData.map(s => ({
    state: s.state.replace(' Pradesh', '').replace(' Islands', ''),
    risk: s.avg_risk_score,
    fullMark: 100,
  }));

  const topStations = [...stations]
    .sort((a, b) => (b.risk?.score || 0) - (a.risk?.score || 0))
    .slice(0, 5);

  const statCards = [
    { label: t('activeSensors'), value: stats.total_stations, icon: Radio, color: 'from-blue-500 to-cyan-500', textColor: 'text-blue-400', sub: `${stats.active_stations} ${t('online')}` },
    { label: t('activeAlerts'), value: stats.active_alerts, icon: AlertTriangle, color: stats.active_alerts > 0 ? 'from-red-500 to-orange-500' : 'from-green-500 to-emerald-500', textColor: stats.active_alerts > 0 ? 'text-red-400' : 'text-green-400', pulse: stats.active_alerts > 0, sub: t('requiresAttention') },
    { label: t('peopleAtRisk'), value: stats.affected_population.toLocaleString(), icon: Users, color: 'from-purple-500 to-pink-500', textColor: 'text-purple-400', sub: t('acrossNER') },
    { label: t('pendingReports'), value: stats.pending_reports, icon: FileText, color: 'from-amber-500 to-yellow-500', textColor: 'text-amber-400', sub: `${stats.recent_reports_24h} ${t('in24h')}` },
    { label: t('avgRiskScore'), value: stats.average_risk_score.toFixed(1), icon: TrendingUp, color: 'from-rose-500 to-red-500', textColor: 'text-rose-400', sub: t('outOf100') },
    { label: t('highRiskVillages'), value: stats.high_risk_villages, icon: MapPin, color: 'from-orange-500 to-red-500', textColor: 'text-orange-400', sub: t('ofTotal').replace('{n}', String(stats.total_villages)) },
  ];

  const formatTime = (ts: string) => {
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } catch { return ts; }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 shadow-xl">
          <p className="text-xs text-dark-400">{formatTime(label)}</p>
          {payload.map((p: any, i: number) => (
            <p key={i} className="text-sm font-medium" style={{ color: p.color }}>
              {p.name}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const getTimeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  const handleAcknowledge = async (id: number) => {
    try {
      await acknowledgeAlert(id);
      setAlertsData(prev => prev.filter(a => a.id !== id));
    } catch (e) {
      console.error('Acknowledge failed:', e);
    }
  };

  const handleResolve = async (id: number) => {
    try {
      await resolveAlert(id);
      setAlertsData(prev => prev.filter(a => a.id !== id));
    } catch (e) {
      console.error('Resolve failed:', e);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <Shield className="w-6 h-6 sm:w-8 sm:h-8 text-green-400" />
            <div>
              <h1 className="text-lg sm:text-2xl font-bold text-white">{t('dashboard')}</h1>
              <p className="text-dark-400 text-xs sm:text-sm">{t('regionSubtitle')}</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Tab Switcher */}
          <div className="flex bg-dark-800 rounded-xl p-1 border border-dark-700">
            {(['overview', 'stations', 'alerts'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-2 sm:px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeTab === tab
                    ? 'bg-green-600/20 text-green-400 border border-green-600/30'
                    : 'text-dark-400 hover:text-white border border-transparent'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map((card, i) => (
          <div
            key={i}
            className={`glass rounded-xl p-4 transition-all duration-300 hover:scale-[1.03] hover:border-dark-600 cursor-default group ${
              card.pulse ? 'border-red-600/30 animate-pulse' : ''
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}>
                <card.icon className="w-5 h-5 text-white" />
              </div>
              {card.pulse && (
                <span className="flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                </span>
              )}
            </div>
            <p className="text-2xl font-bold text-white">{card.value}</p>
            <p className="text-xs text-dark-400 mt-1">{card.label}</p>
            <p className="text-[10px] text-dark-500 mt-0.5">{card.sub}</p>
          </div>
        ))}
      </div>

      {activeTab === 'overview' && (
        <>
          {/* Charts Row 1 */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Rainfall Trend */}
            <div className="lg:col-span-2 glass rounded-xl p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-blue-600/20 flex items-center justify-center">
                    <Droplets className="w-4 h-4 text-blue-400" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">{t('rainfallTrend')}</h3>
                    <p className="text-xs text-dark-500">48h average across all stations</p>
                  </div>
                </div>
                <span className="text-xs text-dark-500">{rainfall.length} data points</span>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={rainfall.slice(-48)}>
                  <defs>
                    <linearGradient id="rainfallGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="timestamp" tick={{ fontSize: 9, fill: '#64748b' }} tickFormatter={formatTime} interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 9, fill: '#64748b' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="avg_rainfall" stroke="#3b82f6" fill="url(#rainfallGrad)" strokeWidth={2} name="Rainfall (mm)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Risk Distribution Pie */}
            <div className="glass rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-orange-600/20 flex items-center justify-center">
                  <Activity className="w-4 h-4 text-orange-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">{t('riskDistribution')}</h3>
                  <p className="text-xs text-dark-500">Across {stats.total_stations} stations</p>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie
                    data={riskPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                    animationBegin={0}
                    animationDuration={1200}
                  >
                    {riskPieData.map((entry, index) => (
                      <Cell key={index} fill={entry.color} stroke="transparent" />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex justify-center gap-3 mt-2">
                {riskPieData.map((d, i) => (
                  <div key={i} className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                    <span className="text-xs text-dark-400">{d.name}: <span className="text-white font-medium">{d.value}</span></span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Charts Row 2 */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Risk Trend */}
            <div className="glass rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-red-600/20 flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 text-red-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">{t('riskTrend')}</h3>
                  <p className="text-xs text-dark-500">48h average risk score</p>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={riskTrend.slice(-48)}>
                  <defs>
                    <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="timestamp" tick={{ fontSize: 9, fill: '#64748b' }} tickFormatter={formatTime} interval="preserveStartEnd" />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: '#64748b' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="avg_risk" stroke="transparent" fill="url(#riskGrad)" />
                  <Line type="monotone" dataKey="avg_risk" stroke="#ef4444" strokeWidth={2} dot={false} name={t('riskScore')} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Road Status */}
            <div className="glass rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-blue-600/20 flex items-center justify-center">
                  <Car className="w-4 h-4 text-blue-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">{t('roadStatus')}</h3>
                  <p className="text-xs text-dark-500">{stats.road_status.open + stats.road_status.partially_blocked + stats.road_status.blocked} {t('roadsMonitored').replace('{n}', '')}</p>
                </div>
              </div>
              <div className="space-y-4 mt-2">
                {[
                  { label: t('open'), value: stats.road_status.open, color: 'bg-green-500', textColor: 'text-green-400', pct: 100 },
                  { label: t('partiallyBlocked'), value: stats.road_status.partially_blocked, color: 'bg-amber-500', textColor: 'text-amber-400', pct: 60 },
                  { label: t('blocked'), value: stats.road_status.blocked, color: 'bg-red-500', textColor: 'text-red-400', pct: 30 },
                ].map((item, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="text-dark-300 flex items-center gap-1.5">
                        <div className={`w-2 h-2 rounded-full ${item.color}`} />
                        {item.label}
                      </span>
                      <span className={`font-semibold ${item.textColor}`}>{item.value} {t('roads')}</span>
                    </div>
                    <div className="h-2 bg-dark-800 rounded-full overflow-hidden">
                      <div className={`h-full ${item.color} rounded-full transition-all duration-1000`} style={{ width: `${Math.max(item.pct, item.value * 20)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 p-2.5 rounded-lg bg-dark-800/50 border border-dark-700">
                <div className="flex items-center gap-2">
                  <Zap className={`w-4 h-4 ${stats.road_status.blocked > 0 ? 'text-red-400' : 'text-green-400'}`} />
                  <span className="text-xs text-dark-300">
                    {stats.road_status.blocked > 0
                      ? `${stats.road_status.blocked} ${t('roadBlocked')}`
                      : t('allRoutesOpen')}
                  </span>
                </div>
              </div>
            </div>

            {/* State Summary */}
            <div className="glass rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-emerald-600/20 flex items-center justify-center">
                  <Mountain className="w-4 h-4 text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">{t('stateSummary')}</h3>
                  <p className="text-xs text-dark-500">8 NER states monitored</p>
                </div>
              </div>
              <div className="space-y-2">
                {stateData.map((state, i) => (
                  <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-dark-800/50 hover:bg-dark-800 transition-all cursor-default group">
                    <div className="flex items-center gap-2">
                      <div className={`w-1.5 h-6 rounded-full ${
                        state.avg_risk_score >= 50 ? 'bg-red-500' :
                        state.avg_risk_score >= 25 ? 'bg-amber-500' : 'bg-green-500'
                      }`} />
                      <div>
                        <p className="text-xs font-medium text-white">{state.state}</p>
                        <p className="text-[10px] text-dark-500">{state.stations} stations</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-bold ${
                        state.avg_risk_score >= 50 ? 'text-red-400' :
                        state.avg_risk_score >= 25 ? 'text-amber-400' : 'text-green-400'
                      }`}>
                        {state.avg_risk_score}
                      </span>
                      {state.critical_count > 0 && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-600/20 text-red-400 border border-red-600/30">
                          {state.critical_count} CRIT
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* State Risk Radar Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="glass rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-purple-600/20 flex items-center justify-center">
                  <Target className="w-4 h-4 text-purple-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">{t('stateRiskRadar')}</h3>
                  <p className="text-xs text-dark-500">{t('comparativeRisk')}</p>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={250}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#1e293b" />
                  <PolarAngleAxis dataKey="state" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 8, fill: '#64748b' }} />
                  <Radar name="Risk" dataKey="risk" stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* Top Risk Stations */}
            <div className="glass rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-red-600/20 flex items-center justify-center">
                  <AlertCircle className="w-4 h-4 text-red-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">{t('topRiskStations')}</h3>
                  <p className="text-xs text-dark-500">{t('highestRiskLocations')}</p>
                </div>
              </div>
              <div className="space-y-3">
                {topStations.map((station, i) => {
                  const risk = station.risk;
                  const riskLevel = risk?.level || 'low';
                  const riskScore = risk?.score || 0;
                  return (
                    <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-dark-800/50 hover:bg-dark-800 transition-all cursor-pointer group"
                      onClick={() => window.location.href = `/station/${station.station_id}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${
                          riskLevel === 'critical' ? 'bg-red-600/20 text-red-400' :
                          riskLevel === 'high' ? 'bg-orange-600/20 text-orange-400' :
                          riskLevel === 'moderate' ? 'bg-amber-600/20 text-amber-400' :
                          'bg-green-600/20 text-green-400'
                        }`}>
                          #{i + 1}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-white group-hover:text-green-400 transition-colors">{station.name}</p>
                          <p className="text-[10px] text-dark-500">{station.state} • {station.district}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <p className={`text-lg font-bold ${
                            riskLevel === 'critical' ? 'text-red-400' :
                            riskLevel === 'high' ? 'text-orange-400' :
                            riskLevel === 'moderate' ? 'text-amber-400' : 'text-green-400'
                          }`}>{riskScore}</p>
                          <p className="text-[10px] text-dark-500 capitalize">{riskLevel}</p>
                        </div>
                        <ChevronRight className="w-4 h-4 text-dark-500 group-hover:text-green-400 transition-colors" />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </>
      )}

      {activeTab === 'stations' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {stations.map((station) => {
            const risk = station.risk;
            const riskLevel = risk?.level || 'low';
            const riskScore = risk?.score || 0;
            return (
              <div key={station.station_id} className="glass rounded-xl p-4 hover:border-dark-600 transition-all cursor-pointer group"
                onClick={() => window.location.href = `/station/${station.station_id}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="text-sm font-semibold text-white group-hover:text-green-400 transition-colors">{station.name}</h4>
                    <p className="text-[10px] text-dark-500">{station.state} • {station.district}</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    riskLevel === 'critical' ? 'bg-red-600/20 text-red-400 border border-red-600/30' :
                    riskLevel === 'high' ? 'bg-orange-600/20 text-orange-400 border border-orange-600/30' :
                    riskLevel === 'moderate' ? 'bg-amber-600/20 text-amber-400 border border-amber-600/30' :
                    'bg-green-600/20 text-green-400 border border-green-600/30'
                  }`}>
                    {riskLevel.toUpperCase()}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 mb-3">
                  <div className="text-center p-1.5 rounded-lg bg-dark-800/50">
                    <Droplets className="w-3 h-3 text-blue-400 mx-auto mb-0.5" />
                    <p className="text-xs font-bold text-white">{station.latest_reading?.rainfall_mm || 0}</p>
                    <p className="text-[9px] text-dark-500">mm</p>
                  </div>
                  <div className="text-center p-1.5 rounded-lg bg-dark-800/50">
                    <Mountain className="w-3 h-3 text-emerald-400 mx-auto mb-0.5" />
                    <p className="text-xs font-bold text-white">{station.elevation}</p>
                    <p className="text-[9px] text-dark-500">m</p>
                  </div>
                  <div className="text-center p-1.5 rounded-lg bg-dark-800/50">
                    <TrendingUp className="w-3 h-3 text-orange-400 mx-auto mb-0.5" />
                    <p className="text-xs font-bold text-white">{station.slope_angle}°</p>
                    <p className="text-[9px] text-dark-500">slope</p>
                  </div>
                </div>
                {/* Risk bar */}
                <div className="h-1.5 bg-dark-800 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all duration-1000 ${
                    riskLevel === 'critical' ? 'bg-red-500' :
                    riskLevel === 'high' ? 'bg-orange-500' :
                    riskLevel === 'moderate' ? 'bg-amber-500' : 'bg-green-500'
                  }`} style={{ width: `${riskScore}%` }} />
                </div>
                <div className="flex justify-between mt-1">
                  <span className="text-[9px] text-dark-500">{t('riskScoreLabel')}</span>
                  <span className="text-[9px] text-dark-400 font-medium">{riskScore}/100</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {activeTab === 'alerts' && (
        <div className="glass rounded-xl p-6">
          <div className="flex items-center gap-2 mb-6">
            <Bell className="w-5 h-5 text-red-400" />
            <h3 className="text-lg font-semibold text-white">{t('activeAlertsWarnings')}</h3>
            <span className="ml-auto text-xs text-dark-500">{alertsData.length} {t('active').toLowerCase()}</span>
          </div>
          {alertsData.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle className="w-10 h-10 text-green-500 mx-auto mb-2" />
              <p className="text-dark-400 text-sm">{t('noData')}</p>
            </div>
          ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {alertsData.map((alert) => {
              const timeAgo = getTimeAgo(alert.created_at);
              return (
              <div key={alert.id} className={`p-4 rounded-xl border transition-all hover:scale-[1.01] ${
                alert.risk_level === 'critical' ? 'bg-red-600/10 border-red-600/30' :
                alert.risk_level === 'high' ? 'bg-orange-600/10 border-orange-600/30' :
                'bg-amber-600/10 border-amber-600/30'
              }`}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-semibold text-white">{alert.title}</p>
                    <p className="text-xs text-dark-400 mt-1">{t('stationLabel')}: {alert.station_id} \u2022 {timeAgo}</p>
                    <p className="text-xs text-dark-400 mt-0.5">\ud83d\udc65 {alert.affected_population.toLocaleString()} {t('peopleAffected')}</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    alert.risk_level === 'critical' ? 'bg-red-600/20 text-red-400' :
                    alert.risk_level === 'high' ? 'bg-orange-600/20 text-orange-400' :
                    'bg-amber-600/20 text-amber-400'
                  }`}>
                    {alert.risk_level.toUpperCase()}
                  </span>
                </div>
                <div className="flex gap-2 mt-3">
                  {user && ['admin', 'field_officer', 'district_admin'].includes(user.role) && (
                    <button
                      onClick={() => handleAcknowledge(alert.id)}
                      className="px-3 py-1 rounded-lg bg-amber-600/20 text-amber-400 border border-amber-600/30 text-xs font-medium hover:bg-amber-600/30 transition-all"
                    >
                      {t('acknowledge')}
                    </button>
                  )}
                  {user?.role === 'admin' && (
                    <button
                      onClick={() => handleResolve(alert.id)}
                      className="px-3 py-1 rounded-lg bg-green-600/20 text-green-400 border border-green-600/30 text-xs font-medium hover:bg-green-600/30 transition-all"
                    >
                      {t('resolve')}
                    </button>
                  )}
                </div>
              </div>
              );
            })}
          </div>
          )}
        </div>
      )}

      {/* Footer Status */}
      <div className="glass rounded-xl p-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <Radio className="w-3 h-3 text-green-400" />
            <span className="text-[10px] text-dark-400">{stats.active_stations} sensors online</span>
          </div>
          <div className="flex items-center gap-1.5">
            <AlertTriangle className="w-3 h-3 text-red-400" />
            <span className="text-[10px] text-dark-400">{stats.active_alerts} active alerts</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Building2 className="w-3 h-3 text-purple-400" />
            <span className="text-[10px] text-dark-400">{stats.total_villages} villages monitored</span>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <Clock className="w-3 h-3 text-dark-500" />
          <span className="text-[10px] text-dark-500">Last update: {new Date(stats.last_updated).toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  );
}
