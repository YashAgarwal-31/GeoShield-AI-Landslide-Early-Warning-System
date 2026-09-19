import type { AxiosInstance, AxiosResponse } from 'axios';

const CACHE_PREFIX = 'geoshield_api_cache:';
const DB_NAME = 'geoshield-offline';
const STORE = 'queued-reports';
const DB_VERSION = 1;

type CachedEnvelope = {
  savedAt: number;
  data: unknown;
  status: number;
  statusText: string;
  headers?: Record<string, string>;
};

export const apiCacheKey = (url: string, params?: unknown) =>
  `${CACHE_PREFIX}${url}?${JSON.stringify(params || {})}`;

export function saveApiCache(key: string, response: AxiosResponse) {
  try {
    const envelope: CachedEnvelope = {
      savedAt: Date.now(),
      data: response.data,
      status: response.status,
      statusText: response.statusText,
    };
    localStorage.setItem(key, JSON.stringify(envelope));
  } catch {
    // Cache quota/storage availability must never break the live app.
  }
}

export function readApiCache(key: string, maxAgeMs = 24 * 60 * 60 * 1000): CachedEnvelope | null {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as CachedEnvelope;
    if (!parsed.savedAt || Date.now() - parsed.savedAt > maxAgeMs) return null;
    return parsed;
  } catch {
    return null;
  }
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: 'id', autoIncrement: true });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function queueReport(formData: FormData): Promise<void> {
  if (typeof indexedDB === 'undefined') throw new Error('Offline queue unavailable');
  const entries: Array<[string, FormDataEntryValue]> = [];
  formData.forEach((value, key) => entries.push([key, value]));
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).add({ createdAt: Date.now(), entries });
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
  db.close();
}

async function queuedReports(): Promise<any[]> {
  if (typeof indexedDB === 'undefined') return [];
  const db = await openDb();
  const rows = await new Promise<any[]>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readonly');
    const request = tx.objectStore(STORE).getAll();
    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => reject(request.error);
  });
  db.close();
  return rows;
}

async function deleteQueuedReport(id: IDBValidKey): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
  db.close();
}

export async function flushQueuedReports(api: AxiosInstance): Promise<number> {
  if (typeof navigator !== 'undefined' && !navigator.onLine) return 0;
  const rows = await queuedReports();
  let sent = 0;
  for (const row of rows) {
    const form = new FormData();
    for (const [key, value] of row.entries || []) {
      form.append(key, value);
    }
    try {
      await api.post('/reports', form);
      await deleteQueuedReport(row.id);
      sent += 1;
    } catch {
      break;
    }
  }
  return sent;
}

export async function getQueuedReportCount(): Promise<number> {
  return (await queuedReports()).length;
}
