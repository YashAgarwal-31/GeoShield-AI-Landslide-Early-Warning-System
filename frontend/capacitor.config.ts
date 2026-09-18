import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.geoshield.app',
  appName: 'GeoShield',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
    // Required by the academic/debug APK when connecting to a LAN HTTP backend.
    // Signed production releases should use an HTTPS backend and disable this.
    cleartext: true,
  },
};

export default config;
