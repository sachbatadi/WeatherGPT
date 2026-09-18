import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { speakText, stopSpeaking } from '../utils/speech';
import {
  PhoneCall,
  Volume2,
  VolumeX,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  MapPin,
  Building2,
  ExternalLink,
  ArrowUpRight,
  Ban,
  PowerOff,
  ShieldCheck,
} from 'lucide-react';

export const SimpleEmergencySection: React.FC = () => {
  const { language, t } = useLanguage();
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [activeSpeechKey, setActiveSpeechKey] = useState<string | null>(null);

  const handleSpeak = (key: string, text: string) => {
    if (isSpeaking && activeSpeechKey === key) {
      stopSpeaking();
      setIsSpeaking(false);
      setActiveSpeechKey(null);
      return;
    }

    stopSpeaking();
    setIsSpeaking(true);
    setActiveSpeechKey(key);

    speakText(
      text,
      language,
      () => {
        setIsSpeaking(true);
        setActiveSpeechKey(key);
      },
      () => {
        setIsSpeaking(false);
        setActiveSpeechKey(null);
      }
    );
  };

  const alertVoiceText =
    language === 'pa'
      ? 'ਹੜ੍ਹ ਸੰਕਟਕਾਲੀਨ ਚੇਤਾਵਨੀ! ਜੇਕਰ ਤੁਹਾਡੇ ਘਰ ਵਿੱਚ ਪਾਣੀ ਦਾਖ਼ਲ ਹੋ ਰਿਹਾ ਹੈ, ਤੁਰੰਤ ਉੱਚੀ ਥਾਂ ਜਾਂ ਛੱਤ ਤੇ ਚੜ੍ਹ ਜਾਓ। ਬਚਾਅ ਟੀਮ ਬੁਲਾਉਣ ਲਈ ਇੱਕ ਸੌ ਬਾਰਾਂ ਤੇ ਫ਼ੋਨ ਕਰੋ।'
      : language === 'hi'
      ? 'बाढ़ आपातकालीन चेतावनी! यदि आपके घर में पानी प्रवेश कर रहा है, तो तुरंत ऊंची जगह या छत पर जाएं। बचाव दल बुलाने हेतु एक सौ बारह पर कॉल करें।'
      : 'Flood Emergency! If water is entering your home, move to the roof or high ground immediately. Call 112 for rescue teams.';

  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      {/* 1. TOP SOS EMERGENCY PANEL (Institutional High-Contrast Dark Slate) */}
      <div className="bg-slate-900 text-white rounded-xl p-5 sm:p-6 border border-slate-800 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-lg bg-red-600/20 text-red-400 border border-red-500/30 flex items-center justify-center shrink-0 mt-0.5">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-red-500" />
                <span className="text-[11px] font-bold uppercase tracking-wider text-red-400 font-mono">
                  {language === 'pa' ? 'ਤੁਰੰਤ ਬਚਾਅ ਤੇ ਮਦਦ' : language === 'hi' ? 'त्वरित बचाव व सहायता' : 'Emergency Rescue Protocol'}
                </span>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white mt-1">
                {language === 'pa'
                  ? 'ਕੀ ਤੁਹਾਨੂੰ ਤੁਰੰਤ ਮਦਦ ਚਾਹੀਦੀ ਹੈ?'
                  : language === 'hi'
                  ? 'क्या आपको तुरंत मदद चाहिए?'
                  : 'Do You Need Emergency Assistance?'}
              </h2>
              <p className="text-slate-300 text-xs sm:text-sm mt-1 max-w-2xl leading-relaxed">
                {language === 'pa'
                  ? 'ਜੇਕਰ ਪਾਣੀ ਵਿੱਚ ਫਸ ਗਏ ਹੋ ਤਾਂ ਹੇਠਾਂ ਦਿੱਤੇ ਨੰਬਰਾਂ ਤੇ ਸਿੱਧਾ ਫ਼ੋਨ ਕਰੋ ਜਾਂ ਉੱਚੀ ਥਾਂ ਤੇ ਚੜ੍ਹੋ।'
                  : language === 'hi'
                  ? 'यदि बाढ़ के पानी में फंसे हैं तो नीचे दिए नंबरों पर कॉल करें अथवा सुरक्षित स्थान पर जाएं।'
                  : 'If trapped or stranded in flood water, use the verified hotlines below for immediate evacuation.'}
              </p>
            </div>
          </div>

          {/* Voice button */}
          <button
            type="button"
            onClick={() => handleSpeak('sos-hero', alertVoiceText)}
            className={`shrink-0 px-3.5 py-2 rounded-lg font-semibold text-xs flex items-center gap-2 border transition-colors ${
              isSpeaking && activeSpeechKey === 'sos-hero'
                ? 'bg-amber-400 text-slate-950 border-amber-300'
                : 'bg-slate-800 hover:bg-slate-700 text-white border-slate-700'
            }`}
          >
            {isSpeaking && activeSpeechKey === 'sos-hero' ? (
              <>
                <VolumeX className="w-4 h-4 text-slate-950" />
                <span>{t('simple.voiceStop', 'Stop Audio')}</span>
              </>
            ) : (
              <>
                <Volume2 className="w-4 h-4 text-slate-300" />
                <span>{t('simple.voiceBtn', 'Listen Warning')}</span>
              </>
            )}
          </button>
        </div>

        {/* 1-Tap Emergency Hotlines (Clean, High-Contrast Institutional Grid) */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-5">
          {/* 112 */}
          <a
            href="tel:112"
            className="flex items-center justify-between p-3.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700 transition-colors"
          >
            <div>
              <span className="text-xl sm:text-2xl font-black text-white font-mono block">112</span>
              <span className="text-[11px] font-medium text-slate-400">
                {language === 'pa' ? 'ਪੁਲਿਸ ਤੇ ਐਨ.ਡੀ.ਆਰ.ਐਫ਼' : language === 'hi' ? 'पुलिस व बचाव दल' : 'National Rescue & Police'}
              </span>
            </div>
            <div className="w-8 h-8 rounded-md bg-red-500/20 text-red-400 border border-red-500/30 flex items-center justify-center">
              <PhoneCall className="w-4 h-4" />
            </div>
          </a>

          {/* 1077 */}
          <a
            href="tel:1077"
            className="flex items-center justify-between p-3.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700 transition-colors"
          >
            <div>
              <span className="text-xl sm:text-2xl font-black text-white font-mono block">1077</span>
              <span className="text-[11px] font-medium text-slate-400">
                {language === 'pa' ? 'ਜ਼ਿਲ੍ਹਾ ਹੜ੍ਹ ਕੰਟਰੋਲ ਰੂਮ' : language === 'hi' ? 'जिला बाढ़ नियंत्रण' : 'District Flood Control'}
              </span>
            </div>
            <div className="w-8 h-8 rounded-md bg-blue-500/20 text-blue-400 border border-blue-500/30 flex items-center justify-center">
              <PhoneCall className="w-4 h-4" />
            </div>
          </a>

          {/* 108 */}
          <a
            href="tel:108"
            className="flex items-center justify-between p-3.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700 transition-colors"
          >
            <div>
              <span className="text-xl sm:text-2xl font-black text-white font-mono block">108</span>
              <span className="text-[11px] font-medium text-slate-400">
                {language === 'pa' ? 'ਮੈਡੀਕਲ ਐਂਬੂਲੈਂਸ' : language === 'hi' ? 'चिकित्सा एम्बुलेंस' : 'Emergency Ambulance'}
              </span>
            </div>
            <div className="w-8 h-8 rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center">
              <PhoneCall className="w-4 h-4" />
            </div>
          </a>
        </div>
      </div>

      {/* 2. SAFE RELIEF SHELTER (Clean White Card) */}
      <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs">
        <div className="flex items-center justify-between mb-3.5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center">
              <Building2 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-bold text-slate-900">
                {language === 'pa'
                  ? 'ਸਭ ਤੋਂ ਨੇੜਲਾ ਸੁਰੱਖਿਅਤ ਰਾਹਤ ਕੈਂਪ'
                  : language === 'hi'
                  ? 'निकटतम सुरक्षित राहत शिविर'
                  : 'Designated Safe Relief Shelter'}
              </h3>
              <p className="text-[11px] text-slate-500">
                {language === 'pa' ? 'ਸਰਕਾਰੀ ਤੌਰ ਤੇ ਪ੍ਰਬੰਧਿਤ ਸੁਰੱਖਿਅਤ ਥਾਂ' : language === 'hi' ? 'प्रशासन द्वारा संचालित आश्रय स्थल' : 'District Administration Managed Camp'}
              </p>
            </div>
          </div>
          <span className="px-2.5 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
            {language === 'pa' ? 'ਖੁੱਲ੍ਹਾ ਹੈ (ਸੁਰੱਖਿਅਤ)' : language === 'hi' ? 'सक्रिय एवं सुरक्षित' : 'Operational & Verified'}
          </span>
        </div>

        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-3.5">
          <div>
            <h4 className="text-sm font-bold text-slate-900">
              {language === 'pa'
                ? 'ਸਰਕਾਰੀ ਸੀਨੀਅਰ ਸੈਕੰਡਰੀ ਸਕੂਲ, ਮਾਡਲ ਟਾਊਨ ਪਟਿਆਲਾ'
                : language === 'hi'
                ? 'सरकारी सीनियर सेकेंडरी स्कूल, मॉडल टाउन पटियाला'
                : 'Govt Senior Secondary School, Model Town, Patiala'}
            </h4>
            <div className="flex flex-wrap items-center gap-2.5 mt-2 text-xs text-slate-600">
              <span className="flex items-center gap-1 font-medium text-slate-800">
                <MapPin className="w-3.5 h-3.5 text-blue-600" />
                <span>1.2 km ({language === 'pa' ? 'ਉੱਚੀ ਪੱਕੀ ਸੜਕ' : language === 'hi' ? 'पक्की सड़क' : 'Elevated paved access'})</span>
              </span>
              <span>•</span>
              <span>{language === 'pa' ? 'ਖਾਣਾ ਤੇ ਪਾਣੀ ਉਪਲਬਧ' : language === 'hi' ? 'भोजन व पेयजल' : 'Food & Potable Water'}</span>
              <span>•</span>
              <span>{language === 'pa' ? 'ਡਾਕਟਰੀ ਟੀਮ ਮੌਜੂਦ' : language === 'hi' ? 'चिकित्सक उपस्थित' : 'Medical Unit Onsite'}</span>
            </div>
          </div>

          <a
            href="https://maps.google.com/?q=Patiala+Model+Town+School"
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs flex items-center justify-center gap-1.5 transition-colors"
          >
            <span>{language === 'pa' ? 'ਨਕਸ਼ੇ ਤੇ ਰਸਤਾ ਦੇਖੋ' : language === 'hi' ? 'ਨਕਸ਼ੇ ਤੇ ਦੇਖੋ' : 'View Evacuation Route'}</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* 3. IMMEDIATE ACTIONS (Uniform Institutional Grid) */}
      <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs">
        <div className="flex items-center justify-between mb-3.5">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm sm:text-base font-bold text-slate-900">
              {t('simple.whatToDo', 'Immediate Life-Saving Directives')}
            </h3>
          </div>
          <span className="text-[11px] text-slate-500 font-medium">
            {language === 'pa' ? '4 ਜ਼ਰੂਰੀ ਨਿਰਦੇਸ਼' : language === 'hi' ? '4 आवश्यक निर्देश' : '4 Standard Safety Directives'}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Card 1: High Ground */}
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 flex flex-col justify-between hover:bg-slate-100/60 transition-colors">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-slate-200 text-slate-700">
                  ACTION 1
                </span>
                <ArrowUpRight className="w-4 h-4 text-slate-700" />
              </div>
              <h4 className="text-xs font-bold text-slate-900">
                {t('simple.step1Title', 'Move to High Ground')}
              </h4>
              <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
                {t('simple.step1Desc', 'Relocate to rooftop, 2nd floor, or higher village road.')}
              </p>
            </div>
          </div>

          {/* Card 2: Stay Out of Water */}
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 flex flex-col justify-between hover:bg-slate-100/60 transition-colors">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-slate-200 text-slate-700">
                  ACTION 2
                </span>
                <Ban className="w-4 h-4 text-red-600" />
              </div>
              <h4 className="text-xs font-bold text-slate-900">
                {t('simple.step2Title', 'Stay Out of Moving Water')}
              </h4>
              <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
                {t('simple.step2Desc', 'Never walk or drive into moving flood currents.')}
              </p>
            </div>
          </div>

          {/* Card 3: Untie Cattle */}
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 flex flex-col justify-between hover:bg-slate-100/60 transition-colors">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-slate-200 text-slate-700">
                  ACTION 3
                </span>
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              </div>
              <h4 className="text-xs font-bold text-slate-900">
                {t('simple.step3Title', 'Untie & Relocate Livestock')}
              </h4>
              <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
                {t('simple.step3Desc', 'Untie cattle so they are not trapped by rising water.')}
              </p>
            </div>
          </div>

          {/* Card 4: Turn Off Electricity */}
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 flex flex-col justify-between hover:bg-slate-100/60 transition-colors">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-slate-200 text-slate-700">
                  ACTION 4
                </span>
                <PowerOff className="w-4 h-4 text-amber-600" />
              </div>
              <h4 className="text-xs font-bold text-slate-900">
                {t('simple.step4Title', 'Turn Off Main Power Switch')}
              </h4>
              <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
                {t('simple.step4Desc', 'Shut down main electrical supply to avoid electrocution.')}
              </p>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
};
