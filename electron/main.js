/**
 * GeoShield Electron Desktop App
 * Auto-starts the Python backend and loads the frontend.
 */
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let backendProcess;
const BACKEND_PORT = 8000;
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;

if (process.env.GEOSHIELD_USER_DATA_DIR) {
  app.setPath('userData', path.resolve(process.env.GEOSHIELD_USER_DATA_DIR));
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    backgroundColor: '#0a0f1a',
    title: 'GeoShield — Landslide Risk Monitoring',
    icon: path.join(__dirname, '..', 'branding', 'team_logo.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    titleBarStyle: 'hiddenInset',
    show: false,
  });

  // Wait for backend to start, then load frontend
  mainWindow.loadURL(BACKEND_URL);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  const backendDir = app.isPackaged
    ? path.join(process.resourcesPath, 'backend')
    : path.join(__dirname, '..', 'backend');
  const dataDir = app.getPath('userData');
  const bundledPython = path.join(process.resourcesPath, 'runtime', 'python', 'python.exe');
  const pythonCmd =
    app.isPackaged && process.platform === 'win32' && fs.existsSync(bundledPython)
      ? bundledPython
      : (process.platform === 'win32' ? 'python' : 'python3');
  const databasePath = path.join(dataDir, 'geoshield.db').replace(/\\/g, '/');
  const modelCacheDir = path.join(dataDir, 'models');
  const reportUploadDir = path.join(dataDir, 'uploads', 'reports');

  fs.mkdirSync(dataDir, { recursive: true });
  const backendLogPath = path.join(dataDir, 'backend.log');
  const backendLogStream = fs.createWriteStream(backendLogPath, { flags: 'a' });
  backendLogStream.write(`\n[${new Date().toISOString()}] Starting GeoShield backend with ${pythonCmd}\n`);

  console.log('[GeoShield] Starting backend...');
  console.log(`[GeoShield] Backend log: ${backendLogPath}`);
  backendProcess = spawn(pythonCmd, [
    '-m', 'uvicorn', 'app.main:app',
    '--host', '127.0.0.1',
    '--port', String(BACKEND_PORT),
  ], {
    cwd: backendDir,
    stdio: 'pipe',
    env: {
      ...process.env,
      APP_ENV: 'demo',
      ENABLE_DEMO_USERS: 'true',
      WEATHER_LIVE_ENABLED: 'false',
      MODEL_TRAINING_ENABLED: 'false',
      TRUST_PROXY_HEADERS: 'false',
      DATABASE_URL: `sqlite:///${databasePath}`,
      MODEL_CACHE_DIR: modelCacheDir,
      REPORT_UPLOAD_DIR: reportUploadDir,
      AUTO_SEED_REFERENCE_DATA: 'true',
      PYTHONNOUSERSITE: '1',
      PYTHONUTF8: '1',
      PYTHONIOENCODING: 'utf-8',
      TRAINING_DATA_PATH: app.isPackaged
        ? path.join(process.resourcesPath, 'datasets', 'processed', 'real_ner_training_data.csv')
        : path.join(__dirname, '..', 'datasets', 'processed', 'real_ner_training_data.csv'),
      SATELLITE_DATA_PATH: app.isPackaged
        ? path.join(process.resourcesPath, 'datasets', 'processed', 'real_satellite_data.json')
        : path.join(__dirname, '..', 'datasets', 'processed', 'real_satellite_data.json'),
    },
  });

  backendProcess.stdout.on('data', (data) => {
    backendLogStream.write(data);
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr.on('data', (data) => {
    backendLogStream.write(data);
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.on('error', (error) => {
    backendLogStream.write(`Backend spawn error: ${error.stack || error.message}\n`);
    console.error('[GeoShield] Backend spawn error:', error);
  });

  backendProcess.on('close', (code) => {
    backendLogStream.write(`Backend exited with code ${code}\n`);
    backendLogStream.end();
    console.log(`[GeoShield] Backend exited with code ${code}`);
  });
}

function stopBackend() {
  if (backendProcess) {
    console.log('[GeoShield] Stopping backend...');
    backendProcess.kill();
    backendProcess = null;
  }
}

// Wait for backend to be ready
function waitForBackend(retries = 30, delay = 1000) {
  return new Promise((resolve, reject) => {
    const http = require('http');
    let attempts = 0;

    const check = () => {
      attempts++;
      const req = http.get(`${BACKEND_URL}/api/health`, (res) => {
        if (res.statusCode === 200) {
          console.log('[GeoShield] Backend ready!');
          resolve();
        } else {
          retry();
        }
      });

      req.on('error', () => retry());
      req.setTimeout(500, () => { req.destroy(); retry(); });
    };

    const retry = () => {
      if (attempts >= retries) {
        reject(new Error('Backend failed to start'));
      } else {
        setTimeout(check, delay);
      }
    };

    check();
  });
}

ipcMain.handle('get-app-version', () => app.getVersion());
ipcMain.on('window-minimize', () => mainWindow?.minimize());
ipcMain.on('window-maximize', () => {
  if (!mainWindow) return;
  if (mainWindow.isMaximized()) mainWindow.unmaximize();
  else mainWindow.maximize();
});
ipcMain.on('window-close', () => mainWindow?.close());

app.whenReady().then(async () => {
  startBackend();

  try {
    await waitForBackend();
  } catch (err) {
    console.error('[GeoShield] Backend failed to start:', err.message);
  }

  createWindow();
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  stopBackend();
});
