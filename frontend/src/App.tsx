import { HashRouter as Router, Routes, Route, NavLink, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { useState, useEffect, createContext, useContext } from 'react';
import { t, setLanguage, getCurrentLanguage, Language, languages } from './i18n/translations';
import { loginAPI, setStoredToken, clearStoredToken, getStoredToken, getAlertStats, getReadiness, getAlertWebSocketUrl, getServerUrl, setServerUrl, isMobileApp, normalizeServerBase, getWebPushPublicKey, subscribeWebPush, api } from './services/api';
import Dashboard from './pages/Dashboard';
import RiskMap from './pages/RiskMap';
import Alerts from './pages/Alerts';
import Reports from './pages/Reports';
import StationDetail from './pages/StationDetail';
import Simulator from './pages/Simulator';
import SatelliteData from './pages/SatelliteData';
import DemoFlow from './pages/DemoFlow';
import FloodData from './pages/FloodData';
import Stations from './pages/Stations';
import AdminOperations from './pages/AdminOperations';
import ErrorBoundary from './components/ErrorBoundary';
import MobileFAB from './components/MobileFAB';
import {
  LayoutDashboard, Map, AlertTriangle, FileText, Globe, Shield, Radio,
  ChevronLeft, Clock, LogOut, User, Bell, Search, Activity, Mountain,
  Droplets, BarChart3, Settings, Home, TrendingUp, Building2, MapPin, Zap, Satellite, Rocket, Waves,
} from 'lucide-react';

interface AuthContextType {
  isLoggedIn: boolean;
  user: { name: string; role: string } | null;
  login: (name: string, role: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  isLoggedIn: false,
  user: null,
  login: () => {},
  logout: () => {},
});

export const useAuth = () => useContext(AuthContext);

function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [apiUrl, setApiUrl] = useState('');
  const [serverInput, setServerInput] = useState('');
  const [showServerSettings, setShowServerSettings] = useState(false);
  const [needsServer, setNeedsServer] = useState(false);

  useEffect(() => {
    const saved = getServerUrl();
    const mobile = isMobileApp();
    const pageIsHttp = window.location.protocol === 'http:' || window.location.protocol === 'https:';

    if (saved) {
      const normalized = normalizeServerBase(saved);
      setApiUrl(normalized ? `${normalized}/api` : '/api');
      setServerInput(saved);
      setNeedsServer(false);
      setShowServerSettings(false);
      return;
    }

    // Normal browser deployments use same-origin /api. A packaged mobile app
    // needs a backend address (unless adb reverse makes localhost available).
    setApiUrl(pageIsHttp && !mobile ? '/api' : 'http://localhost:8000/api');
    setServerInput('');
    const needsConfig = mobile;
    setNeedsServer(needsConfig);
    setShowServerSettings(needsConfig);
  }, []);

  const saveServerUrl = (value?: string) => {
    const raw = (value ?? serverInput).trim();
    const normalized = normalizeServerBase(raw);
    if (!normalized) return;

    localStorage.setItem('geoshield_server_url', normalized);
    setServerInput(normalized);
    setApiUrl(`${normalized}/api`);
    setNeedsServer(false);
    setShowServerSettings(false);
    setError('');
  };

  const clearServerUrl = () => {
    localStorage.removeItem('geoshield_server_url');
    setServerInput('');

    const mobile = isMobileApp();
    const pageIsHttp =
      window.location.protocol === 'http:' ||
      window.location.protocol === 'https:';

    if (pageIsHttp && !mobile) {
      setApiUrl('/api');
      setNeedsServer(false);
      setShowServerSettings(false);
      setError('Custom server URL cleared. Using the same-origin backend.');
    } else {
      setApiUrl('http://localhost:8000/api');
      setNeedsServer(true);
      setShowServerSettings(true);
      setError('Server URL cleared. Please enter a backend address.');
    }
  };

  const detectServer = async () => {
    setLoading(true);
    setError('');
    const candidates = [
      'localhost:8000',
      '127.0.0.1:8000',
      // Android emulator special host alias.
      '10.0.2.2:8000',
    ];
    
    for (const candidate of candidates) {
      try {
        const testUrl = `http://${candidate}/api/health`;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 1500);
        const res = await fetch(testUrl, { signal: controller.signal, mode: 'cors' });
        clearTimeout(timeoutId);
        if (res.ok) {
          saveServerUrl(candidate);
          setError(`Connected to server at ${candidate}`);
          setLoading(false);
          return;
        }
      } catch (e) {
        // try next
      }
    }
    
    setError('Auto-detect failed. Please enter server IP manually below.');
    setShowServerSettings(true);
    setLoading(false);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    if (!email || !password) {
      setError(t('enterCredentials'));
      setLoading(false);
      return;
    }
    try {
      const res = await loginAPI(email, password);
      setStoredToken(res.data.token);
      login(res.data.user.name, res.data.user.role);
      navigate('/');
    } catch (err: any) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      const saved = normalizeServerBase(getServerUrl());
      const currentApiUrl = saved ? `${saved}/api` : '/api';
      const isNetworkError = !err.response || status === 0 || status === undefined || err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND' || err.code === 'ERR_NETWORK';
      if (isNetworkError) {
        setError(`Cannot reach backend at ${currentApiUrl}. Check network or set Backend URL in Settings.`);
      } else if (status === 401) {
        setError(detail || 'Invalid email or password');
      } else {
        setError(detail || `Login failed (HTTP ${status || 'error'})`);
      }
      console.error('Login error:', err);
      setLoading(false);
    }
  };

  const testConnection = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/health');
      if (res.data?.status === 'healthy') {
        setError('Backend connection successful.');
      } else {
        setError('Backend responded, but health status was unexpected.');
      }
    } catch (err: any) {
      const saved = normalizeServerBase(getServerUrl());
      const currentApiUrl = saved ? `${saved}/api` : '/api';
      setError(`Cannot reach backend at ${currentApiUrl}. Check network or set Backend URL in Settings.`);
      console.error('Connection test error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Resolve the same backend origin used by the normal API client.
  const getBaseUrl = (): string => {
    const saved = getServerUrl();
    if (saved) return normalizeServerBase(saved);

    const pageIsHttp =
      window.location.protocol === 'http:' ||
      window.location.protocol === 'https:';
    if (pageIsHttp && !isMobileApp()) {
      return window.location.origin;
    }
    return '';
  };

  // XMLHttpRequest bypasses WebView CORS restrictions that block fetch()
  const xhrFetch = (url: string, timeoutMs = 5000): Promise<{status: number; contentType: string; body: string}> => {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { xhr.abort(); reject(new Error('Timeout')); }, timeoutMs);
      const xhr = new XMLHttpRequest();
      xhr.open('GET', url, true);
      xhr.timeout = timeoutMs;
      xhr.onload = () => {
        clearTimeout(timer);
        resolve({ status: xhr.status, contentType: xhr.getResponseHeader('content-type') || 'unknown', body: xhr.responseText });
      };
      xhr.onerror = () => { clearTimeout(timer); reject(new Error('Network error')); };
      xhr.ontimeout = () => { clearTimeout(timer); reject(new Error('Timeout')); };
      xhr.send();
    });
  };

  const checkHealth = async () => {
    setLoading(true);
    setError('');
    const base = getBaseUrl();
    if (!base) {
      setError('❌ Enter server IP in Settings first (e.g. 192.168.1.5:8000)');
      setShowServerSettings(true);
      setLoading(false);
      return;
    }
    const endpoints = [`${base}/health`, `${base}/api/health`];
    for (const url of endpoints) {
      try {
        const result = await xhrFetch(url);
        if (result.contentType.includes('application/json')) {
          setError(`✅ Backend reachable at ${url}! HTTP ${result.status}`);
          setLoading(false);
          return;
        }
      } catch (e) {
        continue;
      }
    }
    setError(`❌ Cannot reach backend at ${base}. Check phone is on same WiFi, no VPN, no AP isolation.`);
    setShowServerSettings(true);
    setLoading(false);
  };

  const testRaw = async () => {
    setLoading(true);
    setError('');
    const base = getBaseUrl();
    if (!base) {
      setError('❌ Enter server IP in Settings first (e.g. 192.168.1.5:8000)');
      setShowServerSettings(true);
      setLoading(false);
      return;
    }
    const endpoints = [
      `${base}/health`,
      `${base}/api/health`,
    ];
    const results: string[] = [];
    for (const url of endpoints) {
      try {
        const r = await xhrFetch(url);
        const isJson = r.contentType.includes('json');
        const icon = isJson ? '✅' : '⚠️';
        results.push(`${icon} ${url} → HTTP ${r.status} CT: ${r.contentType}\n   Body: ${r.body.slice(0, 150)}`);
      } catch (e: any) {
        results.push(`❌ ${url} → ${e.message || 'Network error'}`);
      }
    }
    const allJson = results.every(r => r.startsWith('✅'));
    const allFail = results.every(r => r.startsWith('❌'));
    const header = allJson ? '✅ All endpoints returning JSON!' : allFail ? '❌ Cannot reach any endpoint' : '⚠️ Mixed results — see details below';
    setError(`${header}\n\n${results.join('\n\n')}`);
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-green-600/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-600/5 rounded-full blur-3xl" />
      </div>
      <div className="relative w-full max-w-md">
        <div className="glass rounded-2xl p-8 border border-dark-700">
          <div className="text-center mb-8">
            <div className="mx-auto mb-4">
              <img src="/geoshield_logo.svg" alt="GeoShield Logo" className="w-20 h-20 mx-auto rounded-2xl shadow-lg shadow-green-600/20" />
            </div>
            <h1 className="text-2xl font-bold text-white">GeoShield</h1>
            <p className="text-dark-400 text-sm mt-1">AI-Based Landslide Risk Monitoring</p>
            <p className="text-dark-500 text-xs mt-0.5">North Eastern Region, India</p>
          </div>
          <form onSubmit={handleLogin} className="space-y-4">
            {needsServer && (
              <div className="bg-amber-600/10 border border-amber-600/30 rounded-xl p-3">
                <p className="text-xs text-amber-400 font-medium">⚠️ Server URL not configured. Set it below before logging in.</p>
              </div>
            )}
            {error && (
              <p className="text-xs text-red-400 bg-red-600/10 border border-red-600/20 rounded-lg px-3 py-2">{error}</p>
            )}
            <div className={`bg-dark-800/50 border rounded-xl p-3 space-y-2 ${needsServer ? 'border-amber-600/50' : 'border-dark-700'}`}>
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-dark-400 font-medium">🌐 Server Connection</span>
                <span className="text-[10px] text-dark-500">API: {apiUrl}</span>
              </div>
              <input
                type="text"
                value={serverInput}
                onChange={(e) => setServerInput(e.target.value)}
                placeholder="e.g. 192.168.1.100:8000 or 10.0.2.2:8000"
                className="w-full text-xs px-3 py-2 rounded-lg bg-dark-900 border border-dark-600 text-white placeholder-dark-500 focus:outline-none focus:border-green-600/50"
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => saveServerUrl()}
                  className="flex-1 py-1.5 rounded-lg bg-green-600/20 text-green-400 text-[11px] font-medium border border-green-600/30 hover:bg-green-600/30"
                >
                  Save & Connect
                </button>
                <button
                  type="button"
                  onClick={detectServer}
                  disabled={loading}
                  className="flex-1 py-1.5 rounded-lg bg-blue-600/20 text-blue-400 text-[11px] font-medium border border-blue-600/30 hover:bg-blue-600/30 disabled:opacity-50"
                >
                  Auto-detect
                </button>
                <button
                  type="button"
                  onClick={clearServerUrl}
                  className="px-3 py-1.5 rounded-lg bg-dark-700 text-dark-400 text-[11px] font-medium border border-dark-600 hover:text-red-400"
                >
                  Clear
                </button>
              </div>
              <p className="text-[10px] text-dark-500">
                Emulator: <span className="text-green-400">10.0.2.2:8000</span> • Physical device: use your PC's LAN IP (e.g. <span className="text-green-400">192.168.1.100:8000</span>)
              </p>
            </div>
            <div>
              <label className="text-xs text-dark-400 mb-1 block">{t('emailLabel')}</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@geoshield.gov.in"
                className="w-full px-4 py-3 rounded-xl bg-dark-800 border border-dark-700 text-white text-sm placeholder-dark-500 focus:outline-none focus:border-green-600/50 focus:ring-1 focus:ring-green-600/30 transition-all"
              />
            </div>
            <div>
              <label className="text-xs text-dark-400 mb-1 block">{t('passwordLabel')}</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t('enterPasswordPlaceholder')}
                className="w-full px-4 py-3 rounded-xl bg-dark-800 border border-dark-700 text-white text-sm placeholder-dark-500 focus:outline-none focus:border-green-600/50 focus:ring-1 focus:ring-green-600/30 transition-all"
              />
            </div>
            <button
              type="submit"
              disabled={loading || needsServer}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 text-white font-medium text-sm hover:from-green-500 hover:to-emerald-500 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Shield className="w-4 h-4" />
                  {t('signInToGeoShield')}
                </>
              )}
            </button>
            {needsServer && (
              <p className="text-[10px] text-amber-400 text-center">Configure server URL above to enable login</p>
            )}
            <div className="flex gap-2">
              <button
                type="button"
                onClick={testConnection}
                disabled={loading || needsServer}
                className="flex-1 py-2 rounded-xl bg-dark-800 text-dark-300 text-xs font-medium border border-dark-700 hover:text-white hover:border-dark-600 transition-all disabled:opacity-50"
              >
                Test Login
              </button>
              <button
                type="button"
                onClick={checkHealth}
                disabled={loading}
                className="flex-1 py-2 rounded-xl bg-dark-800 text-dark-300 text-xs font-medium border border-dark-700 hover:text-white hover:border-dark-600 transition-all disabled:opacity-50"
              >
                Check Backend
              </button>
              <button
                type="button"
                onClick={testRaw}
                disabled={loading}
                className="flex-1 py-2 rounded-xl bg-dark-800 text-dark-300 text-xs font-medium border border-dark-700 hover:text-white hover:border-dark-600 transition-all disabled:opacity-50"
              >
                Raw Test
              </button>
            </div>
          </form>
          <div className="mt-4 text-[10px] text-dark-500 text-center">
            API: {apiUrl}
          </div>
        </div>
      </div>
    </div>
  );
}

