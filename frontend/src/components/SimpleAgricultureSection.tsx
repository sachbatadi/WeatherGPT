import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { speakText, stopSpeaking } from '../utils/speech';
import {
  Sprout,
  Volume2,
  VolumeX,
  PhoneCall,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Calendar,
  CloudRain,
  CloudSun,
  Sun,
  Ban,
  Droplets,
  ShieldCheck,
  Activity,
  Building2,
} from 'lucide-react';

export const SimpleAgricultureSection: React.FC = () => {
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

  const agriHeroVoiceText =
    language === 'pa'
      ? 'ਪੰਜਾਬ ਖੇਤੀਬਾੜੀ ਯੂਨੀਵਰਸਿਟੀ ਲੁਧਿਆਣਾ ਦੀ ਕਿਸਾਨ ਸਲਾਹ: ਅੱਜ ਭਾਰੀ ਮੀਂਹ ਪੈਣ ਦੀ ਸੰਭਾਵਨਾ ਹੈ। ਝੋਨੇ ਦੇ ਖੇਤਾਂ ਵਿੱਚ ਕੋਈ ਵੀ ਸਪਰੇਅ ਜਾਂ ਖਾਦ ਨਾ ਪਾਓ। ਖੇਤਾਂ ਚੋਂ ਵਾਧੂ ਪਾਣੀ ਕੱਢਣ ਲਈ ਨਾਲੀਆਂ ਖੋਲ੍ਹੋ ਅਤੇ ਪਸ਼ੂਆਂ ਦੀ ਤੂੜੀ ਤਰਪਾਲ ਨਾਲ ਢੱਕੋ।'
      : language === 'hi'
      ? 'पंजाब कृषि विश्वविद्यालय लुधियाना की किसान सलाह: आज भारी वर्षा का अनुमान है। धान के खेतों में कोई छिड़काव या खाद न डालें। खेतों से अतिरिक्त पानी की निकासी करें और पशुओं का चारा तिरपाल से ढकें।'
      : 'Punjab Agricultural University advisory: Heavy rainfall anticipated. Suspend pesticide and fertilizer spraying on paddy. Clear field drainage bunds and protect cattle fodder under tarpaulins.';

  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      {/* 1. TOP PAU ADVISORY BANNER */}
      <div className="bg-white text-slate-900 rounded-xl p-5 sm:p-6 border border-emerald-300 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center shrink-0 mt-0.5">
              <Sprout className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-600" />
                <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 font-mono">
                  {language === 'pa'
                    ? 'ਪੰਜਾਬ ਖੇਤੀਬਾੜੀ ਯੂਨੀਵਰਸਿਟੀ (PAU) ਸਲਾਹ'
                    : language === 'hi'
                    ? 'पंजाब कृषि विश्वविद्यालय (PAU) परामर्श'
                    : 'PAU Agro-Meteorological Advisory'}
                </span>
              </div>
              <h2
                id="heading-daily-agro-directives"
                className="text-lg sm:text-xl font-bold tracking-tight text-slate-950 mt-1"
              >
                {language === 'pa'
                  ? 'ਕਿਸਾਨ ਜ਼ਰੂਰੀ ਸਲਾਹ'
                  : language === 'hi'
                  ? 'किसान आवश्यक निर्देश'
                  : 'Daily Agro-Climatic Directives'}
              </h2>
              <p className="text-slate-600 text-xs sm:text-sm mt-1 max-w-2xl leading-relaxed">
                {language === 'pa'
                  ? 'ਪਟਿਆਲਾ ਵਿੱਚ 78 ਮਿ.ਮੀ. ਬਾਰਿਸ਼ ਦਰਜ। ਫ਼ਸਲ ਤੇ ਪਸ਼ੂਆਂ ਦੀ ਸੁਰੱਖਿਆ ਲਈ ਜ਼ਰੂਰੀ ਹਦਾਇਤਾਂ।'
                  : language === 'hi'
                  ? 'पटियाला में 78 मिमी वर्षा दर्ज। फसल व मवेशी सुरक्षा हेतु आवश्यक निर्देश।'
                  : '78mm rain recorded in Patiala. Follow these essential tips to protect crops and livestock.'}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => handleSpeak('agri-hero', agriHeroVoiceText)}
            className={`shrink-0 px-3.5 py-2 rounded-lg font-semibold text-xs flex items-center gap-2 border transition-colors ${
              isSpeaking && activeSpeechKey === 'agri-hero'
                ? 'bg-amber-400 text-slate-950 border-amber-500 shadow-xs'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-800 border-slate-300'
            }`}
          >
            {isSpeaking && activeSpeechKey === 'agri-hero' ? (
              <>
                <VolumeX className="w-4 h-4 text-slate-950" />
                <span>{t('simple.voiceStop', 'Stop Audio')}</span>
              </>
            ) : (
              <>
                <Volume2 className="w-4 h-4 text-slate-600" />
                <span>{language === 'pa' ? 'ਸਾਰੀ ਸਲਾਹ ਸੁਣੋ' : language === 'hi' ? 'सलाह सुनें' : 'Listen Advisory'}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* 2. 4 FARM DIRECTIVES (Uniform Institutional Grid) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Rule 1: No Spray */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 flex flex-col justify-between transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg hover:border-red-300 cursor-pointer shadow-xs">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-red-50 text-red-700 border border-red-200">
                {language === 'pa' ? 'ਬਿਲਕੁਲ ਨਾ ਕਰੋ' : language === 'hi' ? 'बिल्कुल न करें' : 'PROHIBITED'}
              </span>
              <Ban className="w-4 h-4 text-red-600" />
            </div>
            <h4 className="text-sm font-bold text-slate-900 mt-1">
              {language === 'pa' ? 'ਅੱਜ ਕੋਈ ਸਪਰੇਅ ਨਾ ਕਰੋ' : language === 'hi' ? 'आज कोई स्प्रे न करें' : 'Do Not Spray Chemicals'}
            </h4>
            <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
              {language === 'pa'
                ? 'ਮੀਂਹ ਸਾਰੀ ਦਵਾਈ ਵਹਾ ਕੇ ਲੈ ਜਾਵੇਗਾ ਅਤੇ ਪੈਸੇ ਦੀ ਬਰਬਾਦੀ ਹੋਵੇਗੀ।'
                : language === 'hi'
                ? 'बारिश सारी दवा बहा ले जाएगी, लागत व्यर्थ होगी।'
                : 'Precipitation will wash away foliar sprays and fertilizers.'}
            </p>
          </div>
        </div>

        {/* Rule 2: Open Field Drainage */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 flex flex-col justify-between transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg hover:border-emerald-300 cursor-pointer shadow-xs">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-50 text-emerald-800 border border-emerald-200">
                {language === 'pa' ? 'ਤੁਰੰਤ ਕਰੋ' : language === 'hi' ? 'तुरंत करें' : 'ACTION REQUIRED'}
              </span>
              <Droplets className="w-4 h-4 text-emerald-600" />
            </div>
            <h4 className="text-sm font-bold text-slate-900 mt-1">
              {language === 'pa' ? 'ਖੇਤਾਂ ਚੋਂ ਪਾਣੀ ਨਿਕਾਸੀ ਖੋਲ੍ਹੋ' : language === 'hi' ? 'खेतों से पानी निकासी खोलें' : 'Clear Paddy Field Drainage'}
            </h4>
            <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
              {language === 'pa'
                ? 'ਬੰਨੇ ਕੱਟ ਕੇ ਨਾਲੀਆਂ ਖੋਲ੍ਹੋ ਤਾਂ ਜੋ ਝੋਨੇ ਦੀਆਂ ਜੜ੍ਹਾਂ ਨਾ ਗਲਣ।'
                : language === 'hi'
                ? 'नालियां खोलें ताकि धान की जड़ें सड़ने से बच सकें।'
                : 'Cut bunds to discharge excess standing water and prevent root decay.'}
            </p>
          </div>
        </div>

        {/* Rule 3: Cover Cattle Fodder */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 flex flex-col justify-between transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg hover:border-amber-300 cursor-pointer shadow-xs">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-50 text-amber-800 border border-amber-200">
                {language === 'pa' ? 'ਸੰਭਾਲੋ' : language === 'hi' ? 'सुरक्षित करें' : 'PROTECT'}
              </span>
              <ShieldCheck className="w-4 h-4 text-amber-600" />
            </div>
            <h4 className="text-sm font-bold text-slate-900 mt-1">
              {language === 'pa' ? 'ਤੂੜੀ ਤੇ ਸੁੱਕਾ ਚਾਰਾ ਢੱਕੋ' : language === 'hi' ? 'सूखा चारा व अनाज ढकें' : 'Cover Fodder with Tarpaulins'}
            </h4>
            <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
              {language === 'pa'
                ? 'ਤੂੜੀ ਦੇ ਕੁੱਪ ਉੱਤੇ ਪਲਾਸਟਿਕ ਤਰਪਾਲ ਪਾਓ ਅਤੇ ਉੱਚੀ ਥਾਂ ਰੱਖੋ।'
                : language === 'hi'
                ? 'भूसे व चारे पर तिरपाल डालें और ऊंची जगह पर रखें।'
                : 'Prevent fungal mold by securing dry fodder stores on elevated plinths.'}
            </p>
          </div>
        </div>

        {/* Rule 4: Cattle Health */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 flex flex-col justify-between transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg hover:border-blue-300 cursor-pointer shadow-xs">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-50 text-blue-800 border border-blue-200">
                {language === 'pa' ? 'ਪਸ਼ੂ ਸੰਭਾਲ' : language === 'hi' ? 'पशु स्वास्थ्य' : 'LIVESTOCK'}
              </span>
              <Activity className="w-4 h-4 text-blue-600" />
            </div>
            <h4 className="text-sm font-bold text-slate-900 mt-1">
              {language === 'pa' ? 'ਡੰਗਰਾਂ ਨੂੰ ਗੰਦੇ ਪਾਣੀ ਤੋਂ ਬਚਾਓ' : language === 'hi' ? 'मवेशियों को दूषित जल से बचाएं' : 'Protect Livestock Water'}
            </h4>
            <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
              {language === 'pa'
                ? 'ਗੰਦਾ ਪਾਣੀ ਪੀਣ ਨਾਲ ਗਲਘੋਟੂ ਅਤੇ ਪੇਟ ਦੇ ਕੀੜਿਆਂ ਦਾ ਰੋਗ ਫੈਲਦਾ ਹੈ।'
                : language === 'hi'
                ? 'दूषित पानी से गलघोंटू व संक्रामक रोग फैलते हैं।'
                : 'Supply fresh tubewell water to prevent waterborne hemorrhagic septicemia.'}
            </p>
          </div>
        </div>
      </div>

      {/* 3. 3-DAY VISUAL OUTLOOK FOR FARMERS */}
      <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs">
        <div className="flex items-center gap-2 mb-3">
          <Calendar className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm sm:text-base font-bold text-slate-900">
            {language === 'pa' ? 'ਅਗਲੇ 3 ਦਿਨਾਂ ਦਾ ਮੌਸਮ' : language === 'hi' ? 'अगले 3 दिनों का मौसम' : '3-Day Agro-Weather Outlook'}
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Day 1: Today */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center gap-3 transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-md cursor-pointer">
            <div className="w-9 h-9 rounded-lg bg-white border border-slate-200 text-blue-600 flex items-center justify-center shrink-0">
              <CloudRain className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-500 block">
                {language === 'pa' ? 'ਅੱਜ (ਦਿਨ 1)' : language === 'hi' ? 'आज (दिन 1)' : 'Today (Day 1)'}
              </span>
              <span className="text-xs font-bold text-slate-900 block">
                {language === 'pa' ? 'ਭਾਰੀ ਮੀਂਹ (78mm)' : language === 'hi' ? 'भारी वर्षा (78mm)' : 'Heavy Rain (78mm)'}
              </span>
              <span className="text-[10px] font-medium text-red-600">
                {language === 'pa' ? 'ਸਪਰੇਅ ਬੰਦ' : language === 'hi' ? 'छिड़काव स्थगित' : 'No Field Spraying'}
              </span>
            </div>
          </div>

          {/* Day 2: Tomorrow */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center gap-3 transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-md cursor-pointer">
            <div className="w-9 h-9 rounded-lg bg-white border border-slate-200 text-amber-600 flex items-center justify-center shrink-0">
              <CloudSun className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-500 block">
                {language === 'pa' ? 'ਕੱਲ੍ਹ (ਦਿਨ 2)' : language === 'hi' ? 'कल (दिन 2)' : 'Tomorrow (Day 2)'}
              </span>
              <span className="text-xs font-bold text-slate-900 block">
                {language === 'pa' ? 'ਬੂੰਦਾ-ਬਾਂਦੀ' : language === 'hi' ? 'हल्की वर्षा' : 'Scattered Showers'}
              </span>
              <span className="text-[10px] font-medium text-amber-700">
                {language === 'pa' ? 'ਸਾਵਧਾਨੀ ਰੱਖੋ' : language === 'hi' ? 'सावधानी रखें' : 'Caution Advised'}
              </span>
            </div>
          </div>

          {/* Day 3: Day 3 */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center gap-3 transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-md cursor-pointer">
            <div className="w-9 h-9 rounded-lg bg-white border border-slate-200 text-emerald-600 flex items-center justify-center shrink-0">
              <Sun className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-500 block">
                {language === 'pa' ? 'ਪਰਸੋਂ (ਦਿਨ 3)' : language === 'hi' ? 'परसों (दिन 3)' : 'Day 3 (Clear Sky)'}
              </span>
              <span className="text-xs font-bold text-slate-900 block">
                {language === 'pa' ? 'ਸਾਫ਼ ਧੁੱਪ' : language === 'hi' ? 'साफ धूप' : 'Sunny & Dry'}
              </span>
              <span className="text-[10px] font-medium text-emerald-700">
                {language === 'pa' ? 'ਸਪਰੇਅ ਲਈ ਢੁਕਵਾਂ' : language === 'hi' ? 'छिड़काव योग्य' : 'Safe to Spray'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
