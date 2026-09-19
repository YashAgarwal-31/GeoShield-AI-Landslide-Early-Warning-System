import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const enabled =
  process.env.GEOSHIELD_ANDROID_DEV_TRANSPORT?.trim().toLowerCase() === 'true';

if (!enabled) {
  console.log('[GeoShield] Android dev transport disabled; keeping release-safe defaults.');
  process.exit(0);
}

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(scriptDir, '..');
const androidDir = path.join(frontendDir, 'android');
const debugManifestDir = path.join(androidDir, 'app', 'src', 'debug');
const generatedConfig = path.join(
  androidDir,
  'app',
  'src',
  'main',
  'assets',
  'capacitor.config.json',
);

if (!fs.existsSync(androidDir)) {
  throw new Error('Android project is missing. Run "npx cap add android" first.');
}

if (!fs.existsSync(generatedConfig)) {
  throw new Error('Generated Capacitor config is missing. Run "npx cap sync android" first.');
}

const parsedConfig = JSON.parse(fs.readFileSync(generatedConfig, 'utf8'));
if (parsedConfig?.server?.cleartext !== true) {
  throw new Error('Generated Android config does not enable debug cleartext transport.');
}
if (parsedConfig?.android?.allowMixedContent !== true) {
  throw new Error('Generated Android config does not enable debug mixed content.');
}

fs.mkdirSync(debugManifestDir, { recursive: true });
fs.writeFileSync(
  path.join(debugManifestDir, 'AndroidManifest.xml'),
  `<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application android:usesCleartextTraffic="true" />
</manifest>
`,
  'utf8',
);

console.log('[GeoShield] Debug-only Android LAN transport configured.');