function MainLayout() {
  const [lang, setLangState] = useState<Language>(getCurrentLanguage());
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [activeAlerts, setActiveAlerts] = useState(0);
  const [systemReady, setSystemReady] = useState<boolean | null>(null);
  const [liveStreamConnected, setLiveStreamConnected] = useState(false);
  const [serverUrl, setServerUrlState] = useState(getServerUrl());
  const [pushSetupMessage, setPushSetupMessage] = useState('');
  const { user, logout } = useAuth();
  const location = useLocation();

  useEffect(() => {
    const clock = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(clock);
  }, []);

  useEffect(() => {
    const fetchAlertCount = async () => {
      try {
        const res = await getAlertStats();
        setActiveAlerts(res.data.active);
      } catch { /* polling fallback keeps the last known count */ }
    };
    fetchAlertCount();
    const interval = setInterval(fetchAlertCount, 15000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const checkReadiness = async () => {
      try {
        const res = await getReadiness();
        setSystemReady(res.data.status === 'ready' && res.data.database === 'connected');
      } catch {
        setSystemReady(false);
      }
    };
    checkReadiness();
    const interval = setInterval(checkReadiness, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let stopped = false;

    const refreshAlertCount = async () => {
      try {
        const res = await getAlertStats();
        setActiveAlerts(res.data.active);
      } catch { /* polling fallback will retry */ }
    };

    const connect = () => {
      if (stopped) return;
      try {
        socket = new WebSocket(getAlertWebSocketUrl('all'));
      } catch {
        reconnectTimer = setTimeout(connect, 3000);
        return;
      }

      socket.onopen = () => setLiveStreamConnected(true);
      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (['alert.created', 'alert.updated', 'alerts.reset'].includes(message.type)) {
            refreshAlertCount();
          }
          if (
            message.type === 'alert.created' &&
            typeof Notification !== 'undefined' &&
            Notification.permission === 'granted' &&
            message.alert
          ) {
            new Notification(message.alert.title || 'GeoShield Alert', {
              body: message.alert.message || 'New early-warning alert received.',
              icon: '/geoshield_logo.svg',
              tag: `geoshield-alert-${message.alert.id || Date.now()}`,
            });
          }
        } catch { /* ignore malformed non-operational frames */ }
      };
      socket.onerror = () => socket?.close();
      socket.onclose = (event) => {
        setLiveStreamConnected(false);
        if (event.code === 4401) {
          logout();
          return;
        }
        if (!stopped) reconnectTimer = setTimeout(connect, 3000);
      };
    };

    connect();
    return () => {
      stopped = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [logout]);

  const handleLangChange = (newLang: Language) => {
    setLangState(newLang);
    setLanguage(newLang);
  };

  const enableBrowserNotifications = async () => {
    setPushSetupMessage('');
    if (
      typeof Notification === 'undefined' ||
      !('serviceWorker' in navigator) ||
      !('PushManager' in window)
    ) {
      setPushSetupMessage('Web Push is not supported on this browser/device.');
      return;
    }

    try {
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        setPushSetupMessage('Notification permission was not granted.');
        return;
      }

      const registration = await navigator.serviceWorker.ready;
      let subscription = await registration.pushManager.getSubscription();

      if (!subscription) {
        const keyResponse = await getWebPushPublicKey();
        const base64 = keyResponse.data.public_key
          .replace(/-/g, '+')
          .replace(/_/g, '/');
        const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
        const raw = window.atob(padded);
        const applicationServerKey = Uint8Array.from(
          Array.from(raw).map((char) => char.charCodeAt(0)),
        );
        subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey,
        });
      }

      await subscribeWebPush(subscription.toJSON(), 'all');
      setPushSetupMessage('Emergency Web Push is active for this device.');
    } catch (error: any) {
      setPushSetupMessage(
        error?.response?.data?.detail ||
        error?.message ||
        'Unable to activate Web Push on this device.',
      );
    }
  };

  const canRunScenario =
    user?.role === 'admin' ||
    user?.role === 'district_admin' ||
    user?.role === 'field_officer';

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: t('dashboard'), badge: null },
    { to: '/map', icon: Map, label: t('map'), badge: null },
    { to: '/alerts', icon: AlertTriangle, label: t('alerts'), badge: activeAlerts > 0 ? activeAlerts : null },
    { to: '/reports', icon: FileText, label: t('reports'), badge: null },
    { to: '/stations', icon: Radio, label: t('stations'), badge: null },
    { to: '/satellite', icon: Satellite, label: t('satellite'), badge: null },
    { to: '/flood', icon: Waves, label: t('floodRisk'), badge: null },
    ...(canRunScenario
      ? [{ to: '/simulator', icon: Zap, label: 'Scenario Testing', badge: null }]
      : []),
    ...(['admin', 'district_admin'].includes(user?.role || '')
      ? [{ to: '/admin', icon: Settings, label: user?.role === 'admin' ? 'Administration' : 'District Operations', badge: null }]
      : []),
  ];

  return (
    <div className="flex h-screen overflow-hidden bg-dark-950">
      {/* Mobile Backdrop */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0 fixed inset-y-0 left-0 z-50 md:relative md:z-auto transition-all duration-300 ${sidebarOpen ? 'w-64' : 'w-[72px]'} bg-dark-900 border-r border-dark-700 flex flex-col flex-shrink-0`}
      >
        {/* Logo */}
        <div className="p-4 border-b border-dark-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl overflow-hidden flex-shrink-0 shadow-lg shadow-green-600/20">
              <img src="/geoshield_logo.svg" alt="GeoShield" className="w-full h-full object-cover" />
            </div>
            {sidebarOpen && (
              <div className="min-w-0">
                <h1 className="text-lg font-bold text-white truncate">GeoShield</h1>
                <p className="text-[10px] text-dark-400 truncate">{t('nerLandslideMonitor')}</p>
              </div>
            )}
          </div>
        </div>

        {/* Live Status */}
        <div className={`px-3 py-2.5 border-b border-dark-700 ${!sidebarOpen ? 'px-2' : ''}`}>
          <div className={`flex items-center gap-2 ${sidebarOpen ? '' : 'justify-center'}`}>
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
            </span>
            {sidebarOpen && (
              <div>
                <span className="text-[10px] text-green-400 font-semibold tracking-wider">SYSTEM ONLINE</span>
              </div>
            )}
          </div>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 py-3 space-y-1 px-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={() => setMobileMenuOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative ${
                  isActive
                    ? 'bg-green-600/15 text-green-400 border border-green-600/25 shadow-lg shadow-green-600/5'
                    : 'text-dark-300 hover:bg-dark-800 hover:text-white border border-transparent'
                } ${!sidebarOpen ? 'justify-center' : ''}`
              }
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span className="text-sm font-medium">{item.label}</span>}
              {item.badge && sidebarOpen && (
                <span className="ml-auto px-1.5 py-0.5 rounded-full bg-red-600 text-white text-[10px] font-bold min-w-[18px] text-center">
                  {item.badge}
                </span>
              )}
              {item.badge && !sidebarOpen && (
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-600 text-white text-[8px] font-bold flex items-center justify-center">
                  {item.badge}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Station Quick Links */}
        {sidebarOpen && (
          <div className="px-3 py-2 border-t border-dark-700">
            <p className="text-[10px] text-dark-500 font-medium tracking-wider mb-2 px-1">{t('quickStations')}</p>
            <div className="space-y-0.5">
              {[
                { name: 'Gangtok', risk: 'moderate', id: 'NER-001' },
                { name: 'Cherrapunji', risk: 'high', id: 'NER-011' },
                { name: 'Imphal', risk: 'moderate', id: 'NER-006' },
              ].map((s) => (
                <NavLink
                  key={s.id}
                  to={`/station/${s.id}`}
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs text-dark-400 hover:bg-dark-800 hover:text-white transition-all"
                >
                  <div className={`w-1.5 h-1.5 rounded-full ${
                    s.risk === 'high' ? 'bg-red-500' : s.risk === 'moderate' ? 'bg-amber-500' : 'bg-green-500'
                  }`} />
                  {s.name}
                </NavLink>
              ))}
            </div>
          </div>
        )}

        {/* Language Selector */}
        <div className={`p-3 border-t border-dark-700 ${!sidebarOpen ? 'p-2' : ''}`}>
          {sidebarOpen ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-dark-400">
                <Globe className="w-3.5 h-3.5" />
                <span className="text-[10px] font-medium tracking-wider">{t('settings').toUpperCase()}</span>
              </div>
              <div className="grid grid-cols-2 gap-1">
                {(Object.entries(languages) as [Language, { name: string; flag: string }][]).map(
                  ([code, { name, flag }]) => (
                    <button
                      key={code}
                      onClick={() => handleLangChange(code)}
                      className={`text-[11px] px-2 py-1.5 rounded-lg transition-all ${
                        lang === code
                          ? 'bg-green-600/15 text-green-400 border border-green-600/25'
                          : 'text-dark-400 hover:bg-dark-800 border border-transparent hover:text-dark-200'
                      }`}
                    >
                      {flag} {name}
                    </button>
                  )
                )}
              </div>
               <button
                 onClick={enableBrowserNotifications}
                 className="w-full text-[11px] px-2 py-1.5 rounded-lg bg-amber-600/10 text-amber-300 border border-amber-600/30 hover:bg-amber-600/20"
               >
                 Enable Emergency Push
               </button>
               {pushSetupMessage && (
                 <p className="text-[10px] leading-relaxed text-dark-400">{pushSetupMessage}</p>
               )}
               <div className="space-y-2">
                 <label className="text-[10px] text-dark-500 font-medium">Backend URL</label>
                 <div className="flex gap-1">
                   <input
                     type="text"
                     value={serverUrl}
                     onChange={(e) => setServerUrlState(e.target.value)}
                     placeholder="http://192.168.1.100:8000"
                     className="flex-1 text-[11px] px-2 py-1.5 rounded-lg bg-dark-800 border border-dark-700 text-white placeholder-dark-500 focus:outline-none focus:border-green-600/50"
                   />
                   <button
                     onClick={() => setServerUrl(serverUrl)}
                     className="text-[11px] px-2 py-1.5 rounded-lg bg-green-600/20 text-green-400 border border-green-600/30 hover:bg-green-600/30"
                   >
                     Save
                   </button>
                 </div>
               </div>
             </div>
           ) : (
            <button
              onClick={() => setSidebarOpen(true)}
              className="w-full flex justify-center text-dark-400 hover:text-white p-1"
            >
              <Globe className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* User & Collapse */}
        <div className="border-t border-dark-700">
          {sidebarOpen && user && (
            <div className="px-3 py-2.5 flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4 text-white" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-white truncate">{user.name}</p>
                <p className="text-[10px] text-dark-400 truncate">{user.role}</p>
              </div>
              <button
                onClick={logout}
                className="text-dark-400 hover:text-red-400 transition-all p-1"
                title={t('logout')}
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="w-full p-3 text-dark-400 hover:text-white hover:bg-dark-800 transition-all flex items-center justify-center"
          >
            <ChevronLeft className={`w-4 h-4 transition-transform duration-300 ${sidebarOpen ? '' : 'rotate-180'}`} />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-12 border-b border-dark-700 bg-dark-900/80 backdrop-blur-sm flex items-center justify-between px-4 flex-shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-1.5 -ml-1.5 rounded-lg text-dark-300 hover:text-white hover:bg-dark-800 transition-all"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${
              systemReady === true
                ? 'bg-green-600/10 border-green-600/20'
                : systemReady === false
                  ? 'bg-red-600/10 border-red-600/20'
                  : 'bg-amber-600/10 border-amber-600/20'
            }`}>
              <Radio className={`w-3 h-3 ${
                systemReady === true ? 'text-green-400' : systemReady === false ? 'text-red-400' : 'text-amber-400'
              }`} />
              <span className={`text-[10px] font-semibold ${
                systemReady === true ? 'text-green-400' : systemReady === false ? 'text-red-400' : 'text-amber-400'
              }`}>
                {systemReady === true ? 'SYSTEM READY' : systemReady === false ? 'SYSTEM OFFLINE' : 'CHECKING SYSTEM'}
              </span>
              {systemReady === true && (
                <span
                  className={`w-1.5 h-1.5 rounded-full ${liveStreamConnected ? 'bg-green-400' : 'bg-amber-400'}`}
                  title={liveStreamConnected ? 'Live alert stream connected' : 'Live stream reconnecting; polling fallback active'}
                />
              )}
            </div>
            <span className="text-xs text-dark-400 hidden md:inline">NER Operational Monitoring Platform</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-dark-400">
              <Bell className="w-3.5 h-3.5" />
              {activeAlerts > 0 && (
                <span className="px-1.5 py-0.5 rounded-full bg-red-600 text-white text-[9px] font-bold">{activeAlerts}</span>
              )}
            </div>
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-dark-800 border border-dark-700">
              <Clock className="w-3 h-3 text-dark-400" />
              <span className="text-[10px] text-dark-300 font-mono">
                {currentTime.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })}
              </span>
            </div>
            <div className="px-2 py-1 rounded-lg bg-blue-600/10 border border-blue-600/20">
              <span className="text-[10px] text-blue-400 font-medium">SIH 2026</span>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-dark-950">
          {/* key={lang} forces remount when language changes, so t() calls re-evaluate */}
          <Routes key={lang}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/map" element={<RiskMap />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/stations" element={<Stations />} />
            <Route path="/station/:stationId" element={<StationDetail />} />
            <Route
              path="/simulator"
              element={canRunScenario ? <Simulator /> : <Navigate to="/" replace />}
            />
            <Route path="/satellite" element={<SatelliteData />} />
            <Route path="/flood" element={<FloodData />} />
            {['admin', 'district_admin'].includes(user?.role || '') && <Route path="/admin" element={<AdminOperations />} />}
            <Route
              path="/demo"
              element={canRunScenario ? <DemoFlow /> : <Navigate to="/" replace />}
            />
          </Routes>
        </main>
      </div>
      {/* Mobile Floating Action Button */}
      <MobileFAB />
    </div>
  );
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<{ name: string; role: string } | null>(null);

  // Restore session from stored JWT on mount
  useEffect(() => {
    const token = getStoredToken();
    if (token) {
      try {
        const segment = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
        const padded = segment.padEnd(Math.ceil(segment.length / 4) * 4, '=');
        const payload = JSON.parse(atob(padded));
        if (payload.exp * 1000 > Date.now()) {
          setUser({ name: payload.name, role: payload.role });
          setIsLoggedIn(true);
        } else {
          clearStoredToken();
        }
      } catch {
        clearStoredToken();
      }
    }
  }, []);

  const login = (name: string, role: string) => {
    setIsLoggedIn(true);
    setUser({ name, role });
  };

  const logout = () => {
    clearStoredToken();
    setIsLoggedIn(false);
    setUser(null);
  };

  return (
    <ErrorBoundary>
      <AuthContext.Provider value={{ isLoggedIn, user, login, logout }}>
        <Router>
          {isLoggedIn ? <MainLayout /> : <LoginPage />}
        </Router>
      </AuthContext.Provider>
    </ErrorBoundary>
  );
}

export default App;
