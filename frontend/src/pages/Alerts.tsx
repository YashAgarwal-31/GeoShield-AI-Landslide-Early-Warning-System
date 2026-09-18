import { useEffect, useState, useCallback } from 'react';
import {
  getAlerts, acknowledgeAlert, resolveAlert, getAlertTimeline, getAlertHistory,
  getAlertWebSocketUrl, Alert as AlertType, TimelineEntry,
} from '../services/api';
import { t } from '../i18n/translations';
import { useAuth } from '../App';
import {
  AlertTriangle, CheckCircle, XCircle, Clock, Users, MapPin, Radio, Bell,
  BarChart3, List, History, ChevronRight, Activity, TrendingUp,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area,
} from 'recharts';

const RISK_STYLES: Record<string, { bg: string; border: string; text: string; icon: string }> = {
  critical: { bg: 'bg-red-600/10', border: 'border-red-600/30', text: 'text-red-400', icon: '🔴' },
  high: { bg: 'bg-orange-600/10', border: 'border-orange-600/30', text: 'text-orange-400', icon: '🟠' },
  moderate: { bg: 'bg-amber-600/10', border: 'border-amber-600/30', text: 'text-amber-400', icon: '🟡' },
  low: { bg: 'bg-green-600/10', border: 'border-green-600/30', text: 'text-green-400', icon: '🟢' },
};

const RISK_COLORS: Record<string, string> = {
  critical: '#ef4444', high: '#f97316', moderate: '#f59e0b', low: '#22c55e',
};

