import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { EmergencyHelplineBar } from './EmergencyHelplineBar';
import { EMERGENCY_ACTIONS } from '../data/mockData';
import { EmergencyActionItem } from '../types';
import {
  FileCode,
  Users,
  Activity,
  AlertTriangle,
  Clock,
  Calendar,
  MapPin,
  Building2,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  X,
} from 'lucide-react';

export const DisasterEmergencyView: React.FC = () => {
  const { t, language } = useLanguage();
  const [actions, setActions] = useState<EmergencyActionItem[]>(EMERGENCY_ACTIONS);
  const [isCapModalOpen, setIsCapModalOpen] = useState<boolean>(false);
  const [showRawCap, setShowRawCap] = useState<boolean>(false);

  const toggleActionStatus = (id: string) => {
    setActions((prev) =>
      prev.map((act) => {
        if (act.id !== id) return act;
        const nextStatus =
          act.status === 'In Progress' ? 'Completed' : act.status === 'Pending' ? 'In Progress' : 'Pending';
        return { ...act, status: nextStatus };
      })
    );
  };

  return (
    <div className="space-y-6 pb-12 font-sans">
      {/* 1. TOP OVERVIEW: Detected Threat & Active Alerts (Side-by-Side) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Card 1: Flash Flood Inundation Warning */}
        <div
          id="card-flash-flood-warning"
          className="bg-white rounded-2xl border border-red-200 p-5 shadow-sm relative overflow-hidden flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold tracking-wider text-red-600 uppercase font-mono flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-red-600 animate-ping" />
                {t('deoc.threatHeading', 'DETECTED THREAT')}
              </span>
              <span className="px-2.5 py-0.5 rounded text-xs font-bold font-mono bg-red-100 text-red-700 border border-red-200">
                {t('common.critical', 'Critical')}
              </span>
            </div>

            <div className="mt-2.5">
              <h3 className="text-xl font-bold text-slate-900">{t('deoc.threatName', 'Flash Flood')}</h3>
              <p className="text-sm font-semibold text-slate-700 mt-0.5">
                {t('deoc.threatLocation', 'Patiala District, Ward 12–14')}
              </p>
              <p className="text-xs text-slate-600 mt-1.5 leading-normal">
                {language === 'pa'
                  ? 'ਘੱਗਰ ਵਿੱਚ ਪਾਣੀ ਤੇਜ਼ੀ ਨਾਲ ਵੱਧ ਰਿਹਾ ਹੈ। ਬੜੀ ਨਦੀ ਨੇੜਲੇ ਘਰਾਂ ਵਿੱਚ ਹੜ੍ਹ ਦਾ ਖ਼ਤਰਾ।'
                  : language === 'hi'
                  ? 'घग्गर में पानी तेजी से बढ़ रहा है। बड़ी नदी किनारे के घरों में बाढ़ का खतरा।'
                  : 'Water rising fast along Ghaggar. Immediate flood risk for homes near Badi Nadi.'}
              </p>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs font-bold text-red-600 font-mono">
              {language === 'pa'
                ? 'ਨਿਕਾਸੀ ਤਰਜੀਹ: 8.4 / 10 (ਲਾਜ਼ਮੀ)'
                : language === 'hi'
                ? 'निकासी प्राथमिकता: 8.4 / 10 (अनिवार्य)'
                : 'Evacuation Priority: 8.4 / 10 (Mandatory)'}
            </span>
          </div>
        </div>

        {/* Card 2: Active Alerts & Dispatch Status */}
        <div
          id="card-active-alerts"
          className="bg-white rounded-2xl border border-amber-200 p-5 shadow-sm flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-2.5">
              <h3 className="text-base font-bold text-slate-900">
                {t('deoc.activeAlerts', 'Active Alerts & Dispatch Status')}
              </h3>
              <span className="text-xs font-mono text-slate-400">{t('deoc.capFeed', 'CAP Feed v1.2')}</span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="p-2.5 bg-red-50/60 border border-red-200/70 rounded-xl transition-all duration-200 transform hover:scale-[1.02] hover:shadow-md cursor-pointer">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-red-900">
                    {t('deoc.alert1', 'Flash flood warning — Ward 12–14')}
                  </span>
                  <span className="font-mono text-[10px] text-red-600 font-bold uppercase">
                    {t('common.cellBroadcast', 'Cell Broadcast')}
                  </span>
                </div>
                <p className="text-slate-600 mt-0.5 text-[11px] leading-normal">
                  {language === 'pa'
                    ? 'ਦਰਿਆ 14.82m ਤੇ (ਖ਼ਤਰਾ 14.50m)। ਨੀਵੇਂ ਇਲਾਕਿਆਂ ਦੇ ਲੋਕ ਸੁਰੱਖਿਅਤ ਥਾਂ ਜਾਣ।'
                    : language === 'hi'
                    ? 'नदी 14.82m पर (खतरा 14.50m)। निचले क्षेत्र तुरंत सुरक्षित स्थान पर जाएं।'
                    : 'River at 14.82m (danger: 14.50m). Low areas must move to safety.'}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2.5 pt-0.5">
                <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100 transition-all duration-200 transform hover:scale-105 hover:-translate-y-0.5 hover:shadow-md hover:bg-white hover:border-slate-300 cursor-pointer">
                  <span className="text-slate-500 text-[11px] block">{t('common.alertsDispatched', 'Alerts Dispatched:')}</span>
                  <span className="font-mono text-base font-bold text-slate-900">8,400</span>
                  <span className="text-[10px] text-slate-400 block font-mono">{t('common.cellBroadcastActive', 'Cell Broadcast Active')}</span>
                </div>
                <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100 transition-all duration-200 transform hover:scale-105 hover:-translate-y-0.5 hover:shadow-md hover:bg-white hover:border-slate-300 cursor-pointer">
                  <span className="text-slate-500 text-[11px] block">{t('common.stateEscalation', 'State Escalation:')}</span>
                  <span className="font-mono text-base font-bold text-red-600">{t('common.yes', 'Yes')}</span>
                  <span className="text-[10px] text-slate-400 block font-mono">{t('common.sdrfNotified', 'SDRF Notified')}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. OPERATIONS & POPULATION/TELEMETRY (Side-by-Side 2-Column Grid) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* LEFT COLUMN: Response Actions (DEOC Protocol) */}
        <div id="card-response-actions" className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  {t('deoc.responseActions', 'Response Actions')}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Standard Operating Procedures & Checklist
                </p>
              </div>
              <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded">{t('deoc.deocProtocol', 'DEOC Protocol')}</span>
            </div>

            <div className="space-y-2.5">
              {actions.map((act) => {
                const isDone = act.status === 'Completed';
                const isInProg = act.status === 'In Progress';
                return (
                  <div
                    key={act.id}
                    className={`p-3 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 transition-all duration-200 transform hover:scale-[1.02] hover:shadow-md cursor-pointer ${
                      isDone
                        ? 'bg-emerald-50/40 border-emerald-200 hover:bg-emerald-50/80'
                        : isInProg
                        ? 'bg-blue-50/30 border-blue-200 hover:bg-blue-50/60'
                        : 'bg-slate-50/60 border-slate-200 hover:bg-white hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-start gap-2.5">
                      <span className="font-mono text-xs font-bold text-slate-400 shrink-0 mt-0.5">
                        {act.stepNumber}
                      </span>
                      <div>
                        <p className={`text-xs font-medium ${isDone ? 'text-slate-500 line-through' : 'text-slate-800'}`}>
                          {t('emergency.action.title.' + act.id, act.title)}
                        </p>
                        <span className="text-[10px] text-slate-400 font-mono block">
                          {t('emergency.action.deadline.' + act.id, act.deadline)}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 self-end sm:self-auto shrink-0">
                      <span
                        className={`text-[10px] font-bold font-mono px-2 py-0.5 rounded ${
                          isDone
                            ? 'bg-emerald-100 text-emerald-700'
                            : isInProg
                            ? 'bg-blue-100 text-blue-700'
                            : 'bg-slate-200 text-slate-700'
                        }`}
                      >
                        {isDone
                          ? t('common.completed', 'Completed')
                          : isInProg
                          ? t('common.inProgress', 'In Progress')
                          : t('common.pending', 'Pending')}
                      </span>

                      <button
                        type="button"
                        onClick={() => toggleActionStatus(act.id)}
                        className={`text-[11px] px-2 py-0.5 rounded-lg border font-medium transition-colors ${
                          isDone
                            ? 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                            : 'bg-slate-900 border-slate-900 text-white hover:bg-slate-800'
                        }`}
                      >
                        {isDone ? t('common.reopen', 'Reopen') : t('common.markExecuted', 'Mark Done')}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <button
            type="button"
            onClick={() => {
              setShowRawCap(false);
              setIsCapModalOpen(true);
            }}
            className="mt-4 w-full py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold rounded-xl transition-colors flex items-center justify-center gap-2 border border-slate-200 cursor-pointer shadow-xs"
          >
            <span>{t('deoc.inspectCap', 'View Alert Details')}</span>
          </button>
        </div>

        {/* RIGHT COLUMN: Population Impact + Hydromet Telemetry */}
        <div className="space-y-5">
          {/* Card 1: Population Impact */}
          <div id="card-population-impact" className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold tracking-wider text-slate-400 uppercase font-mono">
                {t('deoc.popImpact', 'POPULATION IMPACT')}
              </span>
              <span className="px-2 py-0.5 rounded text-[11px] font-bold font-mono bg-red-100 text-red-700 border border-red-200">
                {t('common.critical', 'Critical')}
              </span>
            </div>

            <div className="mt-2.5">
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-slate-950 font-mono">42,000</span>
                <span className="text-xs text-slate-500 font-medium">
                  {t('deoc.estPopLabel', 'Estimated affected population')}
                </span>
              </div>

              <ul className="mt-2.5 space-y-1.5 text-xs text-slate-600">
                <li className="flex items-start gap-2">
                  <span className="text-slate-400">•</span>
                  <span>{language === 'pa' ? 'ਨੀਵੇਂ ਖੇਤਰ: ਵਾਰਡ 12–14 (ਬੜੀ ਤੇ ਛੋਟੀ ਨਦੀ)' : language === 'hi' ? 'निचले क्षेत्र: वार्ड 12–14 (बड़ी व छोटी नदी)' : 'Low-lying zones: Wards 12–14 (Badi & Chhoti Nadi)'}</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-400">•</span>
                  <span>{language === 'pa' ? 'ਦਰਿਆਈ ਬਸਤੀਆਂ: ਸਮਾਣਾ ਤੇ ਸਨੌਰ ਬਲਾਕ' : language === 'hi' ? 'नदी किनारे बस्तियां: समाना व सनौर ब्लॉक' : 'Riverbank settlements: Samana & Sanaur'}</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-400">•</span>
                  <span>{language === 'pa' ? '2 ਬਿਜਲੀ ਸਬ-ਸਟੇਸ਼ਨ ਅਤੇ 4 ਪੁਲ ਹਾਈ ਅਲਰਟ ਤੇ' : language === 'hi' ? '2 विद्युत सब-स्टेशन और 4 पुल हाई अलर्ट पर' : '2 power sub-stations & 4 bridges on alert'}</span>
                </li>
              </ul>

              <div className="mt-3 p-2.5 bg-slate-50 rounded-xl border border-slate-100 text-xs flex items-center gap-2 transition-all duration-200 transform hover:scale-[1.02] hover:shadow-md hover:bg-white hover:border-slate-300 cursor-pointer">
                <Users className="w-4 h-4 text-blue-600 shrink-0" />
                <span className="text-slate-700 font-medium">
                  {language === 'pa' ? 'ਰਾਹਤ ਕੈਂਪ: ਸਰਕਾਰੀ ਮਹਿੰਦਰਾ ਕਾਲਜ ਤੇ 3 ਕਮਿਊਨਿਟੀ ਹਾਲ' : language === 'hi' ? 'राहत शिविर: सरकारी महिंद्रा कॉलेज व 3 सामुदायिक भवन' : 'Relief Centers: Govt Mohindra College & 3 Halls'}
                </span>
              </div>
            </div>
          </div>

          {/* Card 2: Operational GIS Threat Map & River Basin Hydromet Telemetry */}
          <div id="card-hydromet-telemetry" className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-600" />
                <h3 className="text-base font-bold text-slate-900">
                  {t('deoc.showGauges', 'River Basin Hydromet Telemetry')}
                </h3>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 bg-red-50 dark:bg-rose-950/50 text-red-700 dark:text-rose-400 border border-red-200 dark:border-rose-900/50 rounded font-semibold">
                LIVE
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              <div className="p-3 bg-red-50/40 dark:bg-zinc-900/80 rounded-xl border border-red-200 dark:border-rose-500/30 transition-all duration-200 transform hover:scale-105 hover:-translate-y-1 hover:shadow-md hover:bg-red-50/70 dark:hover:bg-zinc-850 cursor-pointer">
                <span className="text-xs text-slate-600 dark:text-zinc-400 block font-medium">Ghaggar @ Naraj Bridge</span>
                <span className="text-2xl font-bold font-mono text-red-600 dark:text-rose-400 mt-0.5 block">14.82 m</span>
                <span className="text-[10px] text-red-700 dark:text-rose-300 block font-semibold">Danger: 14.50 m (+0.32m)</span>
              </div>
              <div className="p-3 bg-amber-50/40 dark:bg-zinc-900/80 rounded-xl border border-amber-200 dark:border-amber-500/30 transition-all duration-200 transform hover:scale-105 hover:-translate-y-1 hover:shadow-md hover:bg-amber-50/70 dark:hover:bg-zinc-850 cursor-pointer">
                <span className="text-xs text-slate-600 dark:text-zinc-400 block font-medium">Badi Nadi Catchment</span>
                <span className="text-2xl font-bold font-mono text-amber-600 dark:text-amber-400 mt-0.5 block">6.45 m</span>
                <span className="text-[10px] text-amber-700 dark:text-amber-300 block font-semibold">Warning: 6.20 m (+0.25m)</span>
              </div>
              <div className="p-3 bg-emerald-50/40 dark:bg-zinc-900/80 rounded-xl border border-emerald-200 dark:border-emerald-500/30 transition-all duration-200 transform hover:scale-105 hover:-translate-y-1 hover:shadow-md hover:bg-emerald-50/70 dark:hover:bg-zinc-850 cursor-pointer">
                <span className="text-xs text-slate-600 dark:text-zinc-400 block font-medium">Chhoti Nadi Siphon</span>
                <span className="text-2xl font-bold font-mono text-emerald-700 dark:text-emerald-400 mt-0.5 block">4.10 m</span>
                <span className="text-[10px] text-emerald-700 dark:text-emerald-300 block font-semibold">Normal Flow Stage</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. OFFICIAL EMERGENCY & DISASTER HOTLINES (Bottom-most section) */}
      <EmergencyHelplineBar />

      {/* Human-Readable Alert Details Modal */}
      {isCapModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-5 sm:p-6 shadow-2xl border border-slate-200 max-h-[90vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
                    {language === 'pa' ? 'ਅਲਰਟ ਵੇਰਵੇ' : language === 'hi' ? 'अलर्ट विवरण' : 'Alert Details'}
                    <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-bold border border-red-200">
                      LIVE
                    </span>
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {language === 'pa'
                      ? 'ਪੰਜਾਬ ਰਾਜ ਆਫ਼ਤ ਪ੍ਰਬੰਧਨ ਅਥਾਰਟੀ (PSDMA) ਅਧਿਕਾਰਤ ਸਾਰਾਂਸ਼'
                      : language === 'hi'
                      ? 'पंजाब राज्य आपदा प्रबंधन प्राधिकरण (PSDMA) आधिकारिक सारांश'
                      : 'Official Disaster Management Protocol Summary (PSDMA)'}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsCapModalOpen(false)}
                className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Scrollable Body */}
            <div className="overflow-y-auto pr-1 py-4 space-y-4 flex-1">
              {/* Alert Type & Severity Top Highlight */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Alert Type */}
                <div className="p-3.5 rounded-2xl bg-red-50/70 border border-red-200">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-red-800 uppercase tracking-wide font-mono">
                    <AlertTriangle className="w-4 h-4 text-red-600" />
                    <span>{language === 'pa' ? 'ਅਲਰਟ ਕਿਸਮ' : language === 'hi' ? 'अलर्ट प्रकार' : 'Alert Type'}</span>
                  </div>
                  <div className="mt-1.5 text-sm font-bold text-slate-900">
                    {language === 'pa'
                      ? 'ਅਚਨਚੇਤੀ ਹੜ੍ਹ ਚੇਤਾਵਨੀ (ਟਾਇਰ-3 ਜਲ ਨਿਗਰਾਨੀ)'
                      : language === 'hi'
                      ? 'आकस्मिक बाढ़ चेतावनी (टियर-3 जल निगरानी)'
                      : 'Flash Flood Warning (Tier-3 Hydrological)'}
                  </div>
                  <div className="text-[11px] text-red-700 font-medium mt-0.5">
                    {language === 'pa' ? 'ਘੱਗਰ ਬੇਸਿਨ ਤੇ ਵੱਡੀ ਨਦੀ' : language === 'hi' ? 'घग्गर बेसिन व बड़ी नदी' : 'Ghaggar Basin & Badi Nadi Corridor'}
                  </div>
                </div>

                {/* Severity */}
                <div className="p-3.5 rounded-2xl bg-amber-50/70 border border-amber-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-amber-900 uppercase tracking-wide font-mono">
                      <Activity className="w-4 h-4 text-amber-600" />
                      <span>{language === 'pa' ? 'ਗੰਭੀਰਤਾ ਪੱਧਰ' : language === 'hi' ? 'गंभीरता स्तर' : 'Severity'}</span>
                    </div>
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-md bg-red-600 text-white font-mono uppercase">
                      <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                      {language === 'pa' ? 'ਲਾਲ ਨਿਸ਼ਾਨ' : language === 'hi' ? 'रेड अलर्ट' : 'Red Alert'}
                    </span>
                  </div>
                  <div className="mt-1.5 text-sm font-bold text-slate-900">
                    {language === 'pa'
                      ? 'ਬਹੁਤ ਜ਼ਿਆਦਾ ਖ਼ਤਰਾ (14.82m — ਖ਼ਤਰੇ ਦੇ ਨਿਸ਼ਾਨ ਤੋਂ ਉੱਪਰ)'
                      : language === 'hi'
                      ? 'अति गंभीर (14.82m — खतरे के निशान से ऊपर)'
                      : 'Extreme (14.82m — +0.32m above danger)'}
                  </div>
                  <div className="text-[11px] text-amber-800 font-medium mt-0.5">
                    {language === 'pa' ? 'ਤੁਰੰਤ ਕਾਰਵਾਈ ਲੋੜੀਂਦੀ' : language === 'hi' ? 'तत्काल कार्रवाई आवश्यक' : 'Immediate Evacuation Directive'}
                  </div>
                </div>
              </div>

              {/* Key Details List */}
              <div className="bg-slate-50/80 rounded-2xl border border-slate-200 divide-y divide-slate-200/80">
                {/* Affected Areas */}
                <div className="p-3.5 flex items-start gap-3">
                  <div className="w-8 h-8 rounded-xl bg-orange-100 text-orange-700 flex items-center justify-center shrink-0 mt-0.5">
                    <MapPin className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 font-mono">
                      {language === 'pa' ? 'ਪ੍ਰਭਾਵਿਤ ਖੇਤਰ' : language === 'hi' ? 'प्रभावित क्षेत्र' : 'Affected Areas'}
                    </span>
                    <p className="text-xs font-semibold text-slate-900 mt-0.5 leading-snug">
                      {language === 'pa'
                        ? 'ਪਟਿਆਲਾ ਜ਼ਿਲ੍ਹਾ ਨਗਰ ਨਿਗਮ ਵਾਰਡ 12, 13, 14, ਸਮਾਣਾ ਅਤੇ ਸਨੌਰ ਦਰਿਆਈ ਪੱਟੀ, ਬੜੀ ਤੇ ਛੋਟੀ ਨਦੀ ਕੈਚਮੈਂਟ ਖੇਤਰ।'
                        : language === 'hi'
                        ? 'पटियाला जिला नगर निगम वार्ड 12, 13, 14, समाना एवं सनौर तटवर्ती गलियारा, बड़ी व छोटी नदी जलग्रहण क्षेत्र।'
                        : 'Patiala District Municipal Wards 12, 13, 14, Samana & Sanaur riparian corridors, Badi & Chhoti Nadi floodplains.'}
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {language === 'pa' ? 'ਲਗਭਗ 42,000 ਵਸਨੀਕ ਸਿੱਧੇ ਖ਼ਤਰੇ ਅਧੀਨ' : language === 'hi' ? 'लगभग 42,000 आबादी सीधे जोखिम में' : 'Est. 42,000 population in high-inundation zone'}
                    </p>
                  </div>
                </div>

                {/* Issued Time */}
                <div className="p-3.5 flex items-start gap-3">
                  <div className="w-8 h-8 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center shrink-0 mt-0.5">
                    <Clock className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 font-mono">
                      {language === 'pa' ? 'ਜਾਰੀ ਕਰਨ ਦਾ ਸਮਾਂ' : language === 'hi' ? 'जारी होने का समय' : 'Issued Time'}
                    </span>
                    <p className="text-xs font-semibold text-slate-900 mt-0.5">
                      {language === 'pa'
                        ? 'ਅੱਜ, ਸ਼ਾਮ 08:00 ਵਜੇ IST (ਲਾਈਵ ਬ੍ਰੌਡਕਾਸਟ)'
                        : language === 'hi'
                        ? 'आज, शाम 08:00 बजे IST (लाइव ब्रॉडकास्ट)'
                        : 'Today, 20:00:22 IST (Live Broadcast)'}
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5 font-mono">
                      Telemetry ID: IN-PB-PAT-2026-FL-0042
                    </p>
                  </div>
                </div>

                {/* Expected Duration */}
                <div className="p-3.5 flex items-start gap-3">
                  <div className="w-8 h-8 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0 mt-0.5">
                    <Calendar className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 font-mono">
                      {language === 'pa' ? 'ਸੰਭਾਵਿਤ ਮਿਆਦ' : language === 'hi' ? 'संभावित अवधि' : 'Expected Duration'}
                    </span>
                    <p className="text-xs font-semibold text-slate-900 mt-0.5">
                      {language === 'pa'
                        ? 'ਅਗਲੇ 24 ਤੋਂ 36 ਘੰਟੇ (ਜਦੋਂ ਤੱਕ ਘੱਗਰ ਦਰਿਆ ਦਾ ਪਾਣੀ ਖ਼ਤਰੇ ਦੇ ਨਿਸ਼ਾਨ ਤੋਂ ਹੇਠਾਂ ਨਹੀਂ ਆਉਂਦਾ)'
                        : language === 'hi'
                        ? 'अगले 24 से 36 घंटे (जब तक घग्गर नदी का जलस्तर खतरे के निशान से नीचे नहीं आ जाता)'
                        : 'Next 24 to 36 Hours (until upstream reservoir crest and runoff recedes)'}
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {language === 'pa' ? 'ਪੀਕ ਕਰੈਸਟ ਅਨੁਮਾਨ: ਸਵੇਰੇ ~04:30 ਵਜੇ (15.15 ਮੀਟਰ)' : language === 'hi' ? 'उच्चतम स्तर अनुमान: सुबह ~04:30 बजे (15.15 मीटर)' : 'Peak crest forecast: ~04:30 AM (15.15 m)'}
                    </p>
                  </div>
                </div>

                {/* Source */}
                <div className="p-3.5 flex items-start gap-3">
                  <div className="w-8 h-8 rounded-xl bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                    <Building2 className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 font-mono">
                      {language === 'pa' ? 'ਸਰੋਤ' : language === 'hi' ? 'स्रोत' : 'Source'}
                    </span>
                    <p className="text-xs font-semibold text-slate-900 mt-0.5">
                      {language === 'pa'
                        ? 'ਪੰਜਾਬ ਰਾਜ ਆਫ਼ਤ ਪ੍ਰਬੰਧਨ ਅਥਾਰਟੀ (PSDMA) ਅਤੇ ਜ਼ਿਲ੍ਹਾ ਐਮਰਜੈਂਸੀ ਆਪ੍ਰੇਸ਼ਨ ਸੈਂਟਰ (DEOC ਪਟਿਆਲਾ)'
                        : language === 'hi'
                        ? 'पंजाब राज्य आपदा प्रबंधन प्राधिकरण (PSDMA) एवं जिला आपातकालीन संचालन केंद्र (DEOC पटियाला)'
                        : 'Punjab State Disaster Management Authority (PSDMA) & District Emergency Operation Centre (DEOC Patiala)'}
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {language === 'pa' ? 'ਭਾਰਤ ਮੌਸਮ ਵਿਭਾਗ (IMD) ਤੇ ਕੇਂਦਰੀ ਜਲ ਕਮਿਸ਼ਨ (CWC) ਸਹਿਯੋਗ' : language === 'hi' ? 'भारत मौसम विज्ञान विभाग (IMD) व केंद्रीय जल आयोग (CWC) सहयोग' : 'In official coordination with IMD Hydromet & Central Water Commission (CWC)'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Recommended Actions Container */}
              <div className="p-4 rounded-2xl bg-amber-50/90 border border-amber-300">
                <div className="flex items-center gap-2 mb-2.5">
                  <CheckCircle2 className="w-4 h-4 text-amber-700" />
                  <h4 className="text-xs font-bold text-amber-950 uppercase tracking-wide font-mono">
                    {language === 'pa' ? 'ਸਿਫ਼ਾਰਸ਼ ਕੀਤੀਆਂ ਕਾਰਵਾਈਆਂ' : language === 'hi' ? 'अनुशंसित कार्रवाइयां' : 'Recommended Actions'}
                  </h4>
                </div>
                <ul className="space-y-2 text-xs text-amber-950">
                  <li className="flex items-start gap-2">
                    <span className="font-bold text-red-600 shrink-0">1.</span>
                    <span>
                      <strong>{language === 'pa' ? 'ਤੁਰੰਤ ਨਿਕਾਸੀ:' : language === 'hi' ? 'तत्काल निकासी:' : 'Immediate Evacuation:'}</strong>{' '}
                      {language === 'pa'
                        ? 'ਵਾਰਡ 12–14 ਦੇ ਨੀਵੇਂ ਘਰ ਤੁਰੰਤ ਖਾਲੀ ਕਰਕੇ ਸਰਕਾਰੀ ਮਹਿੰਦਰਾ ਕਾਲਜ ਰਾਹਤ ਕੈਂਪ ਪਹੁੰਚੋ।'
                        : language === 'hi'
                        ? 'वार्ड 12–14 के निचले क्षेत्र खाली कर सरकारी मोहिंद्रा कॉलेज राहत शिविर में जाएं।'
                        : 'Evacuate low-lying riverside homes in Wards 12–14 to designated shelter at Govt Mohindra College.'}
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="font-bold text-red-600 shrink-0">2.</span>
                    <span>
                      <strong>{language === 'pa' ? 'ਪਾਣੀ ਵਿੱਚ ਨਾ ਜਾਓ:' : language === 'hi' ? 'पानी में न जाएं:' : 'Avoid Moving Water:'}</strong>{' '}
                      {language === 'pa'
                        ? 'ਘੱਗਰ ਅਤੇ ਵੱਡੀ ਨਦੀ ਦੇ ਪੁਲਾਂ ਜਾਂ ਵਗਦੇ ਪਾਣੀ ਵਿੱਚ ਪੈਦਲ ਜਾਂ ਗੱਡੀ ਨਾ ਲੈ ਕੇ ਜਾਓ।'
                        : language === 'hi'
                        ? 'घग्गर व बड़ी नदी के पुलों या बहते पानी में वाहन अथवा पैदल न जाएं।'
                        : 'Never walk or drive across flooded bridges or through moving currents.'}
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="font-bold text-amber-700 shrink-0">3.</span>
                    <span>
                      <strong>{language === 'pa' ? 'ਬਿਜਲੀ ਬੰਦ ਕਰੋ:' : language === 'hi' ? 'बिजली बंद करें:' : 'Power Safety:'}</strong>{' '}
                      {language === 'pa'
                        ? 'ਕਰੰਟ ਤੋਂ ਬਚਣ ਲਈ ਘਰ ਵਿੱਚ ਪਾਣੀ ਆਉਣ ਤੋਂ ਪਹਿਲਾਂ ਮੇਨ ਬਿਜਲੀ ਸਵਿੱਚ ਤੁਰੰਤ ਬੰਦ ਕਰੋ।'
                        : language === 'hi'
                        ? 'करंट से बचाव हेतु घर में पानी आने से पहले मुख्य बिजली स्विच तुरंत बंद करें।'
                        : 'Turn off main electrical breakers before floodwaters enter premises.'}
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="font-bold text-amber-700 shrink-0">4.</span>
                    <span>
                      <strong>{language === 'pa' ? 'ਪਸ਼ੂਆਂ ਨੂੰ ਖੋਲ੍ਹੋ:' : language === 'hi' ? 'पशुओं को खोलें:' : 'Protect Cattle:'}</strong>{' '}
                      {language === 'pa'
                        ? 'ਡੰਗਰਾਂ ਨੂੰ ਰੱਸੀਆਂ ਤੋਂ ਖੋਲ੍ਹ ਕੇ ਸੁਰੱਖਿਅਤ ਉੱਚੀ ਥਾਂ ਤੇ ਲੈ ਜਾਓ।'
                        : language === 'hi'
                        ? 'मवेशियों को खोलकर सुरक्षित ऊंची जगह पहुंचाएं।'
                        : 'Untie livestock so they can move freely to higher ground.'}
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="font-bold text-blue-700 shrink-0">5.</span>
                    <span>
                      <strong>{language === 'pa' ? 'ਸਹਾਇਤਾ ਹੈਲਪਲਾਈਨ:' : language === 'hi' ? 'सहायता हेल्पलाइन:' : 'Emergency Hotlines:'}</strong>{' '}
                      {language === 'pa'
                        ? 'ਬਚਾਅ ਟੀਮਾਂ ਲਈ 112 ਜਾਂ ਕੰਟਰੋਲ ਰੂਮ ਲਈ 1077 ਡਾਇਲ ਕਰੋ।'
                        : language === 'hi'
                        ? 'बचाव दल हेतु 112 या कंट्रोल रूम हेतु 1077 डायल करें।'
                        : 'Call 112 (National Emergency Rescue) or 1077 (Patiala DEOC Control Room).'}
                    </span>
                  </li>
                </ul>
              </div>

              {/* Collapsible Technical CAP v1.2 Protocol XML */}
              <div className="pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowRawCap(!showRawCap)}
                  className="w-full py-2 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold flex items-center justify-between transition-colors cursor-pointer"
                >
                  <span className="flex items-center gap-1.5">
                    <FileCode className="w-3.5 h-3.5 text-slate-500" />
                    <span>{showRawCap ? 'Hide Technical CAP v1.2 XML' : 'View Technical CAP v1.2 Payload'}</span>
                  </span>
                  {showRawCap ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>

                {showRawCap && (
                  <pre className="mt-2.5 p-3.5 bg-slate-950 text-emerald-400 font-mono text-[11px] rounded-xl overflow-x-auto leading-relaxed border border-slate-800 animate-in fade-in duration-150">
{`<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>IN-PB-PAT-2026-FL-0042</identifier>
  <sender>deoc-patiala@punjab.gov.in</sender>
  <sent>2026-09-14T20:00:22+05:30</sent>
  <status>Actual</status>
  <msgType>Alert</msgType>
  <scope>Public</scope>
  <info>
    <language>${language === 'pa' ? 'pa-IN' : language === 'hi' ? 'hi-IN' : 'en-IN'}</language>
    <category>Met</category>
    <event>${language === 'pa' ? 'ਅਚਨਚੇਤੀ ਹੜ੍ਹ' : language === 'hi' ? 'आकस्मिक बाढ़' : 'Flash Flood'}</event>
    <urgency>Immediate</urgency>
    <severity>Extreme</severity>
    <certainty>Observed</certainty>
    <eventCode>
      <valueName>IMD</valueName>
      <value>FLASH_FLOOD_TIER3</value>
    </eventCode>
    <headline>${language === 'pa' ? 'ਲਾਜ਼ਮੀ ਨਿਕਾਸੀ ਹਦਾਇਤ: ਵਾਰਡ 12-14 ਪਟਿਆਲਾ' : language === 'hi' ? 'अनिवार्य निकासी निर्देश: वार्ड 12-14 पटियाला' : 'Mandatory Evacuation Directive: Ward 12-14 Patiala'}</headline>
    <description>${language === 'pa' ? 'ਘੱਗਰ ਅਤੇ ਵੱਡੀ ਨਦੀ ਦਾ ਪਾਣੀ 14.82 ਮੀਟਰ ਖ਼ਤਰੇ ਦੇ ਨਿਸ਼ਾਨ ਤੋਂ ਉੱਪਰ। 42,000 ਵਸਨੀਕਾਂ ਨੂੰ ਸਰਕਾਰੀ ਮਹਿੰਦਰਾ ਕਾਲਜ ਰਾਹਤ ਕੈਂਪਾਂ ਵਿੱਚ ਪਹੁੰਚਣ ਦੀ ਹਦਾਇਤ।' : language === 'hi' ? 'घग्गर और बड़ी नदी का जलस्तर 14.82 मीटर खतरे के निशान से ऊपर। 42,000 निवासियों को सरकारी मोहिंद्रा कॉलेज राहत शिविरों में जाने का निर्देश।' : 'Ghaggar and Badi Nadi breach threshold at 14.82m. 42,000 residents directed to relief shelters at Govt Mohindra College.'}</description>
    <area>
      <areaDesc>${language === 'pa' ? 'ਪਟਿਆਲਾ ਜ਼ਿਲ੍ਹਾ ਨਗਰ ਨਿਗਮ ਵਾਰਡ 12, 13, 14, ਸਮਾਣਾ ਅਤੇ ਸਨੌਰ ਦਰਿਆਈ ਖੇਤਰ' : language === 'hi' ? 'पटियाला जिला नगर निगम वार्ड 12, 13, 14, समाना एवं सनौर तटीय गलियारा' : 'Patiala District Municipal Wards 12, 13, 14, Samana & Sanaur riparian corridor'}</areaDesc>
      <circle>30.339,76.386,16.0</circle>
    </area>
  </info>
</alert>`}
                  </pre>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[11px] text-slate-500">
                {language === 'pa' ? 'ਪਟਿਆਲਾ ਜ਼ਿਲ੍ਹਾ ਕੰਟਰੋਲ ਰੂਮ: 1077' : language === 'hi' ? 'पटियाला जिला कंट्रोल रूम: 1077' : 'DEOC Control Room: 1077'}
              </span>
              <button
                type="button"
                onClick={() => setIsCapModalOpen(false)}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl transition-colors cursor-pointer"
              >
                {t('common.close', 'Close')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
