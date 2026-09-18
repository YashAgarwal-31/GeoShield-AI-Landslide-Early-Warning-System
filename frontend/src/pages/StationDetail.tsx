import { useCallback, useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getStation, getStationHistory, getWeather, getWeatherForecast, getAlertWebSocketUrl } from '../services/api';
import DataSourceBadge from '../components/DataSourceBadge';
import { t } from '../i18n/translations';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area,
  BarChart, Bar,
} from 'recharts';
import {
  ArrowLeft, Radio, Mountain, Droplets, Thermometer,
  Activity, AlertTriangle, TrendingUp, ChevronRight,
  CloudRain, Wind,
} from 'lucide-react';

const RISK_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  low: { bg: 'bg-green-600/10', text: 'text-green-400', border: 'border-green-600/30' },
  moderate: { bg: 'bg-amber-600/10', text: 'text-amber-400', border: 'border-amber-600/30' },
  high: { bg: 'bg-orange-600/10', text: 'text-orange-400', border: 'border-orange-600/30' },
  critical: { bg: 'bg-red-600/10', text: 'text-red-400', border: 'border-red-600/30' },
};

export default function StationDetail() {
  const { stationId } = useParams<{ stationId: string }>();
  const navigate = useNavigate();
  const [station, setStation] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [weather, setWeather] = useState<any>(null);
  const [forecast, setForecast] = useState<any[]>([]);
  const [forecastKind, setForecastKind] = useState<'forecast' | 'demo_history'>('demo_history');
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(24);
  const [activeTab, setActiveTab] = useState<'charts' | 'forecast'>('charts');

  const fetchData = useCallback(async () => {
    if (!stationId) return;
    try {
      const [stationRes, historyRes, weatherRes, forecastRes] = await Promise.all([
        getStation(stationId),
        getStationHistory(stationId, timeRange),
        getWeather(stationId),
        getWeatherForecast(stationId, 48),
      ]);
      setStation(stationRes.data);
      setHistory(historyRes.data);
      setWeather(weatherRes.data);
      setForecast(forecastRes.data.forecast);
      setForecastKind(forecastRes.data.series_kind);
    } catch (e) {
      console.error('Station fetch error:', e);
    } finally {
      setLoading(false);
    }
  }, [stationId, timeRange]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  useEffect(() => {
    if (!stationId) return;
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
          const eventStation = message.station_id || message.alert?.station_id;
          if (
            eventStation === stationId &&
            ['sensor.reading', 'alert.created', 'alert.updated'].includes(message.type)
          ) {
            fetchData();
          }
        } catch {
          // Polling fallback will keep the station view fresh.
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
  }, [stationId, fetchData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-12 h-12 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!station) {
    return (
      <div className="p-8 text-center">
        <p className="text-dark-400">{t('stationNotFound')}</p>
        <button onClick={() => navigate(-1)} className="mt-4 text-green-400 hover:underline">
          {t('goBack')}
        </button>
      </div>
    );
  }

  const { station: s, readings, risk_assessment: risk } = station;
  const riskStyle = RISK_COLORS[risk?.risk_level || 'low'] || RISK_COLORS.low;

  const latestReading = readings?.[readings.length - 1] || {};

  const sensorCards = [
    { label: t('rainfall'), value: `${latestReading.rainfall_mm || 0} mm`, icon: Droplets, color: 'from-blue-500 to-cyan-500' },
    { label: t('soilMoisture'), value: `${latestReading.soil_moisture || 0}%`, icon: Droplets, color: 'from-emerald-500 to-teal-500' },
    { label: t('groundDisplacement'), value: `${latestReading.ground_displacement || 0} mm`, icon: Activity, color: 'from-amber-500 to-orange-500' },
    { label: t('porePressure'), value: `${latestReading.pore_water_pressure || 0} kPa`, icon: TrendingUp, color: 'from-purple-500 to-pink-500' },
    { label: t('temperatureLabel'), value: `${latestReading.soil_temperature || 0}°C`, icon: Thermometer, color: 'from-red-500 to-rose-500' },
  ];

  const formatTime = (ts: string) => {
    try {
      return new Date(ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } catch { return ts; }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Back Button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-dark-400 hover:text-white transition-all"
      >
        <ArrowLeft className="w-4 h-4" />
        <span className="text-sm">{t('goBack')}</span>
      </button>

      {/* Station Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Radio className="w-6 h-6 text-green-400" />
            {s.name}
          </h1>
          <p className="text-dark-400 text-sm mt-1">
            {s.state} • {s.district} • {s.village} • ID: {s.station_id}
          </p>
        </div>
        {risk && (
          <div className={`px-4 py-2 rounded-xl ${riskStyle.bg} border ${riskStyle.border}`}>
            <div className="flex items-center gap-2">
              <AlertTriangle className={`w-5 h-5 ${riskStyle.text}`} />
              <div>
                <p className={`text-lg font-bold ${riskStyle.text}`}>{risk.risk_score}/100</p>
                <p className={`text-xs ${riskStyle.text}`}>{risk.risk_level.toUpperCase()}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Station Info */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { label: t('elevation'), value: `${s.elevation}m`, icon: Mountain },
          { label: t('slopeAngle'), value: `${s.slope_angle}°`, icon: TrendingUp },
          { label: t('soilType'), value: (s.soil_type || 'Unknown').replace('_', ' '), icon: Droplets },
          { label: t('vegetationCover'), value: `${s.vegetation_cover}%`, icon: Droplets },
          { label: t('active'), value: t('active'), icon: Radio },
        ].map((item, i) => (
          <div key={i} className="glass rounded-xl p-3">
            <item.icon className="w-4 h-4 text-dark-400 mb-1" />
            <p className="text-xs text-dark-400">{item.label}</p>
            <p className="text-sm font-semibold text-white capitalize">{item.value}</p>
          </div>
        ))}
      </div>

      {/* Risk Assessment */}
      {risk && (
        <div className="glass rounded-xl p-5 border border-dark-700">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-400" />
            {t('aiRiskAssessment')}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Risk Score */}
            <div className="text-center">
              <div className="relative inline-block">
                <svg className="w-32 h-32" viewBox="0 0 120 120">
                  <circle cx="60" cy="60" r="50" fill="none" stroke="#334155" strokeWidth="10" />
                  <circle
                    cx="60" cy="60" r="50"
                    fill="none"
                    stroke={risk.risk_level === 'critical' ? '#ef4444' : risk.risk_level === 'high' ? '#f97316' : risk.risk_level === 'moderate' ? '#f59e0b' : '#22c55e'}
                    strokeWidth="10"
                    strokeDasharray={`${risk.risk_score * 3.14} 314`}
                    strokeLinecap="round"
                    transform="rotate(-90 60 60)"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <p className="text-2xl font-bold text-white">{risk.risk_score}</p>
                  <p className="text-xs text-dark-400">/ 100</p>
                </div>
              </div>
              <p className={`text-sm font-medium mt-2 ${riskStyle.text}`}>{risk.risk_level.toUpperCase()} RISK</p>
            </div>

            {/* Details */}
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-dark-400">{t('landslideProbability')}</span>
                <span className="text-white font-medium">{(risk.landslide_probability * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-dark-400">{t('timeWindow')}</span>
                <span className="text-white font-medium">{risk.predicted_time_window_hours} {t('hours')}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-dark-400">{t('modelVersion')}</span>
                <span className="text-white font-medium">{risk.model_version}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-dark-400">{t('assessedAt')}</span>
                <span className="text-white font-medium">{new Date(risk.timestamp).toLocaleString()}</span>
              </div>
            </div>

            {/* Contributing Factors */}
            <div>
              <p className="text-xs text-dark-400 mb-2">{t('contributingFactors')}</p>
              <div className="space-y-1">
                {JSON.parse(risk.contributing_factors || '[]').map((factor: string, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-orange-400">
                    <ChevronRight className="w-3 h-3" />
                    {factor}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recommendation */}
          <div className="mt-4 p-3 rounded-lg bg-dark-800/50 border border-dark-700">
            <p className="text-xs text-dark-400 mb-1">{t('recommendation')}</p>
            <p className="text-sm text-white">{risk.recommendation}</p>
          </div>
        </div>
      )}

      {/* Sensor Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Rainfall Chart */}
        <div className="glass rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Droplets className="w-4 h-4 text-blue-400" />
              {t('rainfallHistory')}
            </h3>
            <div className="flex gap-1">
              {[6, 12, 24, 48].map(h => (
                <button
                  key={h}
                  onClick={() => setTimeRange(h)}
                  className={`px-2 py-1 rounded text-xs ${timeRange === h ? 'bg-green-600/20 text-green-400' : 'text-dark-400 hover:text-white'}`}
                >
                  {h}h
                </button>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={readings}>
              <defs>
                <linearGradient id="rainGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="timestamp" tick={{ fontSize: 9, fill: '#94a3b8' }} tickFormatter={formatTime} />
              <YAxis tick={{ fontSize: 9, fill: '#94a3b8' }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              <Area type="monotone" dataKey="rainfall_mm" stroke="#3b82f6" fill="url(#rainGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Soil Moisture & Displacement */}
        <div className="glass rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
            <Activity className="w-4 h-4 text-emerald-400" />
            {t('soilMoistureDisplacement')}
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={readings}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="timestamp" tick={{ fontSize: 9, fill: '#94a3b8' }} tickFormatter={formatTime} />
              <YAxis tick={{ fontSize: 9, fill: '#94a3b8' }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              <Line type="monotone" dataKey="soil_moisture" stroke="#22c55e" strokeWidth={2} dot={false} name={t('soilMoisture')} />
              <Line type="monotone" dataKey="ground_displacement" stroke="#f97316" strokeWidth={2} dot={false} name={t('groundDisplacement')} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Weather Card */}
      {weather?.data && (
        <div className="glass rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              ☁️ {t('weatherTitle')}
            </h3>
            <div className="flex bg-dark-800 rounded-lg p-1 border border-dark-700">
              {(['charts', 'forecast'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
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

          <div className="mb-4">
            <DataSourceBadge source={weather.source} />
          </div>

          {activeTab === 'charts' && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {[
                { label: t('temperatureLabel'), value: `${weather.data.temperature}°C` },
                { label: t('humidityLabel'), value: `${weather.data.humidity}%` },
                { label: 'Wind', value: `${weather.data.wind_speed} km/h` },
                { label: t('forecast24h'), value: `${weather.data.forecast_rainfall_24h} mm` },
                { label: t('forecast48h'), value: `${weather.data.forecast_rainfall_48h} mm` },
              ].map((item, i) => (
                <div key={i} className="p-3 rounded-lg bg-dark-800/50">
                  <p className="text-xs text-dark-400">{item.label}</p>
                  <p className="text-lg font-bold text-white">{item.value}</p>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'forecast' && forecast.length > 0 && (
            <div className="space-y-4">
              <h4 className="text-xs text-dark-400 font-medium">
                {forecastKind === 'forecast' ? '48-Hour Forecast' : 'Seeded Demo Weather History'}
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-dark-400 border-b border-dark-700">
                      <th className="text-left py-2 px-3 font-medium">{t('forecastTime')}</th>
                      <th className="text-left py-2 px-3 font-medium">
                        <Thermometer className="w-4 h-4 inline" /> {t('tempShort')}
                      </th>
                      <th className="text-left py-2 px-3 font-medium">
                        <Droplets className="w-4 h-4 inline" /> {t('rainShort')}
                      </th>
                      <th className="text-left py-2 px-3 font-medium">
                        <Wind className="w-4 h-4 inline" /> {t('humidityShort')}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {forecast.map((f, i) => (
                      <tr key={i} className="border-b border-dark-800">
                        <td className="py-2 px-3 text-dark-300">
                          {new Date(f.timestamp).toLocaleString()}
                        </td>
                        <td className="py-2 px-3 text-white">{f.temperature}</td>
                        <td className="py-2 px-3 text-cyan-400">{f.rainfall_1h || 0}</td>
                        <td className="py-2 px-3 text-emerald-400">{f.humidity}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
