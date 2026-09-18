import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.geoshield.app',
  appName: 'GeoShield',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
  },
};

export default config;
