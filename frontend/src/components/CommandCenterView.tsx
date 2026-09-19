import React, { useState, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { GoogleWeatherCard } from './GoogleWeatherCard';
import { INITIAL_EVENT_LOGS } from '../data/mockData';
import { EventLog } from '../types';
import {
  checkBackendHealth,
  runAgentPipeline,
  fetchDispatchedAlerts,
  PipelineRunResult,
  SystemHealth,
  getBackendUrl,
  setBackendUrl,
} from '../services/api';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  ShieldAlert,
  Sprout,
  Activity,
  Layers,
  Sparkles,
  Play,
  RefreshCw,
  Server,
  Check,
  X,
  ShieldCheck,
  Zap,
  Settings,
  Loader2,
} from 'lucide-react';

interface CommandCenterViewProps {
  onNavigateTab: (tab: 'command' | 'risk' | 'emergency' | 'agriculture' | 'weathergpt') => void;
  selectedLocation: string;
}

export const CommandCenterView: React.FC<CommandCenterViewProps> = ({
  onNavigateTab,
  selectedLocation,
}) => {
  const { t, language } = useLanguage();

  const [backendHealth, setBackendHealth] = useState<SystemHealth | null>(null);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);
  const [isRunningPipeline, setIsRunningPipeline] = useState<boolean>(false);
  const [pipelineResult, setPipelineResult] = useState<PipelineRunResult | null>(null);
  const [pipelineMode, setPipelineMode] = useState<'mock' | 'live'>('live');
  const [selectedScenario, setSelectedScenario] = useState<string>('heavy_rain');
  const [eventLogs, setEventLogs] = useState<EventLog[]>(INITIAL_EVENT_LOGS);

  const [isBackendModalOpen, setIsBackendModalOpen] = useState<boolean>(false);
  const [backendUrlInput, setBackendUrlInput] = useState<string>(getBackendUrl());

  useEffect(() => {
    let isMounted = true;

    checkBackendHealth().then((res) => {
      if (isMounted) {
        setIsBackendConnected(res.connected);
        if (res.health) setBackendHealth(res.health);
      }
    });

    fetchDispatchedAlerts(undefined, 20).then((alerts) => {
      if (isMounted && alerts && alerts.length > 0) {
        const liveLogs: EventLog[] = alerts.map((a) => ({
          id: `db-alert-${a.id}`,
          timestamp: new Date(a.created_at).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          }),
          agent: 'Executor',
          eventType: 'EXECUTOR_DISPATCH_COMPLETE',
          message: a.message || 'SMS Alert Dispatched to farmer mobile',
          severity: (a.severity?.toUpperCase() || 'HIGH') as any,
        }));
        setEventLogs((prev) => [...liveLogs, ...prev]);
      }
    });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleRunPipeline = async () => {
    setIsRunningPipeline(true);
    try {
      const locClean = selectedLocation.split(',')[0].trim();
      const res = await runAgentPipeline(
        locClean,
        pipelineMode,
        pipelineMode === 'mock' ? selectedScenario : undefined
      );

      if (res) {
        setPipelineResult(res);

        const nowTime = new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        });

        const newLogs: EventLog[] = [
          {
            id: `pipeline-exec-${Date.now()}-3`,
            timestamp: nowTime,
            agent: 'Executor',
            eventType: 'EXECUTOR_DISPATCH_COMPLETE',
            message:
              res.execution_summary ||
              `LangGraph Executor dispatched alerts for ${res.affected_farmers?.length || 0} farmers.`,
            severity: res.alert_required ? 'CRITICAL' : 'HIGH',
          },
          {
            id: `pipeline-exec-${Date.now()}-2`,
            timestamp: nowTime,
            agent: 'Strategist',
            eventType: 'STRATEGIST_EPI_CALCULATED',
            message: `Risk Level: ${res.risk_level || 'CRITICAL'}. Plan: ${res.recommended_actions?.join('; ') || 'Active flood response'}.`,
            severity: 'CRITICAL',
          },
          {
            id: `pipeline-exec-${Date.now()}-1`,
            timestamp: nowTime,
            agent: 'Sentinel',
            eventType: res.threat_detected ? 'SENTINEL_SURGE_DETECTED' : 'HYDRO_TELEMETRY_INGEST',
            message: res.threat_detected
              ? `Threat Identified: ${res.threat?.event_type || 'Heavy Rain'} (${res.threat?.severity || 'HIGH'}). Confidence: ${Math.round((res.threat?.confidence || 0.92) * 100)}%.`
              : `Observation nominal for ${res.location}. Live satellite & gauge telemetry within safety bounds.`,
            severity: res.threat_detected ? 'HIGH' : 'LOW',
          },
        ];

        setEventLogs((prev) => [...newLogs, ...prev]);
      }
    } catch (err) {
      console.error('Failed to run agentic pipeline:', err);
    } finally {
      setIsRunningPipeline(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* 1. Today's Meteorological Conditions */}
      <GoogleWeatherCard locationName={selectedLocation} />

      {/* 2. Real-Time Autonomous Pipeline Control Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-xs flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold font-mono border ${
                isBackendConnected
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                  : 'bg-amber-50 text-amber-800 border-amber-300'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isBackendConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
                }`}
              />
              <span>
                {isBackendConnected
                  ? 'FASTAPI BACKEND: ONLINE'
                  : 'AUTONOMOUS STANDALONE MODE'}
              </span>
            </span>

            <button
              type="button"
              onClick={() => {
                setBackendUrlInput(getBackendUrl());
                setIsBackendModalOpen(true);
              }}
              title="Configure FastAPI Backend URL"
              className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
            >
              <Settings className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-500 font-medium">Mode:</span>
            <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-50 text-xs font-medium">
              <button
                type="button"
                onClick={() => setPipelineMode('live')}
                className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                  pipelineMode === 'live'
                    ? 'bg-white shadow-xs font-bold text-blue-600'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Live Weather
              </button>
              <button
                type="button"
                onClick={() => setPipelineMode('mock')}
                className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                  pipelineMode === 'mock'
                    ? 'bg-white shadow-xs font-bold text-blue-600'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                SIH Simulation
              </button>
            </div>
          </div>

          {pipelineMode === 'mock' && (
            <div className="flex items-center gap-1.5 text-xs">
              <span className="text-slate-500 font-medium">Scenario:</span>
              <select
                value={selectedScenario}
                onChange={(e) => setSelectedScenario(e.target.value)}
                className="px-2 py-1 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="heavy_rain">Heavy Rainfall (Flash Flood)</option>
                <option value="heatwave">Extreme Heatwave</option>
                <option value="thunderstorm">Severe Thunderstorm</option>
              </select>
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={handleRunPipeline}
          disabled={isRunningPipeline}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition-all shadow-xs flex items-center gap-2 shrink-0 self-end lg:self-auto cursor-pointer"
        >
          {isRunningPipeline ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Executing LangGraph Pipeline...</span>
            </>
          ) : (
            <>
              <Zap className="w-4 h-4 text-amber-300 fill-amber-300" />
              <span>Execute Multi-Agent Pipeline</span>
            </>
          )}
        </button>
      </div>

      {/* Pipeline Execution Result Flash Banner */}
      {pipelineResult && (
        <div className="bg-blue-50 border border-blue-200 rounded-2xl p-4 sm:p-5 shadow-xs animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-blue-100 text-blue-800 rounded-xl mt-0.5 shrink-0">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="text-sm font-bold text-slate-900">
                    Agentic Workflow Completed for {pipelineResult.location}
                  </h3>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold font-mono bg-blue-200 text-blue-900">
                    RISK: {pipelineResult.risk_level?.toUpperCase() || 'HIGH'}
                  </span>
                  <span className="text-xs text-slate-500">
                    {new Date(pipelineResult.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                <p className="text-xs text-slate-700 mt-1 font-medium leading-normal">
                  {pipelineResult.execution_summary ||
                    'Sentinel evaluated sensor stream -> Strategist created targeted farmer mitigations -> Executor dispatched emergency advisories.'}
                </p>

                {pipelineResult.affected_farmers && pipelineResult.affected_farmers.length > 0 && (
                  <div className="mt-2 flex items-center gap-2 text-xs flex-wrap">
                    <span className="font-semibold text-slate-800">Evaluated Farmers:</span>
                    {pipelineResult.affected_farmers.map((f, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 bg-white border border-slate-200 rounded text-slate-700 text-[11px]"
                      >
                        {f.name} ({f.crop})
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <button
              type="button"
              onClick={() => setPipelineResult(null)}
              className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-blue-100/50 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* 3. Autonomous Multi-Agent Pipeline (Sentinel, Strategist, Executor) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Sentinel Agent */}
        <div
          id="agent-card-sentinel"
          className="bg-white rounded-2xl border border-red-200 p-5 shadow-sm flex flex-col justify-between transition-all duration-200 transform hover:scale-[1.02] hover:-translate-y-1 hover:shadow-lg cursor-pointer"
        >
          <div>
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900">{t('agent.sentinel', 'Sentinel')}</h3>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded border text-red-600 bg-red-50 border-red-200">
                {pipelineResult?.threat?.severity || t('common.high', 'High')}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {t('agent.sentinel.desc', 'Detects weather threats & anomalies')}
            </p>

            <div className="flex items-center justify-between text-xs mt-2.5 pt-2.5 border-t border-slate-100">
              <div className="flex items-center gap-1.5 text-emerald-600 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{t('common.completed', 'Completed')}</span>
              </div>
              <span className="font-mono text-slate-400 text-[11px]">
                {pipelineResult ? new Date(pipelineResult.timestamp).toLocaleTimeString() : '19:56:42'}
              </span>
            </div>

            <div className="mt-3 space-y-2 text-xs">
              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">
                  {t('common.input', 'Input')}
                </span>
                <p className="text-slate-800 font-medium">
                  {pipelineMode === 'live' ? 'Live Open-Meteo Satellite Telemetry' : 'SIH Synthesized Radar Telemetry'}
                </p>
              </div>

              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">
                  {t('common.output', 'Output')}
                </span>
                <p className="text-slate-800 font-medium">
                  {pipelineResult?.threat
                    ? `${pipelineResult.threat.event_type} (${pipelineResult.threat.severity}) detected in ${pipelineResult.location}`
                    : t('agent.sentinel.output', 'Heavy rainfall identified, Patiala district')}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-100 space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">{t('common.eventType', 'Event:')}</span>
              <span className="text-slate-800 font-medium">
                {pipelineResult?.threat?.event_type || t('agent.sentinel.eventType', 'Heavy rainfall')}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">{t('common.threat', 'Threat:')}</span>
              <span className="text-amber-700 font-semibold">
                {pipelineResult?.threat_detected ? 'Active Hydrological Threat' : t('agent.sentinel.threat', 'Flash flood risk')}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">{t('common.confidence', 'Confidence:')}</span>
              <span className="text-slate-900 font-mono font-medium">
                {pipelineResult?.threat?.confidence ? `${Math.round(pipelineResult.threat.confidence * 100)}%` : '92%'}
              </span>
            </div>
          </div>
        </div>

        {/* Strategist Agent */}
        <div
          id="agent-card-strategist"
          className="bg-white rounded-2xl border border-amber-200 p-5 shadow-sm flex flex-col justify-between transition-all duration-200 transform hover:scale-[1.02] hover:-translate-y-1 hover:shadow-lg cursor-pointer"
        >
          <div>
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900">{t('agent.strategist', 'Strategist')}</h3>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded border text-amber-700 bg-amber-50 border-amber-200">
                {pipelineResult?.risk_level?.toUpperCase() || t('common.high', 'High')}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {t('agent.strategist.desc', 'Evaluates risk & builds response plans')}
            </p>

            <div className="flex items-center justify-between text-xs mt-2.5 pt-2.5 border-t border-slate-100">
              <div className="flex items-center gap-1.5 text-emerald-600 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{t('common.completed', 'Completed')}</span>
              </div>
              <span className="font-mono text-slate-400 text-[11px]">
                {pipelineResult ? new Date(pipelineResult.timestamp).toLocaleTimeString() : '19:58:10'}
              </span>
            </div>

            <div className="mt-3 space-y-2 text-xs">
              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">
                  {t('common.input', 'Input')}
                </span>
                <p className="text-slate-800 font-medium">
                  Sentinel threat event + PAU crop database
                </p>
              </div>

              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">
                  {t('common.output', 'Output')}
                </span>
                <p className="text-slate-800 font-medium">
                  {pipelineResult?.recommended_actions && pipelineResult.recommended_actions.length > 0
                    ? pipelineResult.recommended_actions[0]
                    : 'Evacuation Priority Index & irrigation hold order'}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-100 space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Farmers Evaluated:</span>
              <span className="text-slate-800 font-medium font-mono">
                {pipelineResult?.affected_farmers?.length ?? 5} registered
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Replanning Needed:</span>
              <span className="text-amber-700 font-semibold font-mono">
                {pipelineResult?.replanning_required ? 'YES (Active)' : 'YES'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Alert Triggered:</span>
              <span className="text-red-600 font-mono font-bold">
                {pipelineResult?.alert_required ? 'TRUE (Emergency)' : 'TRUE'}
              </span>
            </div>
          </div>
        </div>

        {/* Executor Agent */}
        <div
          id="agent-card-executor"
          className="bg-white rounded-2xl border border-blue-500 p-5 shadow-sm flex flex-col justify-between relative transition-all duration-200 transform hover:scale-[1.02] hover:-translate-y-1 hover:shadow-lg cursor-pointer"
        >
          <div>
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900">{t('agent.executor', 'Executor')}</h3>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded border text-blue-600 bg-blue-50 border-blue-200">
                Active
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {t('agent.executor.desc', 'Dispatches emergency response')}
            </p>

            <div className="flex items-center justify-between text-xs mt-2.5 pt-2.5 border-t border-slate-100">
              <div className="flex items-center gap-1.5 text-blue-600 font-semibold">
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-600" />
                </span>
                <span>{pipelineResult ? 'Dispatched' : '• Monitoring'}</span>
              </div>
              <span className="font-mono text-slate-400 text-[11px]">
                {pipelineResult ? new Date(pipelineResult.timestamp).toLocaleTimeString() : '20:00:22'}
              </span>
            </div>

            <div className="mt-3 space-y-2 text-xs">
              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">
                  {t('common.input', 'Input')}
                </span>
                <p className="text-slate-800 font-medium">
                  Strategist response directives & SMS channels
                </p>
              </div>

              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">
                  {t('common.output', 'Output')}
                </span>
                <p className="text-blue-700 font-medium">
                  {pipelineResult?.execution_summary || 'Tri-lingual SMS broadcast & SQLite audit records'}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-100 space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Dispatch Status:</span>
              <span className="text-blue-600 font-medium font-mono">
                {pipelineResult?.status === 'completed' ? 'DELIVERED / LOGGED' : 'STANDBY'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Audit Record ID:</span>
              <span className="text-slate-800 font-mono font-medium">
                {pipelineResult?.audit_event_id ? `#THREAT-${pipelineResult.audit_event_id}` : '#AUDIT-2026-981'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Delivery Channels:</span>
              <span className="text-emerald-700 font-semibold font-mono">SMS, WhatsApp, DLR</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Lower Two Summary Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Emergency Response Command */}
        <div
          id="card-emergency-response"
          className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between transition-all duration-200 transform hover:scale-[1.02] hover:-translate-y-1 hover:shadow-lg cursor-pointer"
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-red-600" />
                <h3 className="text-base font-bold text-slate-900">
                  {t('emergency.title', 'Emergency Response Command')}
                </h3>
              </div>
              <span className="text-xs font-bold px-2 py-0.5 bg-red-100 text-red-700 border border-red-200 rounded font-mono">
                {pipelineResult?.risk_level?.toUpperCase() || 'CRITICAL'}
              </span>
            </div>

            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">{t('emergency.threatLabel', 'Threat')}:</span>
                <span className="font-semibold text-slate-900">
                  {pipelineResult?.threat?.event_type || 'Flash flood — Ward 12–14'}
                </span>
              </div>

              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">{t('emergency.popLabel', 'Exposed')}:</span>
                <span className="font-bold text-red-600 font-mono">42,000 residents</span>
              </div>

              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">{t('emergency.epiLabel', 'EPI Index')}:</span>
                <span className="font-bold text-slate-900 font-mono">8.4 / 10.0 (Mandatory)</span>
              </div>

              <div className="flex justify-between py-1">
                <span className="text-slate-500">{t('emergency.basinLabel', 'Basin')}:</span>
                <span className="text-slate-800 font-medium">Ghaggar & Badi Nadi</span>
              </div>
            </div>

            <div className="bg-slate-50 rounded-xl p-3 border border-slate-100 text-xs">
              <span className="font-semibold text-slate-700 block mb-1">
                {t('common.keyEmergencyActions', 'Key Directives:')}
              </span>
              <ul className="space-y-0.5 text-slate-600">
                <li>
                  • {language === 'pa'
                    ? 'ਵਾਰਡ 12-14 ਵਿੱਚ ਹੇਠਲੀ ਮੰਜ਼ਿਲ ਦੇ ਮਕਾਨ ਤੁਰੰਤ ਖਾਲੀ ਕਰੋ'
                    : language === 'hi'
                    ? 'वार्ड 12–14 में भूतल के आवास खाली करें'
                    : 'Evacuate ground-floor dwellings in Ward 12–14'}
                </li>
                <li>
                  • {language === 'pa'
                    ? 'ਘੱਗਰ ਅਤੇ ਵੱਡੀ ਨਦੀ ਪੁਲਾਂ ਤੋਂ ਆਵਾਜਾਈ ਮੁਲਤਵੀ ਰੱਖੋ'
                    : language === 'hi'
                    ? 'घग्गर व बड़ी नदी पारगमन स्थगित रखें'
                    : 'Suspend transit across Ghaggar and Badi Nadi crossings'}
                </li>
              </ul>
            </div>
          </div>

          <button
            type="button"
            onClick={() => onNavigateTab('emergency')}
            className="mt-4 w-full py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-xl transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
          >
            <span>{t('emergency.btn', 'View Emergency Directives')}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Agricultural Advisory Command */}
        <div
          id="card-agricultural-advisory"
          className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between transition-all duration-200 transform hover:scale-[1.02] hover:-translate-y-1 hover:shadow-lg cursor-pointer"
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sprout className="w-5 h-5 text-emerald-600" />
                <h3 className="text-base font-bold text-slate-900">
                  {t('agri.title', 'Agricultural Advisory Command')}
                </h3>
              </div>
              <span className="text-xs font-bold px-2 py-0.5 bg-amber-100 text-amber-800 border border-amber-200 rounded font-mono">
                PAU ADVISORY
              </span>
            </div>

            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">{t('agri.targetCropsLabel', 'Target Crops')}:</span>
                <span className="font-semibold text-slate-900">
                  {t('agri.targetCropsValue', 'Paddy (PR-126), Cotton')}
                </span>
              </div>

              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">{t('agri.stageLabel', 'Crop Stage')}:</span>
                <span className="text-slate-800 font-medium">Flowering / Grain Filling</span>
              </div>

              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">{t('agri.irrigationHoldLabel', 'Irrigation Hold')}:</span>
                <span className="font-bold text-amber-700 font-mono">
                  {t('agri.irrigationHoldValue', '48 Hours Recommended')}
                </span>
              </div>

              <div className="flex justify-between py-1">
                <span className="text-slate-500">{t('agri.advisoryIdLabel', 'Authority')}:</span>
                <span className="text-slate-800 font-medium">Punjab Agricultural University</span>
              </div>
            </div>

            <div className="bg-slate-50 rounded-xl p-3 border border-slate-100 text-xs">
              <span className="font-semibold text-slate-700 block mb-1">
                {t('common.keyFarmerAdvisory', 'Key Farmer Directives:')}
              </span>
              <p className="text-slate-600 leading-normal">
                {language === 'pa'
                  ? 'ਝੋਨੇ ਦੀਆਂ ਜੜ੍ਹਾਂ ਬਚਾਉਣ ਲਈ ਸ਼ਾਮ ਤੋਂ ਪਹਿਲਾਂ ਨਿਕਾਸੀ ਨਾਲੀਆਂ ਖੋਲ੍ਹੋ। ਮੀਂਹ ਦੌਰਾਨ ਕੋਈ ਵੀ ਸਪਰੇਅ ਨਾ ਕਰੋ।'
                  : language === 'hi'
                  ? 'जड़ हाइपोक्सिया रोकने हेतु शाम से पहले निकासी नालियां खोलें। वर्षा के दौरान छिड़काव स्थगित रखें।'
                  : 'Open field drainage cuts before nightfall to prevent root hypoxia. Suspend foliar sprays during rainfall window.'}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => onNavigateTab('agriculture')}
            className="mt-4 w-full py-2 bg-emerald-800 hover:bg-emerald-900 text-white text-xs font-semibold rounded-xl transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
          >
            <span>{t('agri.btn', 'View Agricultural Advisory')}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 5. Live Multi-Agent Event Log Table */}
      <div id="event-log-container" className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-slate-600" />
            <h3 className="text-base font-bold text-slate-900">
              {t('log.title', 'Live Multi-Agent Event Log')}
            </h3>
          </div>
          <span className="font-mono text-xs text-slate-400">
            {eventLogs.length} verified events logged
          </span>
        </div>

        <div className="overflow-x-auto -mx-6 px-6">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 font-mono text-[11px]">
                <th className="py-2.5 pr-4 font-normal">{t('log.timestamp', 'Timestamp')}</th>
                <th className="py-2.5 px-4 font-normal">{t('log.agent', 'Agent')}</th>
                <th className="py-2.5 px-4 font-normal">{t('log.eventType', 'Event Type')}</th>
                <th className="py-2.5 px-4 font-normal">{t('log.message', 'Message / Outcome')}</th>
                <th className="py-2.5 pl-4 font-normal text-right">{t('log.severity', 'Severity')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {eventLogs.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3.5 pr-4 font-mono text-slate-500 whitespace-nowrap">{item.timestamp}</td>
                  <td className="py-3.5 px-4 font-semibold text-slate-900 whitespace-nowrap">
                    {t('agent.name.' + item.agent, item.agent)}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-[11px] text-slate-500 whitespace-nowrap">
                    {t('event.' + item.eventType, item.eventType)}
                  </td>
                  <td className="py-3.5 px-4 text-slate-700 min-w-[320px]">
                    {t('log.msg.' + item.id, item.message)}
                  </td>
                  <td className="py-3.5 pl-4 text-right whitespace-nowrap">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                        item.severity === 'CRITICAL'
                          ? 'bg-red-100 text-red-700'
                          : item.severity === 'HIGH'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {item.severity}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Backend URL Configuration Modal */}
      {isBackendModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-md w-full p-5 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Server className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">FastAPI Backend Connection</h3>
              </div>
              <button
                type="button"
                onClick={() => setIsBackendModalOpen(false)}
                className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="mt-3 text-xs text-slate-600 space-y-2">
              <p>
                Connect your frontend directly with your Python FastAPI server (running on <code>http://127.0.0.1:8000</code> or deployed on Render/Railway).
              </p>
              <p className="text-[11px] text-slate-500">
                Default for local testing is <code>http://127.0.0.1:8000</code>.
              </p>
            </div>

            <div className="mt-3">
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                Backend Base URL
              </label>
              <input
                type="text"
                value={backendUrlInput}
                onChange={(e) => setBackendUrlInput(e.target.value)}
                placeholder="http://127.0.0.1:8000"
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
              />
            </div>

            <div className="mt-4 flex items-center justify-between gap-2">
              <button
                type="button"
                onClick={() => {
                  setBackendUrl('');
                  setBackendUrlInput('');
                  setIsBackendModalOpen(false);
                  checkBackendHealth().then((res) => setIsBackendConnected(res.connected));
                }}
                className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-600 hover:bg-slate-50 cursor-pointer"
              >
                Reset Default
              </button>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsBackendModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setBackendUrl(backendUrlInput.trim());
                    setIsBackendModalOpen(false);
                    checkBackendHealth().then((res) => {
                      setIsBackendConnected(res.connected);
                      if (res.health) setBackendHealth(res.health);
                    });
                  }}
                  className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs cursor-pointer"
                >
                  Save & Connect
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
