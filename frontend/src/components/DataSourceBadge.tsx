import { DataSourceMetadata } from '../services/api';

const MODE_STYLE: Record<DataSourceMetadata['mode'], string> = {
  live: 'bg-green-600/10 border-green-600/30 text-green-400',
  cached: 'bg-blue-600/10 border-blue-600/30 text-blue-400',
  fallback: 'bg-amber-600/10 border-amber-600/30 text-amber-400',
  unavailable: 'bg-red-600/10 border-red-600/30 text-red-400',
};

function formatAge(seconds: number | null): string {
  if (seconds === null) return 'age unknown';
  if (seconds < 60) return `${seconds}s old`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m old`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h old`;
  return `${Math.floor(seconds / 86400)}d old`;
}

export default function DataSourceBadge({ source }: { source?: DataSourceMetadata | null }) {
  if (!source) return null;
  const title = [source.detail, source.fallback_reason].filter(Boolean).join(' ');
  return (
    <div className="flex flex-wrap items-center gap-2" title={title}>
      <span className={`px-3 py-1.5 rounded-full border text-xs font-medium flex items-center gap-1.5 ${MODE_STYLE[source.mode]}`}>
        <span className="w-2 h-2 rounded-full bg-current" />
        {source.mode.toUpperCase()}{source.is_stale ? ' · STALE' : ''}
      </span>
      <span className="text-xs text-dark-500">
        {source.provider} · {formatAge(source.age_seconds)}
      </span>
    </div>
  );
}
