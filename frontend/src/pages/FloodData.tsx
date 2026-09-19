import { useEffect, useState } from 'react';
import { getFloodData, getFloodSummary, getFloodCorrelation, FloodDistrict, FloodSummary, FloodLandslideCorrelation, DataSourceMetadata } from '../services/api';
import { t } from '../i18n/translations';
import DataSourceBadge from '../components/DataSourceBadge';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ScatterChart, Scatter, Cell, Legend, Line, LineChart, AreaChart, Area,
} from 'recharts';
import { Droplets, AlertTriangle, TrendingUp, Waves, MapPin, Activity } from 'lucide-react';

const RISK_COLOR = (score: number) => {
  if (score >= 70) return '#ef4444';
  if (score >= 50) return '#f97316';
  if (score >= 30) return '#f59e0b';
  return '#22c55e';
};

export default function FloodData() {
  const [data, setData] = useState<FloodDistrict[]>([]);
  const [summary, setSummary] = useState<FloodSummary | null>(null);
  const [correlation, setCorrelation] = useState<FloodLandslideCorrelation[]>([]);
  const [liveSource, setLiveSource] = useState<DataSourceMetadata | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [floodRes, summaryRes, corrRes] = await Promise.all([
          getFloodData(),
          getFloodSummary(),
          getFloodCorrelation(),
        ]);
        setData(floodRes.data.data || []);
        setLiveSource(floodRes.data.live_source || null);
        setSummary(summaryRes.data);
        setCorrelation(corrRes.data.correlation);
      } catch (e) {
        console.error('Flood data fetch error:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Droplets className="w-6 h-6 text-blue-400" />
          {t('floodRiskMonitoring')}
        </h1>
        <p className="text-dark-400 text-sm mt-1">{t('floodLandslideCompoundAnalysis')}</p>
      </div>

      {liveSource && <DataSourceBadge source={liveSource} />}

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: t('districtsMonitored'), value: summary.total_districts, icon: MapPin, color: 'from-blue-500 to-cyan-500' },
            { label: t('avgFloodRisk'), value: `${summary.avg_risk_score}/100`, icon: Droplets, color: 'from-cyan-500 to-teal-500' },
            { label: t('totalHistoricalEvents'), value: summary.total_historical_events, icon: AlertTriangle, color: 'from-orange-500 to-red-500' },
            { label: t('highRiskDistricts'), value: summary.high_risk_districts, icon: Waves, color: 'from-red-500 to-pink-500' },
          ].map((card, i) => (
            <div key={i} className="glass rounded-xl p-4 border border-dark-700">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                  <card.icon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-xs text-dark-400">{card.label}</p>
                  <p className="text-xl font-bold text-white">{card.value}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Flood Risk Bar Chart */}
      <div className="glass rounded-xl p-5 border border-dark-700">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Droplets className="w-4 h-4 text-blue-400" />
          {t('floodRiskByDistrict')}
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data.slice(0, 10)}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="district" tick={{ fontSize: 10, fill: '#94a3b8' }} angle={-30} textAnchor="end" height={60} />
            <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
            <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
            <Bar dataKey="flood_risk_score" name="Flood Risk" radius={[4, 4, 0, 0]}>
              {data.slice(0, 10).map((entry, i) => (
                <Cell key={i} fill={RISK_COLOR(entry.flood_risk_score)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Compound Risk: Flood vs Landslide Scatter */}
      {correlation.length > 0 && (
        <div className="glass rounded-xl p-5 border border-dark-700">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-orange-400" />
            {t('floodVsLandslideCompoundRisk')}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="flood_risk" name={t('floodRisk')} tick={{ fontSize: 10, fill: '#94a3b8' }} label={{ value: t('floodRisk'), position: 'bottom', fill: '#94a3b8', fontSize: 11 }} />
              <YAxis dataKey="landslide_risk" name={t('landslideRisk')} tick={{ fontSize: 10, fill: '#94a3b8' }} label={{ value: t('landslideRisk'), angle: -90, position: 'left', fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                formatter={(value: number, name: string) => [value, name]}
                labelFormatter={() => t('districtsMonitored')}
              />
              <Scatter data={correlation.filter(c => c.has_landslide_data)} fill="#3b82f6">
                {correlation.filter(c => c.has_landslide_data).map((entry, i) => (
                  <Cell key={i} fill={RISK_COLOR(entry.compound_risk)} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
          <p className="text-xs text-dark-400 mt-2">
            {t('compoundRiskFormula')}
          </p>
        </div>
      )}

      {/* District Table */}
      <div className="glass rounded-xl p-5 border border-dark-700">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <MapPin className="w-4 h-4 text-cyan-400" />
          {t('floodRiskDistrictDetails')}
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-dark-400 border-b border-dark-700">
                <th className="text-left py-2 px-3 font-medium">{t('districtsMonitored')}</th>
                <th className="text-left py-2 px-3 font-medium">{t('floodRisk')}</th>
                <th className="text-left py-2 px-3 font-medium">{t('annualFloodDays')}</th>
                <th className="text-left py-2 px-3 font-medium">{t('historicalEventsLabel')}</th>
                <th className="text-left py-2 px-3 font-medium">Live discharge</th>
                <th className="text-left py-2 px-3 font-medium">{t('riverSystems')}</th>
              </tr>
            </thead>
            <tbody>
              {data.map((d, i) => (
                <tr key={i} className="border-b border-dark-800 hover:bg-dark-800/30">
                  <td className="py-2 px-3 text-white font-medium">{d.district}</td>
                  <td className="py-2 px-3">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 rounded-full bg-dark-700">
                        <div className="h-2 rounded-full" style={{ width: `${d.flood_risk_score}%`, background: RISK_COLOR(d.flood_risk_score) }} />
                      </div>
                      <span className="text-white">{d.flood_risk_score}</span>
                    </div>
                  </td>
                  <td className="py-2 px-3 text-cyan-400">{d.annual_flood_days}</td>
                  <td className="py-2 px-3 text-orange-400">{d.historical_events}</td>
                  <td className="py-2 px-3 text-blue-300 text-xs">
                    {d.live_discharge?.river_discharge_today != null
                      ? `${d.live_discharge.river_discharge_today} ${d.live_discharge.river_discharge_unit}`
                      : 'Fallback'}
                  </td>
                  <td className="py-2 px-3 text-dark-300 text-xs">{d.river_systems.join(', ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
