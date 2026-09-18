import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { speakText, stopSpeaking } from '../utils/speech';
import { GoogleWeatherCard } from './GoogleWeatherCard';
import {
  AlertTriangle,
  Volume2,
  VolumeX,
  PhoneCall,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Droplets,
  CloudRain,
  MapPin,
  Flame,
  HelpCircle,
  ChevronRight,
  Zap,
  Activity,
  Wind,
} from 'lucide-react';

interface SimpleVisualHomeProps {
  onNavigateTab: (tab: 'command' | 'risk' | 'emergency' | 'agriculture' | 'weathergpt') => void;
  selectedLocation: string;
}

export const SimpleVisualHome: React.FC<SimpleVisualHomeProps> = ({
  onNavigateTab,
  selectedLocation,
}) => {
  const { t, language } = useLanguage();
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [activeSpeechId, setActiveSpeechId] = useState<string | null>(null);

  // Play audio readout
  const handlePlaySpeech = (id: string, textToSpeak: string) => {
    if (isSpeaking && activeSpeechId === id) {
      stopSpeaking();
      setIsSpeaking(false);
      setActiveSpeechId(null);
      return;
    }

    stopSpeaking();
    setIsSpeaking(true);
    setActiveSpeechId(id);

    speakText(
      textToSpeak,
      language,
      () => {
        setIsSpeaking(true);
        setActiveSpeechId(id);
      },
      () => {
        setIsSpeaking(false);
        setActiveSpeechId(null);
      }
    );
  };

  const emergencyAlertText =
    language === 'pa'
      ? 'ਧਿਆਨ ਦਿਓ! ਵੱਡਾ ਹੜ੍ਹ ਖ਼ਤਰਾ। ਪਟਿਆਲਾ ਵਿੱਚ ਘੱਗਰ ਦਰਿਆ ਦਾ ਪਾਣੀ ਖ਼ਤਰੇ ਦੇ ਨਿਸ਼ਾਨ ਤੋਂ ਉੱਪਰ ਹੈ। ਨੀਵੇਂ ਇਲਾਕੇ ਖਾਲੀ ਕਰੋ ਅਤੇ ਉੱਚੀ ਥਾਂ ਜਾਓ। ਮਦਦ ਲਈ ਇੱਕ ਸੌ ਬਾਰਾਂ ਤੇ ਫ਼ੋਨ ਕਰੋ।'
      : language === 'hi'
      ? 'सावधान! भारी बाढ़ खतरा। पटियाला में घग्गर नदी का पानी खतरे के निशान से ऊपर है। निचले इलाके खाली करें और ऊंचे स्थान पर जाएं। मदद के लिए एक सौ बारह पर फोन करें।'
      : 'Attention! Severe Flood Danger. River water is rising fast above danger mark in Patiala. Move to high ground immediately. Call 112 for rescue.';

  return (
    <div className="space-y-5 pb-16 animate-in fade-in duration-200">
      {/* 1. TOP OFFICIAL ALERT BANNER */}
      <div
        id="simple-danger-banner"
        className="bg-white text-slate-900 rounded-xl p-4 sm:p-5 border-2 border-red-500 shadow-sm relative"
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="max-w-3xl">
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-bold bg-red-600 text-white tracking-wider uppercase font-mono shadow-xs">
                <AlertTriangle className="w-3 h-3 text-white" />
                <span>{language === 'pa' ? 'ਲਾਲ ਨਿਸ਼ਾਨ (ਹੜ੍ਹ ਚੇਤਾਵਨੀ)' : language === 'hi' ? 'रेड अलर्ट (बाढ़ चेतावनी)' : 'RED ALERT (HYDROLOGICAL)'}</span>
              </span>
              <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                <span>{t('loc.' + selectedLocation, selectedLocation)} • {language === 'pa' ? 'ਘੱਗਰ ਬੇਸਿਨ' : language === 'hi' ? 'घग्गर बेसिन' : 'Ghaggar Basin'}</span>
              </span>
            </div>

            <h1
              id="title-severe-flood-danger"
              className="text-lg sm:text-xl font-bold tracking-tight text-slate-950"
            >
              {language === 'pa'
                ? 'ਵੱਡਾ ਹੜ੍ਹ ਖ਼ਤਰਾ'
                : language === 'hi'
                ? 'भारी बाढ़ खतरा'
                : 'Severe Flood Danger'}
            </h1>

            <p className="text-xs text-slate-600 font-normal mt-1 leading-normal">
              {language === 'pa'
                ? 'ਦਰਿਆ ਦਾ ਪਾਣੀ ਖ਼ਤਰੇ ਦੇ ਨਿਸ਼ਾਨ (14.82m) ਤੋਂ ਉੱਪਰ ਹੈ। ਨੀਵੇਂ ਇਲਾਕੇ ਤੁਰੰਤ ਖਾਲੀ ਕਰੋ।'
                : language === 'hi'
                ? 'नदी जलस्तर खतरे के निशान (14.82m) से ऊपर है। निचले इलाके तुरंत खाली करें।'
                : 'River water is rising above danger mark (14.82m). Low-lying areas must evacuate immediately.'}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <button
              id="btn-voice-danger"
              type="button"
              onClick={() => handlePlaySpeech('danger-banner', emergencyAlertText)}
              className={`px-3 py-1.5 rounded-lg font-semibold text-xs transition-colors flex items-center gap-1.5 border ${
                isSpeaking && activeSpeechId === 'danger-banner'
                  ? 'bg-amber-400 text-slate-950 border-amber-500 shadow-xs'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-800 border-slate-200'
              }`}
            >
              {isSpeaking && activeSpeechId === 'danger-banner' ? (
                <>
                  <VolumeX className="w-3.5 h-3.5 text-slate-950" />
                  <span>{t('simple.voiceStop', 'Stop')}</span>
                </>
              ) : (
                <>
                  <Volume2 className="w-3.5 h-3.5 text-slate-600" />
                  <span>{t('simple.voiceBtn', 'Listen')}</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={() => onNavigateTab('weathergpt')}
              className="px-3 py-1.5 rounded-lg font-semibold text-xs bg-blue-600 hover:bg-blue-700 text-white transition-colors flex items-center gap-1 shadow-xs"
            >
              <span>WeatherGPT</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>

            <button
              type="button"
              onClick={() => onNavigateTab('risk')}
              className="px-3 py-1.5 rounded-lg font-semibold text-xs bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-200 transition-colors flex items-center gap-1"
            >
              <span>{t('nav.riskMap', 'Risk Map')}</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. BALANCED 2-COLUMN GRID: METEOROLOGICAL CONDITIONS & RIVER WATER HEIGHT */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-stretch">
        {/* Column 1: Today's Meteorological Conditions */}
        <GoogleWeatherCard locationName={selectedLocation} />

        {/* Column 2: Hydrological Gauge Telemetry */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-600" />
                <h3 className="text-base font-bold text-slate-900">
                  {t('simple.riverGauge', 'River Water Height (Ghaggar Basin)')}
                </h3>
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between">
              <div>
                <span className="text-3xl font-bold font-mono text-slate-950">14.82 m</span>
                <span className="text-xs text-slate-500 ml-2 font-medium">
                  {language === 'pa' ? 'ਖ਼ਤਰਾ: 14.50 m' : language === 'hi' ? 'खतरा: 14.50 m' : 'Danger: 14.50 m'}
                </span>
              </div>
              <span className="text-xs font-bold px-2.5 py-0.5 rounded bg-red-50 text-red-700 border border-red-200 font-mono">
                {language === 'pa' ? 'ਖ਼ਤਰੇ ਤੋਂ ਉੱਪਰ (+0.32m)' : language === 'hi' ? 'खतरे से ऊपर (+0.32m)' : 'Above Danger (+0.32m)'}
              </span>
            </div>

            {/* Progress bar */}
            <div className="mt-4">
              <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden border border-slate-200">
                <div
                  className="bg-red-600 h-full rounded-full transition-all duration-500"
                  style={{ width: '92%' }}
                />
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1.5 font-medium">
                <span>0m</span>
                <span className="text-amber-600 font-semibold">{language === 'pa' ? 'ਚੇਤਾਵਨੀ 6m' : language === 'hi' ? 'चेतावनी 6m' : 'Warning 6m'}</span>
                <span className="text-red-600 font-bold">{language === 'pa' ? 'ਖ਼ਤਰਾ 14.5m' : language === 'hi' ? 'खतरा 14.5m' : 'Danger 14.5m'}</span>
              </div>
            </div>

            {/* Telemetry Highlights - 4 key metrics */}
            <div className="mt-3.5 grid grid-cols-2 gap-2.5">
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 transition-all duration-200 transform hover:scale-105 hover:-translate-y-0.5 hover:shadow-md hover:bg-white hover:border-slate-300 cursor-pointer">
                <span className="text-[11px] text-slate-500 block">{language === 'pa' ? 'ਬੇਸਿਨ ਸਮਰੱਥਾ' : language === 'hi' ? 'बेसिन क्षमता' : 'Basin Capacity'}</span>
                <span className="text-sm font-bold font-mono text-red-600">92% {language === 'pa' ? 'ਭਰਿਆ' : language === 'hi' ? 'भरा' : 'Full'}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 transition-all duration-200 transform hover:scale-105 hover:-translate-y-0.5 hover:shadow-md hover:bg-white hover:border-slate-300 cursor-pointer">
                <span className="text-[11px] text-slate-500 block">{language === 'pa' ? 'ਪਾਣੀ ਦਾ ਵਹਾਅ' : language === 'hi' ? 'जल प्रवाह' : 'Inflow Trend'}</span>
                <span className="text-sm font-bold font-mono text-amber-700">{language === 'pa' ? 'ਤੇਜ਼ੀ ਨਾਲ ਵਾਧਾ (+0.18m/h)' : language === 'hi' ? 'तीव्र वृद्धि (+0.18m/h)' : 'Rising (+0.18m/h)'}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 transition-all duration-200 transform hover:scale-105 hover:-translate-y-0.5 hover:shadow-md hover:bg-white hover:border-slate-300 cursor-pointer">
                <span className="text-[11px] text-slate-500 block">{language === 'pa' ? 'ਨਿਕਾਸ ਦਰ' : language === 'hi' ? 'निकासी दर' : 'Discharge Rate'}</span>
                <span className="text-sm font-bold font-mono text-slate-900">48,500 {language === 'pa' ? 'ਕਿਊਸਿਕ' : language === 'hi' ? 'क्यूसेक' : 'cusecs'}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 transition-all duration-200 transform hover:scale-105 hover:-translate-y-0.5 hover:shadow-md hover:bg-white hover:border-slate-300 cursor-pointer">
                <span className="text-[11px] text-slate-500 block">{language === 'pa' ? 'ਸਿਖਰ ਪੱਧਰ ਅਨੁਮਾਨ' : language === 'hi' ? 'चरम स्तर अनुमान' : 'Peak Crest Forecast'}</span>
                <span className="text-sm font-bold font-mono text-slate-900">~04:30 AM <span className="text-xs text-red-600 font-semibold">(15.15m)</span></span>
              </div>
            </div>

            {/* Critical Evacuation & Shelter Notice */}
            <div className="mt-3 p-2.5 rounded-xl bg-amber-50/70 border border-amber-200/80 flex items-center justify-between text-xs transition-all duration-200 transform hover:scale-[1.02] hover:shadow-md cursor-pointer">
              <div className="flex items-center gap-2 text-slate-800">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                <span className="font-medium">
                  {language === 'pa'
                    ? 'ਖ਼ਤਰਾ ਖੇਤਰ: ਵਾਰਡ 12–14 • ਰਾਹਤ ਕੈਂਪ: ਸਰਕਾਰੀ ਮਹਿੰਦਰਾ ਕਾਲਜ (1.2 km)'
                    : language === 'hi'
                    ? 'संवेदनशील क्षेत्र: वार्ड 12–14 • राहत शिविर: सरकारी महिंद्रा कॉलेज (1.2 km)'
                    : 'Evacuate: Wards 12–14 • Shelter: Govt Mohindra College (1.2 km)'}
                </span>
              </div>
              <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-amber-200/60 text-amber-900 font-mono shrink-0 ml-2">
                {language === 'pa' ? 'ਹਾਈ ਅਲਰਟ' : language === 'hi' ? 'हाई अलर्ट' : 'High Alert'}
              </span>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500 font-medium">
              {language === 'pa' ? 'ਲਾਈਵ ਸੈਂਸਰ ਸਰਗਰਮ' : language === 'hi' ? 'सक्रिय लाइव सेंसर' : 'Naraj Bridge Telemetry Active'}
            </span>
            <button
              type="button"
              onClick={() => onNavigateTab('risk')}
              className="font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1 cursor-pointer"
            >
              <span>{language === 'pa' ? 'ਨਕਸ਼ਾ ਦੇਖੋ' : language === 'hi' ? 'नक्शा देखें' : 'View Risk Map'}</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* 3. ESSENTIAL LIFE-SAVING DIRECTIVES */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2.5">
          <div>
            <h2 className="text-sm font-bold text-slate-900">
              {language === 'pa'
                ? 'ਜ਼ਰੂਰੀ ਜਾਨ-ਬਚਾਊ ਕਦਮ'
                : language === 'hi'
                ? 'आवश्यक जीवन-रक्षक कदम'
                : 'Essential Life-Saving Directives'}
            </h2>
            <p className="text-[11px] text-slate-500">
              {language === 'pa'
                ? 'ਪੰਜਾਬ ਰਾਜ ਆਫ਼ਤ ਪ੍ਰਬੰਧਨ ਅਥਾਰਟੀ (PSDMA) ਵੱਲੋਂ ਜਾਰੀ ਹਦਾਇਤਾਂ'
                : language === 'hi'
                ? 'पंजाब राज्य आपदा प्रबंधन प्राधिकरण (PSDMA) द्वारा जारी निर्देश'
                : 'Directives by Punjab State Disaster Management Authority (PSDMA)'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Step 1: Move to High Ground */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg hover:bg-white hover:border-blue-300 cursor-pointer">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-900 font-mono">01</span>
              <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center">
                <CheckCircle2 className="w-3.5 h-3.5" />
              </span>
            </div>
            <h3 className="text-xs font-bold text-slate-900 mt-2">
              {language === 'pa' ? 'ਉੱਚੀ ਥਾਂ ਜਾਓ' : language === 'hi' ? 'ऊंचे स्थान पर जाएं' : 'Move to High Ground'}
            </h3>
            <p className="text-[11px] text-slate-600 mt-1 leading-normal">
              {language === 'pa'
                ? 'ਘਰ ਦੀ ਛੱਤ ਜਾਂ ਰਾਹਤ ਕੈਂਪ (ਸਰਕਾਰੀ ਮਹਿੰਦਰਾ ਕਾਲਜ) ਪਹੁੰਚੋ।'
                : language === 'hi'
                ? 'छत अथवा राहत शिविर (राजकीय मोहिंद्रा कॉलेज) जाएं।'
                : 'Evacuate to rooftop or relief camp at Govt Mohindra College.'}
            </p>
          </div>

          {/* Step 2: Stay Out of Water */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg hover:bg-white hover:border-red-300 cursor-pointer">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-900 font-mono">02</span>
              <span className="w-5 h-5 rounded-full bg-red-100 text-red-700 flex items-center justify-center">
                <XCircle className="w-3.5 h-3.5" />
              </span>
            </div>
            <h3 className="text-xs font-bold text-slate-900 mt-2">
              {language === 'pa' ? 'ਪਾਣੀ ਵਿੱਚ ਨਾ ਵੜੋ' : language === 'hi' ? 'पानी में न जाएं' : 'Avoid Moving Water'}
            </h3>
            <p className="text-[11px] text-slate-600 mt-1 leading-normal">
              {language === 'pa'
                ? 'ਵਗਦੇ ਹੜ੍ਹ ਦੇ ਪਾਣੀ ਵਿੱਚ ਪੈਦਲ ਜਾਂ ਗੱਡੀ ਲੈ ਕੇ ਨਾ ਜਾਓ।'
                : language === 'hi'
                ? 'बहते पानी में पैदल अथवा वाहन लेकर न जाएं।'
                : 'Never walk or drive into moving flood currents.'}
            </p>
          </div>

          {/* Step 3: Turn off Electricity */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg hover:bg-white hover:border-blue-300 cursor-pointer">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-900 font-mono">03</span>
              <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center">
                <Zap className="w-3.5 h-3.5" />
              </span>
            </div>
            <h3 className="text-xs font-bold text-slate-900 mt-2">
              {language === 'pa' ? 'ਬਿਜਲੀ ਬੰਦ ਕਰੋ' : language === 'hi' ? 'बिजली बंद करें' : 'Isolate Power Main'}
            </h3>
            <p className="text-[11px] text-slate-600 mt-1 leading-normal">
              {language === 'pa'
                ? 'ਕਰੰਟ ਤੋਂ ਬਚਣ ਲਈ ਘਰ ਦਾ ਮੇਨ ਸਵਿੱਚ ਤੁਰੰਤ ਬੰਦ ਕਰੋ।'
                : language === 'hi'
                ? 'करंट से बचाव हेतु मुख्य बिजली स्विच तुरंत बंद करें।'
                : 'Turn off main breaker before water enters premises.'}
            </p>
          </div>

          {/* Step 4: Untie Cattle */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg hover:bg-white hover:border-amber-300 cursor-pointer">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-900 font-mono">04</span>
              <span className="w-5 h-5 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center">
                <CheckCircle2 className="w-3.5 h-3.5" />
              </span>
            </div>
            <h3 className="text-xs font-bold text-slate-900 mt-2">
              {language === 'pa' ? 'ਪਸ਼ੂ ਖੋਲ੍ਹੋ' : language === 'hi' ? 'पशुओं को खोलें' : 'Untie & Move Cattle'}
            </h3>
            <p className="text-[11px] text-slate-600 mt-1 leading-normal">
              {language === 'pa'
                ? 'ਪਸ਼ੂਆਂ ਨੂੰ ਰੱਸੀਆਂ ਤੋਂ ਖੋਲ੍ਹ ਕੇ ਉੱਚੀ ਸੁੱਕੀ ਥਾਂ ਲੈ ਜਾਓ।'
                : language === 'hi'
                ? 'मवेशियों को खोलकर सुरक्षित ऊंची जगह पहुंचाएं।'
                : 'Untie livestock so they can move to high ground.'}
            </p>
          </div>
        </div>
      </div>

      {/* 4. AGRO-METEOROLOGICAL ADVICE SECTION */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 pb-2.5 mb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              {language === 'pa'
                ? 'ਪੀ.ਏ.ਯੂ. ਖੇਤੀਬਾੜੀ ਸਲਾਹ'
                : language === 'hi'
                ? 'पीएयू कृषि परामर्श'
                : 'PAU Agro-Meteorological Advisories'}
            </h3>
            <p className="text-[11px] text-slate-500">
              {language === 'pa'
                ? 'ਪੰਜਾਬ ਖੇਤੀਬਾੜੀ ਯੂਨੀਵਰਸਿਟੀ ਲੁਧਿਆਣਾ'
                : language === 'hi'
                ? 'पंजाब कृषि विश्वविद्यालय लुधियाना'
                : 'Punjab Agricultural University Ludhiana'}
            </p>
          </div>
          <button
            type="button"
            onClick={() => onNavigateTab('agriculture')}
            className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            <span>{language === 'pa' ? 'ਪੂਰੀ ਰਿਪੋਰਟ' : language === 'hi' ? 'विस्तृत रिपोर्ट' : 'Full Advisory'}</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg hover:bg-white hover:border-red-300 cursor-pointer">
            <span className="text-[11px] font-bold text-red-700 uppercase tracking-wider block">
              {language === 'pa' ? 'ਸਪਰੇਅ ਮੁਲਤਵੀ' : language === 'hi' ? 'छिड़काव स्थगित' : 'SUSPEND SPRAY'}
            </span>
            <p className="text-xs text-slate-700 font-medium mt-1 leading-normal">
              {language === 'pa'
                ? 'ਅਗਲੇ 48 ਘੰਟਿਆਂ ਦੌਰਾਨ ਕੀਟਨਾਸ਼ਕ ਜਾਂ ਯੂਰੀਆ ਸਪਰੇਅ ਨਾ ਕਰੋ।'
                : language === 'hi'
                ? 'आगामी 48 घंटों में कीटनाशक अथवा यूरिया छिड़काव न करें।'
                : 'Do not spray pesticides or urea; rainfall will wash chemicals away.'}
            </p>
          </div>

          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg hover:bg-white hover:border-blue-300 cursor-pointer">
            <span className="text-[11px] font-bold text-blue-700 uppercase tracking-wider block">
              {language === 'pa' ? 'ਪਾਣੀ ਨਿਕਾਸੀ' : language === 'hi' ? 'जल निकासी' : 'DRAINAGE OPEN'}
            </span>
            <p className="text-xs text-slate-700 font-medium mt-1 leading-normal">
              {language === 'pa'
                ? 'ਖੇਤਾਂ ਵਿੱਚੋਂ ਵਾਧੂ ਪਾਣੀ ਕੱਢਣ ਲਈ ਬੰਨ੍ਹਾਂ ਦੇ ਨਿਕਾਸ ਤੁਰੰਤ ਖੋਲ੍ਹੋ।'
                : language === 'hi'
                ? 'खेतों से जलभराव रोकने हेतु मेड़ों के निकास खोलें।'
                : 'Open field drainage cuts to flush floodwater and save roots.'}
            </p>
          </div>

          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg hover:bg-white hover:border-amber-300 cursor-pointer">
            <span className="text-[11px] font-bold text-amber-700 uppercase tracking-wider block">
              {language === 'pa' ? 'ਸੁੱਕਾ ਚਾਰਾ ਸੁਰੱਖਿਆ' : language === 'hi' ? 'सूखा चारा संरक्षण' : 'FODDER STORAGE'}
            </span>
            <p className="text-xs text-slate-700 font-medium mt-1 leading-normal">
              {language === 'pa'
                ? 'ਤੂੜੀ ਤੇ ਚਾਰੇ ਨੂੰ ਤਰਪਾਲ ਨਾਲ ਢੱਕ ਕੇ ਉੱਚੀ ਥਾਂ ਰੱਖੋ।'
                : language === 'hi'
                ? 'पशुओं के चारे को तिरपाल से ढककर ऊंची जगह रखें।'
                : 'Cover dry straw with tarpaulins on raised plinths.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
