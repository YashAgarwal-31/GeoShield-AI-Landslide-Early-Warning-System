import { FormEvent, useEffect, useState } from 'react';
import { useAuth } from '../App';
import {
  createStation,
  createUser,
  getManagedStations,
  getReadiness,
  getUsers,
  resetUserPassword,
  setUserStatus,
  updateStation,
  ManagedStation,
  StationCreatePayload,
  UserAccount,
  CommunicationStatus,
  CommunicationDelivery,
  getCommunicationStatus,
  getCommunicationDeliveries,
  testSmsCommunication,
  testPushCommunication,
} from '../services/api';
import {
  Activity,
  CheckCircle2,
  Database,
  MapPin,
  RefreshCw,
  ShieldCheck,
  UserPlus,
  Users,
  Bell,
  Send,
  MessageSquareText,
} from 'lucide-react';

type Message = { kind: 'success' | 'error'; text: string } | null;

const EMPTY_STATION: StationCreatePayload = {
  station_id: '',
  name: '',
  latitude: 25.6,
  longitude: 91.9,
  state: '',
  district: '',
  village: '',
  elevation: 0,
  slope_angle: 0,
  soil_type: 'unknown',
  vegetation_cover: 0,
};

export default function AdminOperations() {
  const { user } = useAuth();
  const isSystemAdmin = user?.role === 'admin';
  const [users, setUsers] = useState<UserAccount[]>([]);
  const [managedStations, setManagedStations] = useState<ManagedStation[]>([]);
  const [readiness, setReadiness] = useState<{ status: string; database: string; environment: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [userMessage, setUserMessage] = useState<Message>(null);
  const [stationMessage, setStationMessage] = useState<Message>(null);
  const [communicationMessage, setCommunicationMessage] = useState<Message>(null);
  const [communicationStatus, setCommunicationStatus] = useState<CommunicationStatus | null>(null);
  const [deliveries, setDeliveries] = useState<CommunicationDelivery[]>([]);
  const [testingChannel, setTestingChannel] = useState<'sms' | 'push' | null>(null);

  const [newUser, setNewUser] = useState({
    email: '',
    name: '',
    password: '',
    role: 'field_officer' as UserAccount['role'],
  });
  const [station, setStation] = useState<StationCreatePayload>({ ...EMPTY_STATION });
  const [editingStationId, setEditingStationId] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [readinessResponse, stationsResponse, communicationResponse, deliveryResponse] = await Promise.all([
        getReadiness(),
        getManagedStations(),
        getCommunicationStatus(),
        getCommunicationDeliveries(20),
      ]);
      setReadiness(readinessResponse.data);
      setManagedStations(stationsResponse.data);
      setCommunicationStatus(communicationResponse.data);
      setDeliveries(deliveryResponse.data);
      if (isSystemAdmin) {
        const usersResponse = await getUsers();
        setUsers(usersResponse.data);
      } else {
        setUsers([]);
      }
    } catch (error: any) {
      setUserMessage({
        kind: 'error',
        text: error.response?.data?.detail || 'Unable to load operations data.',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const submitUser = async (event: FormEvent) => {
    event.preventDefault();
    setUserMessage(null);
    try {
      await createUser(newUser);
      setNewUser({ email: '', name: '', password: '', role: 'field_officer' });
      setUserMessage({ kind: 'success', text: 'Persistent user created successfully.' });
      await load();
    } catch (error: any) {
      setUserMessage({
        kind: 'error',
        text: error.response?.data?.detail || 'Unable to create user.',
      });
    }
  };

  const toggleUser = async (account: UserAccount) => {
    setUserMessage(null);
    try {
      await setUserStatus(account.id, !account.is_active);
      await load();
    } catch (error: any) {
      setUserMessage({
        kind: 'error',
        text: error.response?.data?.detail || 'Unable to update user status.',
      });
    }
  };

  const resetPassword = async (account: UserAccount) => {
    const password = window.prompt(
      `Enter a new password for ${account.email} (minimum 8 characters):`,
    );
    if (password === null) return;
    if (password.length < 8) {
      setUserMessage({ kind: 'error', text: 'Password must be at least 8 characters.' });
      return;
    }

    setUserMessage(null);
    try {
      await resetUserPassword(account.id, password);
      setUserMessage({
        kind: 'success',
        text: `Password reset successfully for ${account.email}.`,
      });
    } catch (error: any) {
      setUserMessage({
        kind: 'error',
        text: error.response?.data?.detail || 'Unable to reset password.',
      });
    }
  };

  const submitStation = async (event: FormEvent) => {
    event.preventDefault();
    setStationMessage(null);
    try {
      if (editingStationId) {
        const { station_id: _stationId, ...updates } = station;
        await updateStation(editingStationId, updates);
        setStationMessage({
          kind: 'success',
          text: `Monitoring station ${editingStationId} updated successfully.`,
        });
      } else {
        await createStation(station);
        setStationMessage({
          kind: 'success',
          text: 'Monitoring station provisioned. It can now accept authenticated gateway readings.',
        });
      }
      setStation({ ...EMPTY_STATION });
      setEditingStationId(null);
      await load();
    } catch (error: any) {
      setStationMessage({
        kind: 'error',
        text: error.response?.data?.detail || 'Unable to save monitoring station.',
      });
    }
  };

  const editStation = (account: ManagedStation) => {
    setEditingStationId(account.station_id);
    setStation({
      station_id: account.station_id,
      name: account.name,
      latitude: account.latitude,
      longitude: account.longitude,
      state: account.state,
      district: account.district,
      village: account.village || '',
      elevation: account.elevation ?? 0,
      slope_angle: account.slope_angle ?? 0,
      soil_type: account.soil_type || 'unknown',
      vegetation_cover: account.vegetation_cover ?? 0,
    });
    setStationMessage(null);
  };

  const cancelStationEdit = () => {
    setEditingStationId(null);
    setStation({ ...EMPTY_STATION });
    setStationMessage(null);
  };

  const toggleStation = async (account: ManagedStation) => {
    setStationMessage(null);
    try {
      await updateStation(account.station_id, { is_active: !account.is_active });
      setStationMessage({
        kind: 'success',
        text: `${account.station_id} is now ${account.is_active ? 'inactive' : 'active'}.`,
      });
      await load();
    } catch (error: any) {
      setStationMessage({
        kind: 'error',
        text: error.response?.data?.detail || 'Unable to update station status.',
      });
    }
  };

  const testCommunication = async (channel: 'sms' | 'push') => {
    setTestingChannel(channel);
    setCommunicationMessage(null);
    try {
      const request = {
        risk_level: 'high' as const,
        title: `GeoShield ${channel.toUpperCase()} Communication Test`,
        message: 'ACT emergency communication channel verification from GeoShield.',
        station_id: 'TEST-ACT',
        district: 'all',
      };
      const response = channel === 'sms'
        ? await testSmsCommunication(request)
        : await testPushCommunication(request);
      const delivery = response.data.delivery;
      const sent = Number(delivery?.sent || 0);
      const configured = Boolean(delivery?.configured);
      setCommunicationMessage({
        kind: sent > 0 ? 'success' : 'error',
        text: sent > 0
          ? `${channel.toUpperCase()} test delivered successfully (${sent} delivery/deliveries).`
          : configured
            ? `${channel.toUpperCase()} provider is configured, but the test did not deliver. Check delivery log/provider status.`
            : `${channel.toUpperCase()} provider is implemented but deployment credentials/subscriptions are not configured yet.`,
      });
      await load();
    } catch (error: any) {
      setCommunicationMessage({
        kind: 'error',
        text: error.response?.data?.detail || `Unable to test ${channel.toUpperCase()} channel.`,
      });
    } finally {
      setTestingChannel(null);
    }
  };

  const messageClass = (message: Message) =>
    message?.kind === 'success'
      ? 'border-green-600/30 bg-green-600/10 text-green-300'
      : 'border-red-600/30 bg-red-600/10 text-red-300';

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-green-400" />
            {isSystemAdmin ? 'System Administration' : 'District Operations'}
          </h1>
          <p className="text-dark-400 text-sm mt-1">
            {isSystemAdmin
              ? 'Manage persistent operators, monitoring stations, and runtime readiness.'
              : 'Manage monitoring-station operations and runtime readiness.'}
          </p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl border border-dark-700 bg-dark-800 text-dark-200 text-sm hover:border-green-600/40 hover:text-green-300 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass rounded-xl p-4 border border-dark-700">
          <Database className="w-5 h-5 text-blue-400 mb-3" />
          <p className="text-xs text-dark-400">Database readiness</p>
          <p className="text-lg font-semibold text-white mt-1">{readiness?.database || 'Checking...'}</p>
        </div>
        <div className="glass rounded-xl p-4 border border-dark-700">
          <Activity className="w-5 h-5 text-green-400 mb-3" />
          <p className="text-xs text-dark-400">Runtime</p>
          <p className="text-lg font-semibold text-white mt-1">{readiness?.status || 'Checking...'}</p>
        </div>
        <div className="glass rounded-xl p-4 border border-dark-700">
          <Users className="w-5 h-5 text-purple-400 mb-3" />
          <p className="text-xs text-dark-400">{isSystemAdmin ? 'Persistent users' : 'Managed stations'}</p>
          <p className="text-lg font-semibold text-white mt-1">{isSystemAdmin ? users.length : managedStations.length}</p>
          <p className="text-[10px] text-dark-500 mt-1">{readiness?.environment || 'unknown'} environment</p>
        </div>
      </div>

      <section className="glass rounded-xl p-5 border border-dark-700">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between mb-4">
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-amber-400" />
            <div>
              <h2 className="text-lg font-semibold text-white">Emergency Communication Center</h2>
              <p className="text-xs text-dark-400">
                Multi-channel warning delivery: Twilio SMS + ntfy + standards-based VAPID Web Push.
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={testingChannel !== null}
              onClick={() => testCommunication('sms')}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-green-600/30 bg-green-600/10 text-green-300 text-xs hover:bg-green-600/20 disabled:opacity-50"
            >
              <MessageSquareText className="w-3.5 h-3.5" />
              {testingChannel === 'sms' ? 'Testing SMS…' : 'Test SMS'}
            </button>
            <button
              type="button"
              disabled={testingChannel !== null}
              onClick={() => testCommunication('push')}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-amber-600/30 bg-amber-600/10 text-amber-300 text-xs hover:bg-amber-600/20 disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              {testingChannel === 'push' ? 'Testing Push…' : 'Test Push'}
            </button>
          </div>
        </div>

        {communicationMessage && (
          <div className={`mb-4 rounded-lg border px-3 py-2 text-xs ${messageClass(communicationMessage)}`}>
            {communicationMessage.text}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          {[
            {
              label: 'SMS / Twilio',
              enabled: communicationStatus?.sms.enabled,
              configured: communicationStatus?.sms.configured,
              detail: 'District-aware emergency SMS',
            },
            {
              label: 'Topic Push / ntfy',
              enabled: communicationStatus?.topic_push.enabled,
              configured: communicationStatus?.topic_push.configured,
              detail: 'Mobile/topic push channel',
            },
            {
              label: 'Web Push / VAPID',
              enabled: communicationStatus?.web_push.enabled,
              configured: communicationStatus?.web_push.configured,
              detail: `${communicationStatus?.web_push.active_subscriptions || 0} active device subscriptions`,
            },
          ].map((channel) => (
            <div key={channel.label} className="rounded-xl border border-dark-700 bg-dark-850/60 p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-white">{channel.label}</p>
                <span className={`px-2 py-0.5 rounded-full text-[10px] border ${
                  channel.enabled && channel.configured
                    ? 'border-green-600/30 bg-green-600/10 text-green-300'
                    : channel.enabled
                      ? 'border-amber-600/30 bg-amber-600/10 text-amber-300'
                      : 'border-dark-600 bg-dark-800 text-dark-400'
                }`}>
                  {channel.enabled && channel.configured ? 'READY' : channel.enabled ? 'NEEDS CONFIG' : 'DISABLED'}
                </span>
              </div>
              <p className="text-[11px] text-dark-500 mt-1">{channel.detail}</p>
            </div>
          ))}
        </div>

        <div className="border-t border-dark-700 pt-3">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-medium text-dark-300">Recent communication deliveries</p>
            <span className="text-[10px] text-dark-500">{deliveries.length} shown</span>
          </div>
          <div className="max-h-44 overflow-y-auto space-y-1.5">
            {deliveries.length === 0 ? (
              <p className="text-[11px] text-dark-500">No delivery attempts recorded yet.</p>
            ) : deliveries.map((delivery) => (
              <div key={delivery.id} className="flex items-center justify-between gap-3 rounded-lg bg-dark-900/60 px-3 py-2">
                <div className="min-w-0">
                  <p className="text-[11px] text-white truncate">
                    {delivery.channel.toUpperCase()} · {delivery.provider}
                    {delivery.district ? ` · ${delivery.district}` : ''}
                  </p>
                  <p className="text-[10px] text-dark-500 truncate">
                    {delivery.recipient || 'provider target'} · {delivery.created_at || 'unknown time'}
                  </p>
                </div>
                <span className={`text-[10px] font-semibold ${
                  delivery.status === 'sent' ? 'text-green-400' : 'text-red-400'
                }`}>
                  {delivery.status.toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className={`grid grid-cols-1 ${isSystemAdmin ? 'xl:grid-cols-2' : ''} gap-6`}>
        {isSystemAdmin && <section className="glass rounded-xl p-5 border border-dark-700">
          <div className="flex items-center gap-2 mb-4">
            <UserPlus className="w-5 h-5 text-green-400" />
            <div>
              <h2 className="text-lg font-semibold text-white">Create operator account</h2>
              <p className="text-xs text-dark-400">Accounts are stored in the application database.</p>
            </div>
          </div>

          {userMessage && (
            <div className={`mb-4 rounded-lg border px-3 py-2 text-xs ${messageClass(userMessage)}`}>
              {userMessage.text}
            </div>
          )}

          <form onSubmit={submitUser} className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input
              required
              type="text"
              value={newUser.name}
              onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
              placeholder="Full name"
              className="px-3 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm"
            />
            <input
              required
              type="email"
              value={newUser.email}
              onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
              placeholder="Email"
              className="px-3 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm"
            />
            <input
              required
              minLength={8}
              type="password"
              value={newUser.password}
              onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
              placeholder="Password (8+ characters)"
              className="px-3 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm"
            />
            <select
              value={newUser.role}
              onChange={(e) => setNewUser({ ...newUser, role: e.target.value as UserAccount['role'] })}
              className="px-3 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm"
            >
              <option value="field_officer">Field Officer</option>
              <option value="district_admin">District Admin</option>
              <option value="citizen">Citizen</option>
              <option value="admin">Admin</option>
            </select>
            <button
              type="submit"
              className="md:col-span-2 px-4 py-2.5 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-500"
            >
              Create persistent user
            </button>
          </form>

          <div className="mt-5 space-y-2 max-h-72 overflow-y-auto pr-1">
            {users.map((account) => (
              <div
                key={account.id}
                className="flex items-center justify-between gap-3 rounded-lg border border-dark-700 bg-dark-850/60 px-3 py-2.5"
              >
                <div className="min-w-0">
                  <p className="text-sm text-white truncate">{account.name}</p>
                  <p className="text-[11px] text-dark-400 truncate">{account.email} · {account.role}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => resetPassword(account)}
                    className="px-2.5 py-1.5 rounded-lg text-[11px] border border-blue-600/30 bg-blue-600/10 text-blue-300 hover:bg-blue-600/20"
                  >
                    Reset password
                  </button>
                  <button
                    onClick={() => toggleUser(account)}
                    className={`px-2.5 py-1.5 rounded-lg text-[11px] border ${
                      account.is_active
                        ? 'border-green-600/30 bg-green-600/10 text-green-300'
                        : 'border-dark-600 bg-dark-800 text-dark-400'
                    }`}
                  >
                    {account.is_active ? 'Active' : 'Disabled'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>}

        <section className="glass rounded-xl p-5 border border-dark-700">
          <div className="flex items-center gap-2 mb-4">
            <MapPin className="w-5 h-5 text-blue-400" />
            <div>
              <h2 className="text-lg font-semibold text-white">
                {editingStationId ? 'Edit monitoring station' : 'Provision monitoring station'}
              </h2>
              <p className="text-xs text-dark-400">
                {editingStationId
                  ? 'Update persistent station metadata or return to provisioning mode.'
                  : 'Creates a persistent station that can receive real gateway observations.'}
              </p>
            </div>
          </div>

          {stationMessage && (
            <div className={`mb-4 rounded-lg border px-3 py-2 text-xs ${messageClass(stationMessage)}`}>
              {stationMessage.text}
            </div>
          )}

          {(isSystemAdmin || editingStationId) ? (
          <form onSubmit={submitStation} className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input
              required
              disabled={Boolean(editingStationId)}
              pattern="NER-[0-9]{3}"
              value={station.station_id}
              onChange={(e) => setStation({ ...station, station_id: e.target.value.toUpperCase() })}
              placeholder="Station ID (NER-101)"
              className="px-3 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm disabled:opacity-60"
            />
            <input
              required
              value={station.name}
              onChange={(e) => setStation({ ...station, name: e.target.value })}
              placeholder="Station name"
              className="px-3 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm"
            />
            <input
              required
              value={station.state}
              onChange={(e) => setStation({ ...station, state: e.target.value })}
              placeholder="State"
              className="px-3 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm"
            />
            <input
              required
              value={station.district}
              onChange={(e) => setStation({ ...station, district: e.target.value })}
              placeholder="District"
              className="px-3 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm"
            />
            <input
              type="number"
              step="any"
              value={station.latitude}
              onChange={(e) => setStation({ ...station, latitude: Number(e.target.value) })}
              placeholder="Latitude"
              className="px-3 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm"
            />
            <input
              type="number"
              step="any"
              value={station.longitude}
              onChange={(e) => setStation({ ...station, longitude: Number(e.target.value) })}
              placeholder="Longitude"
              className="px-3 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm"
            />
            <input
              value={station.village || ''}
              onChange={(e) => setStation({ ...station, village: e.target.value })}
              placeholder="Village / locality"
              className="px-3 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm"
            />
            <input
              type="number"
              step="any"
              value={station.elevation}
              onChange={(e) => setStation({ ...station, elevation: Number(e.target.value) })}
              placeholder="Elevation (m)"
              className="px-3 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm"
            />
            <input
              type="number"
              step="any"
              min={0}
              max={90}
              value={station.slope_angle}
              onChange={(e) => setStation({ ...station, slope_angle: Number(e.target.value) })}
              placeholder="Slope angle"
              className="px-3 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm"
            />
            <input
              value={station.soil_type || ''}
              onChange={(e) => setStation({ ...station, soil_type: e.target.value })}
              placeholder="Soil type"
              className="px-3 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm"
            />
            <input
              type="number"
              min={0}
              max={100}
              step="any"
              value={station.vegetation_cover}
              onChange={(e) => setStation({ ...station, vegetation_cover: Number(e.target.value) })}
              placeholder="Vegetation cover (%)"
              className="px-3 py-2.5 rounded-lg bg-dark-800 border border-dark-700 text-white text-sm"
            />
            <div className="md:col-span-2 flex gap-2">
              <button
                type="submit"
                className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-500"
              >
                <CheckCircle2 className="w-4 h-4" />
                {editingStationId ? 'Save station changes' : 'Provision station'}
              </button>
              {editingStationId && (
                <button
                  type="button"
                  onClick={cancelStationEdit}
                  className="px-4 py-2.5 rounded-lg border border-dark-600 bg-dark-800 text-dark-300 text-sm hover:text-white"
                >
                  Cancel
                </button>
              )}
            </div>
          </form>
          ) : (
            <div className="rounded-lg border border-blue-600/20 bg-blue-600/10 px-3 py-2 text-xs text-blue-200">
              Select an existing monitoring station below to update district operations. New station provisioning is reserved for system administrators.
            </div>
          )}

          <div className="mt-5 border-t border-dark-700 pt-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-sm font-semibold text-white">Monitoring station inventory</h3>
                <p className="text-[11px] text-dark-500">
                  {managedStations.length} persistent stations, including inactive stations.
                </p>
              </div>
            </div>
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {managedStations.map((account) => (
                <div
                  key={account.station_id}
                  className="flex items-center justify-between gap-3 rounded-lg border border-dark-700 bg-dark-850/60 px-3 py-2.5"
                >
                  <div className="min-w-0">
                    <p className="text-sm text-white truncate">{account.name}</p>
                    <p className="text-[11px] text-dark-400 truncate">
                      {account.station_id} · {account.district}, {account.state}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => editStation(account)}
                      className="px-2.5 py-1.5 rounded-lg text-[11px] border border-blue-600/30 bg-blue-600/10 text-blue-300 hover:bg-blue-600/20"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => toggleStation(account)}
                      className={`px-2.5 py-1.5 rounded-lg text-[11px] border ${
                        account.is_active
                          ? 'border-green-600/30 bg-green-600/10 text-green-300'
                          : 'border-dark-600 bg-dark-800 text-dark-400'
                      }`}
                    >
                      {account.is_active ? 'Active' : 'Inactive'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
