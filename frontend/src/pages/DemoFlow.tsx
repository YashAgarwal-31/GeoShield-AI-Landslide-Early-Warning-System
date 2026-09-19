import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  simulateLandslide,
  resetSimulation,
  getDashboardStats,
  getMLHealth,
  getReadiness,
  DashboardStats,
  MLHealth,
  ReadinessResponse,
  SimulationResult,
} from '../services/api';
import { t } from '../i18n/translations';
import {
  Play, RotateCcw, Zap, AlertTriangle, CheckCircle, ChevronRight,
  Shield, Map, Bell, Radio, Activity, Target, Rocket, Eye,
} from 'lucide-react';

const getDemoSteps = () => [
  { id: 1, title: t('dashboard'), description: t('initializing'), icon: Activity, route: '/', color: 'from-blue-500 to-cyan-500', tip: t('riskDistribution') },
  { id: 2, title: t('map'), description: t('riskLegend'), icon: Map, route: '/map', color: 'from-green-500 to-emerald-500', tip: t('roadsLegend') },
  { id: 3, title: t('riskScore'), description: t('enterLocation'), icon: Target, route: '/map', color: 'from-purple-500 to-violet-500', tip: t('autoSelectHighRisk') },
  { id: 4, title: t('simulateLandslide'), description: t('simulateLandslideDesc'), icon: Zap, route: '/simulator', color: 'from-red-500 to-orange-500', tip: t('triggerCriticalEvent') },
  { id: 5, title: t('earlyWarning'), description: t('earlyWarningSubtitle'), icon: Bell, route: '/alerts', color: 'from-amber-500 to-yellow-500', tip: t('comparativeRisk') },
  { id: 6, title: t('satellite'), description: 'Cached satellite-derived snapshot', icon: Eye, route: '/satellite', color: 'from-teal-500 to-cyan-500', tip: 'Explain the cached/stale badge and observation timestamp' },
  { id: 7, title: t('aiRiskAssessment'), description: t('aiRiskRuns'), icon: Shield, route: '/station/NER-011', color: 'from-indigo-500 to-blue-500', tip: t('recommendation') },
  { id: 8, title: t('languageLabel'), description: t('liveMonitoring'), icon: Radio, route: '/', color: 'from-pink-500 to-rose-500', tip: t('demoModeLabel') },
];

