import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'
import './index.css'

// Initialize Capacitor plugins for mobile
async function initCapacitor() {
  try {
    const { StatusBar, Style } = await import('@capacitor/status-bar');
    await StatusBar.setStyle({ style: Style.Dark });
    await StatusBar.setBackgroundColor({ color: '#0a0f1a' });
  } catch {
    // Not on mobile, skip
  }
  // Signal app ready for splash fade-in
  document.body.classList.add('capacitor-ready');
}

initCapacitor();

// Browser/PWA shell cache. Capacitor already bundles the web assets locally,
// while the API layer provides cached data + queued field reports offline.
if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => undefined);
  });
}


ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
)