export default function Alerts() {
  const { user } = useAuth();
  const canAcknowledge = user && ['admin', 'field_officer', 'district_admin'].includes(user.role);
  const canResolve = user?.role === 'admin';
  const [alerts, setAlerts] = useState<AlertType[]>([]);
  const [filter, setFilter] = useState('all');
  const [riskFilter, setRiskFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'list' | 'timeline' | 'history'>('list');
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [timelineSummary, setTimelineSummary] = useState<any>(null);
  const [historyData, setHistoryData] = useState<any[]>([]);
  const [actionFeedback, setActionFeedback] = useState<{id: number; type: 'success' | 'error'; message: string} | null>(null);
  const [liveConnected, setLiveConnected] = useState(false);

  useEffect(() => {
    if (actionFeedback) {
      const t = setTimeout(() => setActionFeedback(null), 3000);
      return () => clearTimeout(t);
    }
  }, [actionFeedback]);

  const fetchAlerts = useCallback(async () => {
    try {
      const params: { status?: string } = {};
      if (filter !== 'all') params.status = filter;
      const res = await getAlerts(params);
      let data = res.data;
      if (riskFilter !== 'all') {
        data = data.filter((a: AlertType) => a.risk_level === riskFilter);
      }
      setAlerts(data);
    } catch (e) {
      console.error('Alert fetch error:', e);
    } finally {
      setLoading(false);
    }
  }, [filter, riskFilter]);

  const fetchTimeline = useCallback(async () => {
    try {
      const res = await getAlertTimeline(72);
      setTimeline(res.data.timeline);
      setTimelineSummary(res.data.summary);
    } catch (e) {
      console.error('Timeline fetch error:', e);
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await getAlertHistory(30);
      setHistoryData(res.data);
    } catch (e) {
      console.error('History fetch error:', e);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
    if (view === 'timeline') fetchTimeline();
    if (view === 'history') fetchHistory();
    const interval = setInterval(fetchAlerts, 15000);
    return () => clearInterval(interval);
  }, [fetchAlerts, fetchTimeline, fetchHistory, view]);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let stopped = false;

    const refreshCurrentView = () => {
      fetchAlerts();
      if (view === 'timeline') fetchTimeline();
      if (view === 'history') fetchHistory();
    };

    const connect = () => {
      if (stopped) return;
      try {
        socket = new WebSocket(getAlertWebSocketUrl('all'));
      } catch (error) {
        console.error('Alert WebSocket URL error:', error);
        reconnectTimer = setTimeout(connect, 3000);
        return;
      }

      socket.onopen = () => setLiveConnected(true);
      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (['alert.created', 'alert.updated', 'alerts.reset', 'sensor.reading'].includes(message.type)) {
            refreshCurrentView();
          }
        } catch (error) {
          console.error('Alert WebSocket message error:', error);
        }
      };
      socket.onerror = () => {
        socket?.close();
      };
      socket.onclose = () => {
        setLiveConnected(false);
        if (!stopped) reconnectTimer = setTimeout(connect, 3000);
      };
    };

    connect();
    return () => {
      stopped = true;
      setLiveConnected(false);
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [fetchAlerts, fetchTimeline, fetchHistory, view]);

  const handleAcknowledge = async (id: number) => {
    try {
      await acknowledgeAlert(id);
      setActionFeedback({ id, type: 'success', message: t('alertAcknowledged') });
      fetchAlerts();
    } catch (e: any) {
      const msg = e.response?.data?.detail || t('acknowledgeFailed');
      setActionFeedback({ id, type: 'error', message: msg });
    }
  };

  const handleResolve = async (id: number) => {
    try {
      await resolveAlert(id);
      setActionFeedback({ id, type: 'success', message: t('alertResolved') });
      fetchAlerts();
    } catch (e: any) {
      const msg = e.response?.data?.detail || t('resolveFailed');
      setActionFeedback({ id, type: 'error', message: msg });
    }
  };

  const stats = {
    total: alerts.length,
    critical: alerts.filter(a => a.risk_level === 'critical').length,
    high: alerts.filter(a => a.risk_level === 'high').length,
    active: alerts.filter(a => a.status === 'active').length,
  };

  return (
    <div className="p-3 sm:p-6 space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
            <Bell className="w-5 h-5 sm:w-6 sm:h-6 text-red-400" />
            {t('alerts')}
          </h1>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-dark-400 text-xs sm:text-sm">{t('earlyWarningSubtitle')}</p>
            <span className={`inline-flex items-center gap-1 text-[10px] ${liveConnected ? 'text-green-400' : 'text-amber-400'}`}>
              <Radio className="w-3 h-3" />
              {liveConnected ? 'LIVE' : 'POLLING'}
            </span>
          </div>
        </div>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {[
            { key: 'list', icon: List, label: t('alerts') },
            { key: 'timeline', icon: Clock, label: t('timeline') },
            { key: 'history', icon: History, label: t('thirtyDayTrend') },
          ].map(({ key, icon: Icon, label }) => (
            <button
              key={key}
              onClick={() => setView(key as any)}
              className={`px-3 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-1 whitespace-nowrap min-h-[40px] ${
                view === key
                  ? 'bg-green-600/20 text-green-400 border border-green-600/30'
                  : 'bg-dark-800 text-dark-400 border border-dark-700 hover:text-white'
              }`}
            >
              <Icon className="w-3 h-3" /> {label}
            </button>
          ))}
        </div>
      </div>

      {/* Alert Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        {[
          { label: t('totalAlerts'), value: stats.total, icon: Bell, color: 'from-blue-500 to-cyan-500' },
          { label: t('active'), value: stats.active, icon: Radio, color: stats.active > 0 ? 'from-red-500 to-orange-500' : 'from-green-500 to-emerald-500', pulse: stats.active > 0 },
          { label: t('criticalLevelShort'), value: stats.critical, icon: AlertTriangle, color: 'from-red-600 to-red-500' },
          { label: t('highRiskLabel'), value: stats.high, icon: AlertTriangle, color: 'from-orange-500 to-amber-500' },
        ].map((card, i) => (
          <div key={i} className={`glass rounded-xl p-3 sm:p-4 ${card.pulse ? 'pulse-alert' : ''}`}>
            <div className="flex items-center gap-2 mb-1 sm:mb-2">
              <div className={`w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                <card.icon className="w-3 h-3 sm:w-4 sm:h-4 text-white" />
              </div>
            </div>
            <p className="text-xl sm:text-2xl font-bold text-white">{card.value}</p>
            <p className="text-[10px] sm:text-xs text-dark-400">{card.label}</p>
          </div>
        ))}
      </div>

      {/* LIST VIEW */}
      {view === 'list' && (
        <>
          {/* Filters */}
          <div className="flex flex-col gap-3">
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex gap-2 overflow-x-auto pb-1">
                <span className="text-xs text-dark-400 self-center whitespace-nowrap">{t('filterByStatus')}:</span>
                {['all', 'active', 'acknowledged', 'resolved'].map((status) => (
                  <button
                    key={status}
                    onClick={() => setFilter(status)}
                    className={`px-3 py-2 rounded-lg text-xs font-medium transition-all whitespace-nowrap min-h-[40px] ${
                      filter === status
                        ? 'bg-green-600/20 text-green-400 border border-green-600/30'
                        : 'bg-dark-800 text-dark-400 border border-dark-700 hover:text-white'
                    }`}
                  >
                    {status === 'all' ? t('all') : status === 'active' ? t('active') : status === 'acknowledged' ? t('acknowledged') : t('resolved')}
                  </button>
                ))}
              </div>
              <div className="flex gap-2 overflow-x-auto pb-1">
                <span className="text-xs text-dark-400 self-center whitespace-nowrap">{t('filterByRisk')}:</span>
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
          </div>

          {/* Alert List */}
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : alerts.length === 0 ? (
            <div className="text-center py-12">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
              <p className="text-dark-400">{t('noAlertsFound')}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {alerts.map((alert) => {
                const style = RISK_STYLES[alert.risk_level] || RISK_STYLES.low;
                return (
                   <div
                     key={alert.id}
                     className={`glass rounded-xl p-3 sm:p-5 border ${style.border} ${style.bg} transition-smooth`}
                   >
                     <div className="flex flex-col gap-3">
                       <div className="flex items-start gap-3">
                         <span className="text-base sm:text-lg">{style.icon}</span>
                         <div className="flex-1 min-w-0">
                           <h3 className="font-semibold text-white text-sm sm:text-base">{alert.title}</h3>
                           <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-dark-400 mt-1">
                             <span className={`px-1.5 py-0.5 rounded-full ${style.bg} ${style.text} font-medium border ${style.border}`}>
                               {alert.risk_level.toUpperCase()}
                             </span>
                             <span className="flex items-center gap-1">
                               <Clock className="w-3 h-3" />
                               {new Date(alert.created_at).toLocaleString()}
                             </span>
                             <span className="flex items-center gap-1">
                               <MapPin className="w-3 h-3" />
                               {alert.station_id}
                             </span>
                             {alert.affected_population > 0 && (
                               <span className="flex items-center gap-1">
                                 <Users className="w-3 h-3" />
                                 {alert.affected_population.toLocaleString()} {t('people')}
                               </span>
                             )}
                           </div>
                         </div>
                       </div>

                       <p className="text-xs sm:text-sm text-dark-300 ml-0 sm:ml-8">{alert.message}</p>

                       {/* Actions */}
                       <div className="flex flex-wrap items-center gap-2 ml-0 sm:ml-8">
                        {alert.status === 'active' && canAcknowledge && (
                          <>
                            <button
                              onClick={() => handleAcknowledge(alert.id)}
                              className="px-3 py-1.5 rounded-lg bg-amber-600/20 text-amber-400 border border-amber-600/30 text-xs font-medium hover:bg-amber-600/30 transition-all"
                            >
                              <CheckCircle className="w-3 h-3 inline mr-1" />
                              {t('acknowledge')}
                            </button>
                            {canResolve && (
                              <button
                                onClick={() => handleResolve(alert.id)}
                                className="px-3 py-1.5 rounded-lg bg-green-600/20 text-green-400 border border-green-600/30 text-xs font-medium hover:bg-green-600/30 transition-all"
                              >
                                <XCircle className="w-3 h-3 inline mr-1" />
                                {t('resolve')}
                              </button>
                            )}
                          </>
                        )}
                        {alert.status === 'acknowledged' && (
                          <span className="px-3 py-1.5 rounded-lg bg-amber-600/10 text-amber-400 border border-amber-600/20 text-xs font-medium">
                            ⏳ {t('acknowledged')}
                          </span>
                        )}
                        {alert.status === 'resolved' && (
                          <span className="px-3 py-1.5 rounded-lg bg-green-600/10 text-green-400 border border-green-600/20 text-xs font-medium">
                            ✅ {t('resolved')}
                          </span>                        )}
                      </div>
                      {actionFeedback?.id === alert.id && (
                        <div className={`w-full mt-2 px-3 py-1.5 rounded-lg text-xs font-medium ${
                          actionFeedback.type === 'success'
                            ? 'bg-green-600/10 text-green-400 border border-green-600/20'
                            : 'bg-red-600/10 text-red-400 border border-red-600/20'
                        }`}>
                          {actionFeedback.type === 'success' ? '✓' : '✗'} {actionFeedback.message}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}


      {/* TIMELINE VIEW */}
      {view === 'timeline' && (
        <div className="space-y-4">
          {timelineSummary && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div className="glass rounded-xl p-3 text-center">
                <p className="text-xl font-bold text-white">{timelineSummary.total_alerts}</p>
                <p className="text-xs text-dark-400">{t('totalAlerts')} (72h)</p>
              </div>
              <div className="glass rounded-xl p-3 text-center">
                <p className="text-xl font-bold text-red-400">{timelineSummary.critical_count}</p>
                <p className="text-xs text-dark-400">{t('criticalLevelShort')}</p>
              </div>
              <div className="glass rounded-xl p-3 text-center">
                <p className="text-xl font-bold text-orange-400">{timelineSummary.high_count}</p>
                <p className="text-xs text-dark-400">{t('highRiskLabel')}</p>
              </div>
              <div className="glass rounded-xl p-3 text-center">
                <p className="text-xl font-bold text-amber-400">{timelineSummary.moderate_count}</p>
                <p className="text-xs text-dark-400">{t('moderateRisk')}</p>
              </div>
              <div className="glass rounded-xl p-3 text-center">
                <p className="text-xl font-bold text-white">{timelineSummary.total_affected_population?.toLocaleString()}</p>
                <p className="text-xs text-dark-400">{t('peopleAffected')}</p>
              </div>
            </div>
          )}
          {timeline.length === 0 ? (
            <div className="text-center py-12">
              <Clock className="w-12 h-12 text-dark-500 mx-auto mb-3" />
              <p className="text-dark-400">{t('noData')}</p>
            </div>
          ) : (
            <div className="relative pl-8">
              {/* Timeline line */}
              <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-dark-700" />
              {timeline.map((entry, idx) => {
                const style = RISK_STYLES[entry.max_risk] || RISK_STYLES.low;
                return (
                  <div key={idx} className="relative mb-6">
                    {/* Timeline dot */}
                    <div className={`absolute -left-6 top-2 w-4 h-4 rounded-full border-2 ${
                      entry.max_risk === 'critical' ? 'bg-red-500 border-red-400' :
                      entry.max_risk === 'high' ? 'bg-orange-500 border-orange-400' :
                      entry.max_risk === 'moderate' ? 'bg-amber-500 border-amber-400' :
                      'bg-green-500 border-green-400'
                    }`} />
                    <div className={`glass rounded-xl p-4 border ${style.border}`}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-white">{entry.timestamp}</span>
                          <span className="text-xs text-dark-400">• {entry.alerts.length} alerts</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${style.bg} ${style.text} border ${style.border}`}>
                            {entry.max_risk.toUpperCase()}
                          </span>
                          <span className="text-xs text-dark-400">
                            👥 {entry.total_affected.toLocaleString()} {t('peopleAffected')}
                          </span>
                        </div>
                      </div>
                      <div className="space-y-1">
                        {entry.alerts.map((alert, ai) => (
                          <div key={ai} className="flex items-center gap-2 text-xs">
                            <span>{RISK_STYLES[alert.risk_level]?.icon}</span>
                            <span className="text-dark-300">{alert.title}</span>
                            <span className="text-dark-500">({alert.station_id})</span>
                            {alert.status === 'resolved' && <CheckCircle className="w-3 h-3 text-green-400" />}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* HISTORY / TREND VIEW */}
      {view === 'history' && (
        <div className="space-y-6">
          <div className="glass rounded-xl p-6">
            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-green-400" />
              {t('thirtyDayTrend')}
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={historyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#fff' }}
                />
                <Area type="monotone" dataKey="critical" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} name={t('criticalRisk')} />
                <Area type="monotone" dataKey="high" stackId="1" stroke="#f97316" fill="#f97316" fillOpacity={0.3} name={t('highRisk')} />
                <Area type="monotone" dataKey="moderate" stackId="1" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.3} name={t('moderateRisk')} />
                <Area type="monotone" dataKey="low" stackId="1" stroke="#22c55e" fill="#22c55e" fillOpacity={0.3} name={t('lowRisk')} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="glass rounded-xl p-6">
            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blue-400" />
              {t('dailyAlertCount')}
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={historyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#fff' }}
                />
                <Bar dataKey="total" fill="#3b82f6" radius={[4, 4, 0, 0]} name={t('totalAlerts')} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