export default function DemoFlow() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [simLoading, setSimLoading] = useState(false);
  const [runtimeStats, setRuntimeStats] = useState<DashboardStats | null>(null);
  const [mlHealth, setMlHealth] = useState<MLHealth | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [runtimeError, setRuntimeError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const loadRuntimeVerification = async () => {
      try {
        const [dashboardResponse, mlResponse, readinessResponse] = await Promise.all([
          getDashboardStats(),
          getMLHealth(),
          getReadiness(),
        ]);
        if (!active) return;
        setRuntimeStats(dashboardResponse.data);
        setMlHealth(mlResponse.data);
        setReadiness(readinessResponse.data);
        setRuntimeError(null);
      } catch (error: any) {
        if (!active) return;
        setRuntimeError(
          error.response?.data?.detail || 'Runtime verification data is unavailable.'
        );
      }
    };

    loadRuntimeVerification();
    return () => {
      active = false;
    };
  }, []);

  const handleRunDemo = async () => {
    setSimLoading(true);
    try {
      const res = await simulateLandslide({ station_id: 'NER-011', intensity: 'critical' });
      setSimResult(res.data);
    } catch (e) {
      console.error('Demo simulation error:', e);
    } finally {
      setSimLoading(false);
    }
  };

  const handleReset = async () => {
    try {
      await resetSimulation();
      setSimResult(null);
    } catch (e) {
      console.error('Reset error:', e);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-green-600/10 border border-green-600/20 text-green-400 text-xs font-medium mb-4">
          <Rocket className="w-3 h-3" />
          {t('sihDemoFlow')}
        </div>
        <h1 className="text-3xl font-bold text-white mb-2">
          GeoShield <span className="text-green-400">{t('liveDemo')}</span>
        </h1>
        <p className="text-dark-400 max-w-2xl mx-auto">
          {t('stepByStepWalkthrough')}
        </p>
      </div>

      {/* Quick Actions */}
      <div className="flex justify-center gap-4">
        <button
          onClick={handleRunDemo}
          disabled={simLoading}
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-red-500 to-orange-500 text-white font-bold flex items-center gap-2 hover:shadow-lg hover:shadow-red-600/20 transition-all disabled:opacity-50"
        >
          {simLoading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Zap className="w-4 h-4" />
          )}
          {t('runLiveSimulation')}
        </button>
        <button
          onClick={handleReset}
          className="px-6 py-3 rounded-xl bg-dark-800 border border-dark-600 text-dark-300 font-medium flex items-center gap-2 hover:text-white transition-all"
        >
          <RotateCcw className="w-4 h-4" />
          {t('resetDemo')}
        </button>
      </div>

      {/* Simulation Result */}
      {simResult && (
        <div className="glass rounded-xl p-6 border border-red-600/30 bg-red-600/5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-red-600/20 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <h3 className="font-bold text-white">{t('simulationCompleteCriticalEvent')}</h3>
              <p className="text-xs text-dark-400">{simResult.simulation.station.name} • {simResult.simulation.station.district}</p>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-red-400">{simResult.risk_assessment.risk_score}/100</p>
              <p className="text-xs text-dark-400">{t('riskScore')}</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-orange-400">{(simResult.risk_assessment.landslide_probability * 100).toFixed(0)}%</p>
              <p className="text-xs text-dark-400">{t('probability')}</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-amber-400">{simResult.simulation.sensor_reading.rainfall_mm}mm</p>
              <p className="text-xs text-dark-400">{t('rainfallSpike')}</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-white">{simResult.risk_assessment.time_window_hours}h</p>
              <p className="text-xs text-dark-400">{t('timeWindow')}</p>
            </div>
          </div>
          {simResult.alert && (
            <div className="mt-4 p-3 bg-amber-600/10 border border-amber-600/20 rounded-lg">
              <p className="text-sm text-amber-300">🔔 {t('alertGeneratedLabel')}: <strong>{simResult.alert.title}</strong></p>
              <p className="text-xs text-dark-400 mt-1">Affected population: {simResult.alert.affected_population.toLocaleString()}</p>
            </div>
          )}
          <p className="text-xs text-dark-300 mt-3 leading-relaxed">📋 {simResult.risk_assessment.recommendation}</p>
        </div>
      )}

      {/* Demo Steps */}
      <div className="space-y-3">
        {getDemoSteps().map((step, idx) => {
          const isActive = activeStep === step.id;
          const StepIcon = step.icon;
          return (
            <div
              key={step.id}
              className={`glass rounded-xl border transition-all cursor-pointer ${
                isActive ? 'border-green-600/50 scale-[1.01]' : 'border-dark-700 hover:border-dark-600'
              }`}
              onClick={() => setActiveStep(isActive ? 0 : step.id)}
            >
              <div className="p-4 flex items-center gap-4">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${step.color} flex items-center justify-center flex-shrink-0`}>
                  <span className="text-white font-bold text-sm">{step.id}</span>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-white flex items-center gap-2">
                    <StepIcon className="w-4 h-4" />
                    {step.title}
                  </h3>
                  <p className="text-xs text-dark-400 mt-0.5">{step.description}</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(step.route);
                  }}
                  className="px-3 py-1.5 rounded-lg bg-green-600/20 text-green-400 border border-green-600/30 text-xs font-medium hover:bg-green-600/30 transition-all flex items-center gap-1 flex-shrink-0"
                >
                  {t('go')} <ChevronRight className="w-3 h-3" />
                </button>
              </div>
              {isActive && (
                <div className="px-4 pb-4 pt-0 ml-14">
                  <div className="p-3 bg-green-600/5 border border-green-600/10 rounded-lg">
                    <p className="text-xs text-green-300 flex items-center gap-1">
                      💡 <strong>{t('demoTip')}:</strong> {step.tip}
                    </p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Runtime verification — values are loaded from the running backend. */}
      <div className="glass rounded-xl p-6">
        <h3 className="text-sm font-bold text-white mb-2">Runtime Verification</h3>
        <p className="text-xs text-dark-400 mb-4">
          These values come from the live application APIs; unsupported latency or accuracy claims are not shown here.
        </p>
        {runtimeError && (
          <div className="mb-4 rounded-lg border border-red-600/30 bg-red-600/10 px-3 py-2 text-xs text-red-300">
            {runtimeError}
          </div>
        )}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            {
              label: 'System readiness',
              value: readiness?.status?.toUpperCase() || 'CHECKING',
              sub: readiness ? `DB: ${readiness.database}` : 'Backend status',
            },
            {
              label: 'ML runtime',
              value: mlHealth?.model_loaded ? 'XGBOOST' : 'FALLBACK',
              sub: mlHealth?.training_source || 'Checking model',
            },
            {
              label: t('trainingSamples'),
              value: mlHealth ? mlHealth.training_samples.toLocaleString() : '—',
              sub: mlHealth?.training_source || 'Runtime provenance',
            },
            {
              label: t('monitoredStations'),
              value: runtimeStats ? runtimeStats.total_stations.toString() : '—',
              sub: runtimeStats ? `${runtimeStats.active_stations} active` : 'Runtime database',
            },
            {
              label: 'Active alerts',
              value: runtimeStats ? runtimeStats.active_alerts.toString() : '—',
              sub: 'Persistent alert workflow',
            },
            {
              label: 'Pending reports',
              value: runtimeStats ? runtimeStats.pending_reports.toString() : '—',
              sub: 'Citizen evidence queue',
            },
            {
              label: 'ML data',
              value: readiness?.ml_training_data || 'CHECKING',
              sub: readiness?.synthetic_model_fallback
                ? 'Synthetic fallback allowed in this profile'
                : 'Synthetic fallback disabled',
            },
            {
              label: t('languagesLabel'),
              value: '4',
              sub: 'EN, HI, BN, AS',
            },
          ].map((stat, i) => (
            <div key={i} className="text-center p-3 bg-dark-800/50 rounded-lg">
              <p className="text-xl font-bold text-white break-words">{stat.value}</p>
              <p className="text-xs text-green-400 font-medium">{stat.label}</p>
              <p className="text-[10px] text-dark-500 break-words">{stat.sub}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Tech Stack */}
      <div className="glass rounded-xl p-6">
        <h3 className="text-sm font-bold text-white mb-4">{t('technologyStack')}</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { layer: t('techBackend'), tech: 'FastAPI + SQLAlchemy + Alembic' },
            { layer: 'AI/ML', tech: 'Random Forest + Gradient Boosting' },
            { layer: t('techFrontend'), tech: 'React + Tailwind + Leaflet.js' },
            { layer: t('techCharts'), tech: 'Recharts (6 chart types)' },
            { layer: t('techAuth'), tech: 'JWT + bcrypt + RBAC' },
            { layer: t('languagesLabel'), tech: '4 languages (EN/HI/BN/AS)' },
            { layer: t('techDatabase'), tech: 'PostgreSQL / SQLite + Alembic' },
            { layer: t('techSatellite'), tech: 'Cached satellite snapshot + live weather with safe fallback' },
          ].map((item, i) => (
            <div key={i} className="p-3 bg-dark-800/50 rounded-lg">
              <p className="text-xs text-green-400 font-medium">{item.layer}</p>
              <p className="text-xs text-dark-300 mt-0.5">{item.tech}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
