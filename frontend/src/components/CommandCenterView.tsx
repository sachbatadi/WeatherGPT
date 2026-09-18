import React from 'react';
import { useLanguage } from '../context/LanguageContext';
import { GoogleWeatherCard } from './GoogleWeatherCard';
import { INITIAL_EVENT_LOGS } from '../data/mockData';
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

  return (
    <div className="space-y-6 pb-12">
      {/* 1. Today's Meteorological Conditions (White Background Telemetry Card) */}
      <GoogleWeatherCard locationName={selectedLocation} />

      {/* 2. Top Alert Banner */}
      <div
        id="banner-heavy-rainfall"
        className="rounded-2xl border border-amber-300/80 bg-amber-50/60 p-4 sm:p-5 shadow-sm transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
      >
        <div className="flex items-start gap-3.5">
          <div className="p-2 bg-amber-100 text-amber-800 rounded-xl border border-amber-300/60 shrink-0 mt-0.5">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-base font-bold text-slate-900">
                {t('banner.title', 'Heavy rainfall event identified in Patiala district')}
              </h2>
              <span className="inline-flex items-center px-2 py-0.5 text-[11px] font-semibold rounded-full bg-amber-200/70 text-amber-900 border border-amber-300/80">
                {t('banner.status', 'Active Monitoring')}
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-1 max-w-3xl leading-normal">
              {t(
                'banner.desc',
                'Localized flash flood risk along Ghaggar basin. 42,000 population exposed across low-lying wards. Multi-agent emergency pipeline active.'
              )}
            </p>
          </div>
        </div>

        <button
          id="btn-view-risk-map-banner"
          type="button"
          onClick={() => onNavigateTab('risk')}
          className="shrink-0 flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-xl shadow-xs transition-all self-end md:self-auto"
        >
          <span>{t('banner.viewRiskMap', 'View Risk Map')}</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* 2. Autonomous Multi-Agent Pipeline (Sentinel, Strategist, Executor) */}
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
                {t('common.high', 'High')}
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
              <span className="font-mono text-slate-400 text-[11px]">19:56:42</span>
            </div>

            <div className="mt-3 space-y-2 text-xs">
              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">
                  {t('common.input', 'Input')}
                </span>
                <p className="text-slate-800 font-medium">
                  {t('agent.sentinel.input', 'Live radar telemetry stream')}
                </p>
              </div>

              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">
                  {t('common.output', 'Output')}
                </span>
                <p className="text-slate-800 font-medium">
                  {t('agent.sentinel.output', 'Heavy rainfall identified, Patiala district')}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-100 space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">{t('common.eventType', 'Event:')}</span>
              <span className="text-slate-800 font-medium">{t('agent.sentinel.eventType', 'Heavy rainfall')}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">{t('common.threat', 'Threat:')}</span>
              <span className="text-amber-700 font-semibold">{t('agent.sentinel.threat', 'Flash flood risk')}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">{t('common.confidence', 'Confidence:')}</span>
              <span className="text-slate-900 font-mono font-medium">87%</span>
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
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded border text-red-600 bg-red-50 border-red-200">
                {t('common.high', 'High')}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {t('agent.strategist.desc', 'Evaluates risks & recommended actions')}
            </p>

            <div className="flex items-center justify-between text-xs mt-2.5 pt-2.5 border-t border-slate-100">
              <div className="flex items-center gap-1.5 text-emerald-600 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{t('common.completed', 'Completed')}</span>
              </div>
              <span className="font-mono text-slate-400 text-[11px]">19:58:12</span>
            </div>

            <div className="mt-3 space-y-2 text-xs">
              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">
                  {t('common.input', 'Input')}
                </span>
                <p className="text-slate-800 font-medium">
                  {t('agent.strategist.input', 'Sentinel detection output')}
                </p>
              </div>

              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">
                  {t('common.output', 'Output')}
                </span>
                <p className="text-slate-800 font-medium">
                  {t('agent.strategist.output', 'Risk assessment for 3 sectors')}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-100 space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">{t('common.sectors', 'Sectors:')}</span>
              <span className="text-slate-800 font-medium text-right truncate max-w-[140px]">
                {t('agent.strategist.sectors', 'Agri, Safety, Transport')}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">{t('common.population', 'Population:')}</span>
              <span className="text-slate-900 font-mono font-medium">42,000</span>
            </div>
            <div className="pt-0.5 text-[11px] text-slate-600 space-y-0.5">
              <span className="text-slate-500 block">{t('common.actions', 'Actions:')}</span>
              <p className="leading-tight">• {t('agent.strategist.action1', 'Advisory for standing crops')}</p>
              <p className="leading-tight">• {t('agent.strategist.action2', 'Pre-position rescue teams in low wards')}</p>
            </div>
          </div>
        </div>

        {/* Executor Agent - ACTIVE / PROCESSING with blue border */}
        <div
          id="agent-card-executor"
          className="bg-white rounded-2xl border-2 border-blue-500 p-5 shadow-sm flex flex-col justify-between relative transition-all duration-200 transform hover:scale-[1.02] hover:-translate-y-1 hover:shadow-lg cursor-pointer"
        >
          <div>
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900">{t('agent.executor', 'Executor')}</h3>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded border text-red-600 bg-red-50 border-red-200">
                {t('common.high', 'High')}
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
                <span>{t('common.processing', '• Processing')}</span>
              </div>
              <span className="font-mono text-slate-400 text-[11px]">20:00:22</span>
            </div>

            <div className="mt-3 space-y-2 text-xs">
              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">
                  {t('common.input', 'Input')}
                </span>
                <p className="text-slate-800 font-medium">
                  {t('agent.executor.input', 'Strategist response directives')}
                </p>
              </div>

              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-mono">
                  {t('common.output', 'Output')}
                </span>
                <p className="text-blue-700 font-medium">
                  {t('agent.executor.output', 'Dispatching notifications')}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-100 space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">{t('common.status', 'Status:')}</span>
              <span className="text-blue-600 font-medium font-mono">{t('common.inProgress', 'in progress')}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">{t('common.notifications', 'Dispatched:')}</span>
              <span className="text-slate-900 font-mono font-medium">8,400</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">{t('common.escalated', 'SDRF Alert:')}</span>
              <span className="text-emerald-700 font-medium font-mono">Yes</span>
            </div>
          </div>
        </div>

      </div>

      {/* 3. Lower Two Summary Cards */}
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
                <h3 className="text-base font-bold text-slate-900">{t('emergency.title', 'Emergency Response Command')}</h3>
              </div>
              <span className="text-xs font-bold px-2 py-0.5 bg-red-100 text-red-700 border border-red-200 rounded font-mono">
                {t('common.critical', 'CRITICAL')}
              </span>
            </div>

            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">{t('emergency.threatLabel', 'Threat')}:</span>
                <span className="font-semibold text-slate-900">
                  {t('emergency.threatValue', 'Flash flood — Ward 12–14')}
                </span>
              </div>

              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">{t('emergency.popLabel', 'Exposed')}:</span>
                <span className="font-bold text-red-600 font-mono">
                  {t('emergency.popValue', '42,000 residents')}
                </span>
              </div>

              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">{t('emergency.epiLabel', 'EPI Index')}:</span>
                <span className="font-bold text-slate-900 font-mono">
                  {t('emergency.epiValue', '8.4 / 10.0 (Mandatory)')}
                </span>
              </div>

              <div className="flex justify-between py-1">
                <span className="text-slate-500">{t('emergency.basinLabel', 'Basin')}:</span>
                <span className="text-slate-800 font-medium">
                  {t('emergency.basinValue', 'Ghaggar & Badi Nadi')}
                </span>
              </div>
            </div>

            <div className="bg-slate-50 rounded-xl p-3 border border-slate-100 text-xs">
              <span className="font-semibold text-slate-700 block mb-1">
                {t('common.keyEmergencyActions', 'Key Directives:')}
              </span>
              <ul className="space-y-0.5 text-slate-600">
                <li>• {language === 'pa' ? 'ਵਾਰਡ 12-14 ਵਿੱਚ ਹੇਠਲੀ ਮੰਜ਼ਿਲ ਦੇ ਮਕਾਨ ਤੁਰੰਤ ਖਾਲੀ ਕਰੋ' : language === 'hi' ? 'वार्ड 12–14 में भूतल के आवास खाली करें' : 'Evacuate ground-floor dwellings in Ward 12–14'}</li>
                <li>• {language === 'pa' ? 'ਘੱਗਰ ਅਤੇ ਵੱਡੀ ਨਦੀ ਪੁਲਾਂ ਤੋਂ ਆਵਾਜਾਈ ਮੁਲਤਵੀ ਰੱਖੋ' : language === 'hi' ? 'घग्गर व बड़ी नदी पारगमन स्थगित रखें' : 'Suspend transit across Ghaggar and Badi Nadi crossings'}</li>
              </ul>
            </div>
          </div>

          <button
            type="button"
            onClick={() => onNavigateTab('emergency')}
            className="mt-4 w-full py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-xl transition-colors flex items-center justify-center gap-1.5"
          >
            <span>{t('emergency.btn', 'View Emergency Console')}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Agriculture Advisory */}
        <div
          id="card-agriculture-advisory"
          className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between transition-all duration-200 transform hover:scale-[1.02] hover:-translate-y-1 hover:shadow-lg cursor-pointer"
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sprout className="w-5 h-5 text-emerald-600" />
                <h3 className="text-base font-bold text-slate-900">{t('agri.title', 'Agriculture Advisory')}</h3>
              </div>
              <span className="text-xs font-bold px-2 py-0.5 bg-amber-100 text-amber-800 border border-amber-200 rounded font-mono">
                {t('common.highRisk', 'HIGH RISK')}
              </span>
            </div>

            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">{t('agri.cropLabel', 'Crop')}:</span>
                <span className="font-semibold text-slate-900">
                  {t('agri.cropValue', 'Paddy / Basmati Rice')}
                </span>
              </div>

              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">{t('agri.areaLabel', 'Command Area')}:</span>
                <span className="font-mono text-slate-800">{t('agri.areaValue', '8,200 ha')}</span>
              </div>

              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">{t('agri.moistureLabel', 'Soil Moisture')}:</span>
                <span className="font-bold text-amber-700 font-mono">
                  {t('agri.moistureValue', '42.5% (Capacity: 38%)')}
                </span>
              </div>

              <div className="flex justify-between py-1">
                <span className="text-slate-500">{t('agri.zoneLabel', 'Zone')}:</span>
                <span className="text-slate-800 font-medium">
                  {t('agri.zoneValue', 'Trans-Gangetic Plain (Punjab)')}
                </span>
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
            className="mt-4 w-full py-2 bg-emerald-800 hover:bg-emerald-900 text-white text-xs font-semibold rounded-xl transition-colors flex items-center justify-center gap-1.5"
          >
            <span>{t('agri.btn', 'View Agricultural Advisory')}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 4. Live Multi-Agent Event Log Table */}
      <div id="event-log-container" className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-slate-600" />
            <h3 className="text-base font-bold text-slate-900">{t('log.title', 'Live Multi-Agent Event Log')}</h3>
          </div>
          <span className="font-mono text-xs text-slate-400">{t('log.subtitle', 'Real-time trace')}</span>
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
              {INITIAL_EVENT_LOGS.map((item) => (
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
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {t('common.' + item.severity.toLowerCase(), item.severity)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
