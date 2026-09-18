import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.geoshield.app',
  appName: 'GeoShield',
  webDir: 'dist',
  server: {
    // Use the bundled Vite build in installed APKs. The backend address is
    // configured from the login/settings screen instead of hard-coding
    // localhost, which points to the Android device itself.
    cleartext: true,
    androidScheme: 'http',
  },
  android: {
    allowMixedContent: true,
    backgroundColor: '#0a0f1a',
    buildOptions: {
      keystorePath: undefined,
      keystoreAlias: undefined,
    },
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2500,
      launchAutoHide: true,
      backgroundColor: '#0a0f1a',
      androidScaleType: 'CENTER_CROP',
      showSpinner: false,
      androidSplashResourceName: 'splash',
      splashFullScreen: true,
      splashImmersive: true,
    },
    StatusBar: {
      style: 'DARK',
      backgroundColor: '#0a0f1a',
      overlaysWebView: true,
    },
    Keyboard: {
      resize: 'body',
      resizeOnFullScreen: true,
    },
  },
};

export default config;
