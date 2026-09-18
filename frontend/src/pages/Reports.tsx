import { useEffect, useState, useCallback, useRef } from 'react';
import { getReports, submitReport, verifyReport, dismissReport, getReportAttachment, getAlertWebSocketUrl, Report } from '../services/api';
import { useAuth } from '../App';
import { t, getCurrentLanguage } from '../i18n/translations';
import {
  FileText, MapPin, CheckCircle, Clock, Send, XCircle,
} from 'lucide-react';

const REPORT_TYPE_KEYS = [
  { value: 'crack', labelKey: 'crack', icon: '🔍' },
  { value: 'slope_movement', labelKey: 'slopeMovement', icon: '⛰️' },
  { value: 'blocked_road', labelKey: 'blockedRoad', icon: '🛣️' },
  { value: 'flooding', labelKey: 'flooding', icon: '🌊' },
  { value: 'other', labelKey: 'other', icon: '📌' },
];

export default function Reports() {
  const { user } = useAuth();
  const canVerify = user?.role === 'admin';
  const canDismiss = user && ['admin', 'field_officer', 'district_admin'].includes(user.role);
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [error, setError] = useState('');
  const [actionFeedback, setActionFeedback] = useState<{id: number; type: 'success' | 'error'; message: string} | null>(null);
  const resetTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Clean up timer on unmount
  useEffect(() => {
    return () => { if (resetTimer.current) clearTimeout(resetTimer.current); };
  }, []);

  // Clear action feedback after 3s
  useEffect(() => {
    if (actionFeedback) {
      const t = setTimeout(() => setActionFeedback(null), 3000);
      return () => clearTimeout(t);
    }
  }, [actionFeedback]);

  // Form state
  const [formType, setFormType] = useState('crack');
  const [formDesc, setFormDesc] = useState('');
  const [formLat, setFormLat] = useState('');
  const [formLng, setFormLng] = useState('');
  const [formName, setFormName] = useState('');
  const [formPhone, setFormPhone] = useState('');
  const [formAttachment, setFormAttachment] = useState<File | null>(null);

  const fetchReports = useCallback(async () => {
    try {
      const params = statusFilter !== 'all' ? { status: statusFilter } : {};
      const res = await getReports(params);
      setReports(res.data);
    } catch (e) {
      console.error('Reports fetch error:', e);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  const handleVerify = async (id: number) => {
    try {
      await verifyReport(id);
      setActionFeedback({ id, type: 'success', message: t('reportVerified') });
      fetchReports();
    } catch (e: any) {
      const msg = e.response?.data?.detail || t('verifyFailed');
      setActionFeedback({ id, type: 'error', message: msg });
    }
  };

  const handleDismiss = async (id: number) => {
    try {
      await dismissReport(id);
      setActionFeedback({ id, type: 'success', message: t('reportDismissed') });
      fetchReports();
    } catch (e: any) {
      const msg = e.response?.data?.detail || t('dismissFailed');
      setActionFeedback({ id, type: 'error', message: msg });
    }
  };

  const handleOpenAttachment = async (id: number) => {
    try {
      const response = await getReportAttachment(id);
      const url = URL.createObjectURL(response.data);
      window.open(url, '_blank', 'noopener,noreferrer');
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'Unable to open attachment.';
      setActionFeedback({ id, type: 'error', message: msg });
    }
  };

  useEffect(() => {
    fetchReports();
    const interval = setInterval(fetchReports, 30000);
    return () => clearInterval(interval);
  }, [fetchReports]);

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
          if (message.type === 'report.created' || message.type === 'report.updated') {
            fetchReports();
          }
        } catch {
          // Polling/manual refresh remains available if a frame is malformed.
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
  }, [fetchReports]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formAttachment && formAttachment.size > 10 * 1024 * 1024) {
      setError('Attachment must be 10 MB or smaller.');
      return;
    }
    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('report_type', formType);
      formData.append('description', formDesc);
      formData.append('latitude', formLat || '25.5');
      formData.append('longitude', formLng || '92.5');
      if (formName) formData.append('reporter_name', formName);
      if (formPhone) formData.append('reporter_phone', formPhone);
      if (formAttachment) formData.append('attachment', formAttachment);
      formData.append('reporter_language', getCurrentLanguage());

      await submitReport(formData);
      setSuccess(true);
      setError('');
      resetTimer.current = setTimeout(() => {
        setShowForm(false);
        setSuccess(false);
        setFormDesc('');
        setFormLat('');
        setFormLng('');
        setFormName('');
        setFormPhone('');
        setFormAttachment(null);
        fetchReports();
      }, 2000);
    } catch (e) {
      console.error('Submit error:', e);
      setError(t('submitError'));
    } finally {
      setSubmitting(false);
    }
  };

  const stats = {
    total: reports.length,
    pending: reports.filter(r => r.status === 'pending').length,
    verified: reports.filter(r => r.status === 'verified').length,
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <FileText className="w-6 h-6 text-blue-400" />
            {t('reports')}
          </h1>
          <p className="text-dark-400 text-sm mt-1">{t('reportsSubtitle')}</p>
        </div>
        <button
          onClick={() => { setShowForm(!showForm); setError(''); }}
          className="px-4 py-2 rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 text-white text-sm font-medium hover:from-green-500 hover:to-emerald-500 transition-all flex items-center gap-2"
        >
          <Send className="w-4 h-4" />
          {t('submitReport')}
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: t('totalReports'), value: stats.total, icon: FileText, color: 'from-blue-500 to-cyan-500' },
          { label: t('pendingReview'), value: stats.pending, icon: Clock, color: 'from-amber-500 to-yellow-500' },
          { label: t('verified'), value: stats.verified, icon: CheckCircle, color: 'from-green-500 to-emerald-500' },
        ].map((card, i) => (
          <div key={i} className="glass rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                <card.icon className="w-4 h-4 text-white" />
              </div>
            </div>
            <p className="text-2xl font-bold text-white">{card.value}</p>
            <p className="text-xs text-dark-400">{card.label}</p>
          </div>
        ))}
      </div>

      {/* Submit Report Form */}
      {showForm && (
        <div className="glass rounded-xl p-6 border border-green-600/20">
          {success ? (
            <div className="text-center py-8">
              <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
              <p className="text-lg font-semibold text-white">{t('reportSubmitted')}</p>
              <p className="text-dark-400 text-sm mt-1">{t('reportThankYou')}</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <h3 className="text-lg font-semibold text-white mb-2">📝 {t('newReport')}</h3>

              {error && (
                <div className="bg-red-600/10 border border-red-600/30 rounded-lg px-4 py-2 text-sm text-red-400">
                  {error}
                </div>
              )}

              {/* Report Type */}
              <div>
                <label className="text-xs text-dark-400 mb-1 block">{t('reportType')} *</label>
                <div className="grid grid-cols-5 gap-2">
                  {REPORT_TYPE_KEYS.map((type) => (
                    // NOTE: t() is called at render time, not module load time
                    <button
                      key={type.value}
                      type="button"
                      onClick={() => setFormType(type.value)}
                      className={`p-2 rounded-lg text-xs font-medium transition-all ${
                        formType === type.value
                          ? 'bg-green-600/20 text-green-400 border border-green-600/30'
                          : 'bg-dark-800 text-dark-400 border border-dark-700 hover:text-white'
                      }`}
                    >
                      <span className="block text-lg mb-1">{type.icon}</span>
                      {t(type.labelKey)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="text-xs text-dark-400 mb-1 block">{t('description')} *</label>
                <textarea
                  value={formDesc}
                  onChange={(e) => setFormDesc(e.target.value)}
                  placeholder={t('reportDescription')}
                  required
                  rows={3}
                  className="w-full px-4 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm placeholder-dark-500 focus:outline-none focus:border-green-600/50 transition-all"
                />
              </div>

              {/* Location */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-dark-400 mb-1 block">{t('latitude')} *</label>
                  <input
                    type="number"
                    step="any"
                    value={formLat}
                    onChange={(e) => setFormLat(e.target.value)}
                    placeholder="25.5788"
                    required
                    className="w-full px-4 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm placeholder-dark-500 focus:outline-none focus:border-green-600/50 transition-all"
                  />
                </div>
                <div>
                  <label className="text-xs text-dark-400 mb-1 block">{t('longitude')} *</label>
                  <input
                    type="number"
                    step="any"
                    value={formLng}
                    onChange={(e) => setFormLng(e.target.value)}
                    placeholder="91.8933"
                    required
                    className="w-full px-4 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm placeholder-dark-500 focus:outline-none focus:border-green-600/50 transition-all"
                  />
                </div>
              </div>

              {/* Reporter Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-dark-400 mb-1 block">{t('reporterName')}</label>
                  <input
                    type="text"
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    placeholder="John Doe"
                    className="w-full px-4 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm placeholder-dark-500 focus:outline-none focus:border-green-600/50 transition-all"
                  />
                </div>
                <div>
                  <label className="text-xs text-dark-400 mb-1 block">{t('reporterPhone')}</label>
                  <input
                    type="tel"
                    value={formPhone}
                    onChange={(e) => setFormPhone(e.target.value)}
                    placeholder="+91 9876543210"
                    className="w-full px-4 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm placeholder-dark-500 focus:outline-none focus:border-green-600/50 transition-all"
                  />
                </div>
              </div>

              {/* Evidence attachment */}
              <div>
                <label className="text-xs text-dark-400 mb-1 block">Photo / video evidence</label>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp,video/mp4,video/webm"
                  onChange={(e) => setFormAttachment(e.target.files?.[0] || null)}
                  className="w-full px-3 py-2 rounded-lg bg-dark-800 border border-dark-700 text-dark-300 text-xs file:mr-3 file:px-3 file:py-1.5 file:rounded-md file:border-0 file:bg-green-600/20 file:text-green-400"
                />
                <p className="text-[10px] text-dark-500 mt-1">JPEG, PNG, WebP, MP4 or WebM · max 10 MB</p>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 text-white text-sm font-medium hover:from-green-500 hover:to-emerald-500 transition-all disabled:opacity-50 flex items-center gap-2"
                >
                  {submitting ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                  {submitting ? t('submitting') : t('submit')}
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-6 py-2.5 rounded-xl bg-dark-800 text-dark-400 text-sm font-medium border border-dark-700 hover:text-white transition-all"
                >
                  {t('cancel')}
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      {/* Filter */}
      <div className="flex gap-2">
        {[{ value: 'all', labelKey: 'filterAll' }, { value: 'pending', labelKey: 'filterPending' }, { value: 'verified', labelKey: 'filterVerified' }, { value: 'dismissed', labelKey: 'filterDismissed' }].map(({ value, labelKey }) => (
          <button
            key={value}
            onClick={() => setStatusFilter(value)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              statusFilter === value
                ? 'bg-green-600/20 text-green-400 border border-green-600/30'
                : 'bg-dark-800 text-dark-400 border border-dark-700 hover:text-white'
            }`}
          >
            {t(labelKey)}
          </button>
        ))}
      </div>

      {/* Reports List */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : reports.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 text-dark-600 mx-auto mb-3" />            <p className="text-dark-400">{t('noReports')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {reports.map((report) => (
            <div key={report.id} className="glass rounded-xl p-4 border border-dark-700 hover:border-dark-600 transition-all">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">
                    {REPORT_TYPE_KEYS.find(rt => rt.value === report.report_type)?.icon || '📌'}
                  </span>
                  <div>
                    <h4 className="text-sm font-semibold text-white capitalize">{t(REPORT_TYPE_KEYS.find(rt => rt.value === report.report_type)?.labelKey || 'other')}</h4>
                    <p className="text-xs text-dark-400">{report.reporter_name || t('anonymous')}</p>
                  </div>
                </div>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                  report.status === 'verified' ? 'bg-green-600/10 text-green-400 border border-green-600/20' :
                  report.status === 'pending' ? 'bg-amber-600/10 text-amber-400 border border-amber-600/20' :
                  'bg-dark-700 text-dark-400 border border-dark-600'
                }`}>
                  {report.status === 'pending' ? t('statusPending') : report.status === 'verified' ? t('statusVerified') : t('statusDismissed')}
                </span>
              </div>
              <p className="text-sm text-dark-300 mb-2">{report.description}</p>
              {report.attachment_filename && (
                <button
                  onClick={() => handleOpenAttachment(report.id)}
                  className="mb-2 px-2.5 py-1.5 rounded-lg bg-blue-600/10 text-blue-400 border border-blue-600/20 text-xs hover:bg-blue-600/20 transition-all"
                >
                  View evidence
                </button>
              )}
              <div className="flex items-center gap-3 text-xs text-dark-400">
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {report.latitude?.toFixed(4) ?? '-'}, {report.longitude?.toFixed(4) ?? '-'}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date(report.created_at).toLocaleString()}
                </span>
              </div>
              {report.status === 'pending' && (
                <div className="flex gap-2 mt-3">
                  {canVerify && (
                    <button
                      onClick={() => handleVerify(report.id)}
                      className="px-3 py-1.5 rounded-lg bg-green-600/20 text-green-400 border border-green-600/30 text-xs font-medium hover:bg-green-600/30 transition-all"
                    >
                      <CheckCircle className="w-3 h-3 inline mr-1" />
                      {t('verify')}
                    </button>
                  )}
                  {canDismiss && (
                    <button
                      onClick={() => handleDismiss(report.id)}
                      className="px-3 py-1.5 rounded-lg bg-red-600/20 text-red-400 border border-red-600/30 text-xs font-medium hover:bg-red-600/30 transition-all"
                    >
                      <XCircle className="w-3 h-3 inline mr-1" />
                      {t('dismiss')}
                    </button>
                  )}
                </div>
              )}
              {actionFeedback?.id === report.id && (
                <div className={`mt-2 px-3 py-1.5 rounded-lg text-xs font-medium ${
                  actionFeedback.type === 'success'
                    ? 'bg-green-600/10 text-green-400 border border-green-600/20'
                    : 'bg-red-600/10 text-red-400 border border-red-600/20'
                }`}>
                  {actionFeedback.type === 'success' ? '✓' : '✗'} {actionFeedback.message}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
