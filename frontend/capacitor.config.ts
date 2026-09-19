import type { CapacitorConfig } from '@capacitor/cli';

const enableDevTransport =
  process.env.GEOSHIELD_ANDROID_DEV_TRANSPORT?.trim().toLowerCase() === 'true';

const config: CapacitorConfig = {
  appId: 'com.geoshield.app',
  appName: 'GeoShield',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
    // Cleartext is opt-in for local academic/debug use only.
    cleartext: enableDevTransport,
  },
  android: {
    // Required when the HTTPS Capacitor WebView calls a local/LAN HTTP backend.
    // This remains disabled unless GEOSHIELD_ANDROID_DEV_TRANSPORT=true.
    allowMixedContent: enableDevTransport,
  },
};

export default config;
