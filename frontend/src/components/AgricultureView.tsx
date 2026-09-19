import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { SimpleAgricultureSection } from './SimpleAgricultureSection';
import { FARM_ACTIONS, AGRI_RISK_FACTORS } from '../data/mockData';
import { FarmActionItem } from '../types';
import {
  CloudRain,
  Wind,
  Droplets,
  Sprout,
  AlertTriangle,
  Sun,
  CloudLightning,
  PhoneCall,
  Building2,
  Copy,
  Check,
  CheckCircle2,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

export const AgricultureView: React.FC = () => {
  const { t, language } = useLanguage();
  const [actions, setActions] = useState<FarmActionItem[]>(FARM_ACTIONS);
  const [copiedNumber, setCopiedNumber] = useState<string | null>(null);

  const toggleFarmAction = (id: string) => {
    setActions((prev) =>
      prev.map((item) => {
        if (item.id !== id) return item;
        const nextStatus =
          item.status === 'In Progress' ? 'Completed' : item.status === 'Pending' ? 'In Progress' : 'Pending';
        return { ...item, status: nextStatus };
      })
    );
  };

  const handleCopy = (num: string) => {
    navigator.clipboard.writeText(num);
    setCopiedNumber(num);
    setTimeout(() => setCopiedNumber(null), 2000);
  };

  // Mock Soil Moisture curve data for Recharts
  const soilMoistureData = [
    { time: '00:00', moisture: 34 },
    { time: '04:00', moisture: 36 },
    { time: '08:00', moisture: 39 },
    { time: '12:00', moisture: 42.5 },
    { time: '16:00', moisture: 43.8 },
    { time: '20:00', moisture: 41.2 },
    { time: '24:00', moisture: 38.5 },
  ];

  return (
    <div className="space-y-6 pb-12 font-sans">
      {/* 1. Citizen Farmer Directives (Data Kept & Simplified) */}
      <SimpleAgricultureSection />

      {/* 2. Weather Forecast Strip */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col lg:flex-row items-start lg:items-center justify-between gap-5">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-2xl border border-blue-100">
            <CloudRain className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl sm:text-4xl font-extrabold text-slate-950 font-mono">31°C</span>
              <span className="text-sm font-semibold text-slate-700">
                {language === 'pa' ? 'ਭਾਰੀ ਮੀਂਹ / ਬੱਦਲਵਾਈ' : language === 'hi' ? 'भारी वर्षा / बादल' : 'Heavy Rain / Overcast'}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {language === 'pa' ? 'ਪਟਿਆਲਾ • ਸਮਾਣਾ ਤੇ ਸਨੌਰ ਬਲਾਕ' : language === 'hi' ? 'पटियाला • समाना व सनौर ब्लॉक' : 'Patiala, Punjab • Samana & Sanaur'}
            </p>
            <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-600">
              <span className="flex items-center gap-1">
                <Droplets className="w-3.5 h-3.5 text-blue-500" />
                <span>{language === 'pa' ? 'ਨਮੀ:' : language === 'hi' ? 'नमी:' : 'Humidity:'}</span>
                <strong className="font-mono text-slate-800">64%</strong>
              </span>
              <span className="flex items-center gap-1">
                <Wind className="w-3.5 h-3.5 text-slate-400" />
                <span>{language === 'pa' ? 'ਹਵਾ:' : language === 'hi' ? 'हवा:' : 'Wind:'}</span>
                <strong className="font-mono text-slate-800">18 km/h SE</strong>
              </span>
              <span className="flex items-center gap-1">
                <CloudRain className="w-3.5 h-3.5 text-indigo-500" />
                <span>{language === 'pa' ? '24 ਘੰਟੇ ਮੀਂਹ:' : language === 'hi' ? '24 घंटे वर्षा:' : '24h Rain:'}</span>
                <strong className="font-mono text-slate-800">78.4 mm</strong>
              </span>
            </div>
          </div>
        </div>

        {/* 3-Day Forecast Cards */}
        <div className="grid grid-cols-3 gap-2.5 w-full lg:w-auto">
          <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100 text-center min-w-[85px] transition-all duration-200 transform hover:scale-105 hover:-translate-y-1 hover:shadow-md hover:bg-white hover:border-slate-300 cursor-pointer">
            <span className="text-[11px] font-medium text-slate-500 block">{language === 'pa' ? 'ਦਿਨ 1' : language === 'hi' ? 'दिन 1' : 'Day 1'}</span>
            <CloudLightning className="w-4 h-4 mx-auto my-1 text-amber-500" />
            <span className="text-xs font-mono font-bold text-slate-800 block">33° / 24°</span>
            <span className="text-[10px] text-blue-600 font-mono">70% Rain</span>
          </div>

          <div className="p-2.5 bg-blue-50/60 rounded-xl border border-blue-200 text-center min-w-[85px] transition-all duration-200 transform hover:scale-105 hover:-translate-y-1 hover:shadow-md hover:bg-blue-50 cursor-pointer">
            <span className="text-[11px] font-bold text-blue-900 block">{language === 'pa' ? 'ਪੀਕ ਦਿਨ 2' : language === 'hi' ? 'पीक दिन 2' : 'Peak Day 2'}</span>
            <CloudRain className="w-4 h-4 mx-auto my-1 text-blue-600" />
            <span className="text-xs font-mono font-bold text-slate-800 block">32° / 23°</span>
            <span className="text-[10px] text-red-600 font-mono font-bold">85% Heavy</span>
          </div>

          <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100 text-center min-w-[85px] transition-all duration-200 transform hover:scale-105 hover:-translate-y-1 hover:shadow-md hover:bg-white hover:border-slate-300 cursor-pointer">
            <span className="text-[11px] font-medium text-slate-500 block">{language === 'pa' ? 'ਦਿਨ 3' : language === 'hi' ? 'दिन 3' : 'Day 3'}</span>
            <Sun className="w-4 h-4 mx-auto my-1 text-amber-500" />
            <span className="text-xs font-mono font-bold text-slate-800 block">29° / 22°</span>
            <span className="text-[10px] text-emerald-600 font-mono">30% Clear</span>
          </div>
        </div>
      </div>

      {/* 3. ROW 1: CROP STATUS & SPRAY WINDOW (Balanced Equal Heights) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-stretch">
        {/* Card A: Crop Status & Environment */}
        <div id="card-crop-status" className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Sprout className="w-4 h-4 text-emerald-600" />
                <h3 className="text-base font-bold text-slate-900">
                  {language === 'pa' ? 'ਫ਼ਸਲ ਸਥਿਤੀ ਤੇ ਵਾਤਾਵਰਣ' : language === 'hi' ? 'फसल स्थिति एवं वातावरण' : 'Crop Status & Field Environment'}
                </h3>
              </div>
              <span className="text-xs font-mono text-slate-400">
                {language === 'pa' ? 'ਸਰਗਰਮ ਸੀਜ਼ਨ' : language === 'hi' ? 'सक्रिय सत्र' : 'Active Cycle'}
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">{language === 'pa' ? 'ਮੁੱਖ ਫ਼ਸਲ:' : language === 'hi' ? 'मुख्य फसल:' : 'Dominant Crop:'}</span>
                <span className="font-semibold text-slate-900">
                  {language === 'pa' ? 'ਝੋਨਾ / ਬਾਸਮਤੀ' : language === 'hi' ? 'धान / बासमती' : 'Paddy / Basmati Rice'}
                </span>
              </div>

              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">{language === 'pa' ? 'ਕਿਸਮ:' : language === 'hi' ? 'किस्म:' : 'Seed Variety:'}</span>
                <span className="font-mono text-slate-800">
                  {language === 'pa' ? 'ਪੂਸਾ ਬਾਸਮਤੀ 1121 / ਪੀਆਰ-126' : language === 'hi' ? 'पूसा बासमती 1121 / पीआर-126' : 'Pusa Basmati 1121 / PR-126'}
                </span>
              </div>

              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">{language === 'pa' ? 'ਵਾਧੇ ਦਾ ਪੜਾਅ:' : language === 'hi' ? 'विकास चरण:' : 'Growth Stage:'}</span>
                <span className="text-slate-800 font-medium">
                  {language === 'pa' ? 'ਸ਼ਾਖਾਵਾਂ ਫੁੱਟਣ ਦਾ ਸਮਾਂ (ਕੱਲੇ)' : language === 'hi' ? 'शाखा फूटने की अवस्था (कल्ले)' : 'Tillering Stage'}
                </span>
              </div>

              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">{language === 'pa' ? 'ਜ਼ਮੀਨੀ ਨਮੀ:' : language === 'hi' ? 'मृदा नमी:' : 'Soil Moisture:'}</span>
                <div className="text-right">
                  <span className="font-mono font-bold text-amber-700 block">
                    42.5% ({language === 'pa' ? 'ਸਮਰੱਥਾ: 38%' : language === 'hi' ? 'क्षमता: 38%' : 'Cap: 38%'})
                  </span>
                  <span className="text-[10px] font-semibold text-amber-600">
                    {language === 'pa' ? 'ਸੰਤ੍ਰਿਪਤ / ਪਾਣੀ ਭਰਨ ਦਾ ਖ਼ਤਰਾ' : language === 'hi' ? 'संतृप्त / जलभराव जोखिम' : 'Saturated / Waterlogging Risk'}
                  </span>
                </div>
              </div>

              <div className="flex justify-between py-1">
                <span className="text-slate-500">{language === 'pa' ? 'ਰਕਬਾ:' : language === 'hi' ? 'क्षेत्रफल:' : 'Command Area:'}</span>
                <span className="font-mono text-slate-800">
                  8,200 ha ({language === 'pa' ? 'ਪਟਿਆਲਾ ਬੇਸਿਨ' : language === 'hi' ? 'पटियाला बेसिन' : 'Patiala Basin'})
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Card B: Agrochemical Spray Window Optimization */}
        <div id="card-spray-window" className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Sun className="w-4 h-4 text-amber-600" />
                <h3 className="text-base font-bold text-slate-900">
                  {language === 'pa' ? 'ਸਪਰੇਅ ਕਰਨ ਲਈ ਸਹੀ ਸਮਾਂ' : language === 'hi' ? 'छिड़काव हेतु उपयुक्त समय' : 'Agrochemical Spray Window'}
                </h3>
              </div>
              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 bg-amber-50 text-amber-800 border border-amber-200 rounded">
                {language === 'pa' ? 'ਪੀ.ਏ.ਯੂ. ਸਲਾਹ' : language === 'hi' ? 'पी.ए.यू. सलाह' : 'PAU ADVISORY'}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
              <div className="p-3 rounded-xl border border-red-200 bg-red-50/60 flex flex-col justify-between transition-all duration-200 transform hover:scale-105 hover:-translate-y-0.5 hover:shadow-md hover:bg-red-50 cursor-pointer">
                <div>
                  <span className="font-bold text-red-800 block text-xs">
                    {language === 'pa' ? 'ਅੱਜ (14:00 - 22:00)' : language === 'hi' ? 'आज (14:00 - 22:00)' : 'Today (14:00 - 22:00)'}
                  </span>
                  <p className="text-slate-600 text-[11px] mt-1 leading-tight">
                    {language === 'pa' ? 'ਖ਼ਤਰਨਾਕ: ਭਾਰੀ ਮੀਂਹ ਦਵਾਈ ਵਹਾ ਦੇਵੇਗਾ।' : language === 'hi' ? 'असुरक्षित: भारी बारिश दवा बहा देगी।' : 'UNSAFE: Downpours wash off spray.'}
                  </p>
                </div>
              </div>

              <div className="p-3 rounded-xl border border-amber-200 bg-amber-50/60 flex flex-col justify-between transition-all duration-200 transform hover:scale-105 hover:-translate-y-0.5 hover:shadow-md hover:bg-amber-50 cursor-pointer">
                <div>
                  <span className="font-bold text-amber-800 block text-xs">
                    {language === 'pa' ? 'ਕੱਲ੍ਹ ਸਵੇਰੇ' : language === 'hi' ? 'कल सुबह' : 'Tomorrow Morning'}
                  </span>
                  <p className="text-slate-600 text-[11px] mt-1 leading-tight">
                    {language === 'pa' ? 'ਸਾਵਧਾਨੀ: ਪੱਤੇ ਗਿੱਲੇ ਹੋਣ ਕਰਕੇ ਅਸਰ ਘੱਟ।' : language === 'hi' ? 'सावधानी: गीली पत्तियों पर प्रभाव कम।' : 'CAUTION: Saturated canopy; wait.'}
                  </p>
                </div>
              </div>

              <div className="p-3 rounded-xl border border-emerald-200 bg-emerald-50/60 flex flex-col justify-between transition-all duration-200 transform hover:scale-105 hover:-translate-y-0.5 hover:shadow-md hover:bg-emerald-50 cursor-pointer">
                <div>
                  <span className="font-bold text-emerald-800 block text-xs">
                    {language === 'pa' ? 'ਦਿਨ 3 (ਧੁੱਪ)' : language === 'hi' ? 'दिन 3 (धूप)' : 'Day 3 (Clearing)'}
                  </span>
                  <p className="text-slate-600 text-[11px] mt-1 leading-tight">
                    {language === 'pa' ? 'ਸਭ ਤੋਂ ਵਧੀਆ: ਪੂਰਾ ਅਸਰ ਤੇ ਸੁਰੱਖਿਅਤ।' : language === 'hi' ? 'सर्वोत्तम: पूर्ण प्रभावी व सुरक्षित।' : 'OPTIMAL: High efficacy window.'}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-3.5 p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between text-xs text-slate-600">
            <span className="font-medium">
              {language === 'pa' ? '💡 ਪੀ.ਏ.ਯੂ. ਸਲਾਹ: ਤੀਜੇ ਦਿਨ ਧੁੱਪ ਨਿਕਲਣ ਤੱਕ ਕੋਈ ਸਪਰੇਅ ਨਾ ਕਰੋ।' : language === 'hi' ? '💡 पी.ए.यू. सलाह: तीसरे दिन धूप निकलने तक कोई छिड़काव न करें।' : '💡 PAU Tip: Delay all pesticide and urea sprays until Day 3 sun window.'}
            </span>
          </div>
        </div>
      </div>

      {/* 4. ROW 2: IDENTIFIED RISK FACTORS & RECOMMENDED FARM ACTIONS (Balanced 4x4 Grid) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-stretch">
        {/* Left: Identified Risk Factors */}
        <div id="card-risk-factors" className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <h3 className="text-base font-bold text-slate-900">
                  {language === 'pa' ? 'ਮੁੱਖ ਖ਼ਤਰੇ (ਖੇਤੀ ਨੁਕਸਾਨ)' : language === 'hi' ? 'मुख्य जोखिम (फसल क्षति)' : 'Identified Risk Factors'}
                </h3>
              </div>
              <span className="text-xs font-mono text-slate-400">
                {language === 'pa' ? 'ਪੀ.ਏ.ਯੂ. ਐਗਰੋ-ਮੈਟ ਮਾਡਲ' : language === 'hi' ? 'पी.ए.यू. एग्रो-मेट मॉडल' : 'PAU Agro-Met Model'}
              </span>
            </div>

            <div className="space-y-2.5">
              {AGRI_RISK_FACTORS.map((rf) => {
                const rfName =
                  language === 'pa'
                    ? rf.id === 'rf-1'
                      ? 'ਜੜ੍ਹਾਂ ਵਿੱਚ ਪਾਣੀ ਭਰਨਾ'
                      : rf.id === 'rf-2'
                      ? 'ਖਾਦ ਵਹਿਣ ਦਾ ਖ਼ਤਰਾ'
                      : rf.id === 'rf-3'
                      ? 'ਉੱਲੀ ਰੋਗ ਤੇ ਗਲਣ ਦਾ ਖ਼ਤਰਾ'
                      : 'ਤੇਜ਼ ਹਵਾ ਨਾਲ ਫ਼ਸਲ ਡਿੱਗਣ ਦਾ ਖ਼ਤਰਾ'
                    : language === 'hi'
                    ? rf.id === 'rf-1'
                      ? 'जड़ क्षेत्र में जलभराव'
                      : rf.id === 'rf-2'
                      ? 'उर्वरक बहाव जोखिम'
                      : rf.id === 'rf-3'
                      ? 'फंगल ब्लास्ट व सड़न जोखिम'
                      : 'तेज हवा से फसल गिरना'
                    : rf.name;

                const rfDesc =
                  language === 'pa'
                    ? rf.id === 'rf-1'
                      ? '10 ਸੈਂ.ਮੀ. ਤੋਂ ਵੱਧ ਖੜ੍ਹਾ ਪਾਣੀ ਨਰਮ ਬਾਸਮਤੀ ਦੀਆਂ ਜੜ੍ਹਾਂ ਨੂੰ ਨੁਕਸਾਨ ਪਹੁੰਚਾ ਸਕਦਾ ਹੈ।'
                      : rf.id === 'rf-2'
                      ? 'ਭਾਰੀ ਮੀਂਹ ਖਾਦ ਨੂੰ ਜੜ੍ਹਾਂ ਦੀ ਪਹੁੰਚ ਤੋਂ ਦੂਰ ਵਹਾ ਕੇ ਲੈ ਜਾਂਦਾ ਹੈ।'
                      : rf.id === 'rf-3'
                      ? 'ਜ਼ਿਆਦਾ ਨਮੀ (>90%) ਉੱਲੀ ਰੋਗ ਦਾ ਵੱਡਾ ਖ਼ਤਰਾ ਪੈਦਾ ਕਰਦੀ ਹੈ।'
                      : '28 ਕਿਮੀ/ਘੰਟਾ ਤੱਕ ਦੀ ਤੇਜ਼ ਹਵਾ ਲੰਬੀ ਫ਼ਸਲ ਨੂੰ ਧਰਤੀ ਤੇ ਵਿਛਾ ਸਕਦੀ ਹੈ।'
                    : language === 'hi'
                    ? rf.id === 'rf-1'
                      ? '10 सेमी से अधिक खड़ा पानी बासमती की जड़ों को नुकसान पहुंचा सकता है।'
                      : rf.id === 'rf-2'
                      ? 'भारी बारिश उर्वरक को जड़ों की पहुंच से परे बहा देती है।'
                      : rf.id === 'rf-3'
                      ? 'अधिक नमी (>90%) से फफूंद जनित रोगों का अत्यधिक जोखिम होता है।'
                      : '28 किमी/घंटा तक की हवाएं बासमती को झुका या गिरा सकती हैं।'
                    : rf.description;

                const sevLabel =
                  rf.severity === 'HIGH'
                    ? language === 'pa' ? 'ਉੱਚ' : language === 'hi' ? 'उच्च' : 'HIGH'
                    : language === 'pa' ? 'ਦਰਮਿਆਨਾ' : language === 'hi' ? 'मध्यम' : 'MEDIUM';

                const confLabel =
                  language === 'pa' ? 'ਯਕੀਨ' : language === 'hi' ? 'सटीकता' : 'conf';

                return (
                  <div key={rf.id} className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs transition-all duration-200 transform hover:scale-[1.02] hover:shadow-md hover:bg-white hover:border-slate-300 cursor-pointer">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-900">{rfName}</span>
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`font-mono text-[10px] font-bold px-1.5 py-0.5 rounded ${
                            rf.severity === 'HIGH'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {sevLabel}
                        </span>
                        <span className="font-mono text-slate-500 text-[10px]">{rf.confidence}% {confLabel}</span>
                      </div>
                    </div>
                    <p className="text-slate-600 mt-1 leading-normal text-[11px]">
                      {rfDesc}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right: Recommended Farm Actions */}
        <div id="card-farm-actions" className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <h3 className="text-base font-bold text-slate-900">
                  {language === 'pa' ? 'ਕਿਸਾਨ ਲਈ ਜ਼ਰੂਰੀ ਕਦਮ' : language === 'hi' ? 'किसान हेतु जरूरी कदम' : 'Recommended Farm Actions'}
                </h3>
              </div>
              <span className="text-xs font-mono text-slate-400">
                {language === 'pa' ? 'ਪੀ.ਏ.ਯੂ. ਅਤੇ ਆਈ.ਸੀ.ਏ.ਆਰ.' : language === 'hi' ? 'पी.ए.यू. एवं आई.सी.ए.आर.' : 'PAU & ICAR'}
              </span>
            </div>

            <div className="space-y-2.5">
              {actions.map((act) => {
                const isDone = act.status === 'Completed';
                const isInProg = act.status === 'In Progress';

                const actTitle =
                  language === 'pa'
                    ? act.id === 'farm-1'
                      ? 'ਜਲ-ਜਮਾਵ ਰੋਕਣ ਲਈ ਖੇਤ ਵਿੱਚੋਂ ਪਾਣੀ ਨਿਕਾਸੀ ਦੀਆਂ ਨਾਲੀਆਂ ਸਾਫ਼ ਕਰੋ'
                      : act.id === 'farm-2'
                      ? 'ਮੀਂਹ ਦੌਰਾਨ ਰਸਾਇਣਕ ਸਪਰੇਅ ਅਤੇ ਯੂਰੀਆ ਪਾਉਣਾ ਬੰਦ ਰੱਖੋ'
                      : act.id === 'farm-3'
                      ? 'ਕੱਟੀ ਹੋਈ ਫ਼ਸਲ ਜਾਂ ਜਿਣਸ ਨੂੰ ਢੱਕੀ ਹੋਈ ਸਟੋਰੇਜ ਵਿੱਚ ਰੱਖੋ'
                      : 'ਮੀਂਹ ਤੋਂ ਬਾਅਦ ਫ਼ਸਲ ਵਿੱਚ ਕੀੜੇ-ਮਕੌੜੇ ਅਤੇ ਉੱਲੀ ਰੋਗ ਦੀ ਜਾਂਚ ਕਰੋ'
                    : language === 'hi'
                    ? act.id === 'farm-1'
                      ? 'जलभराव रोकने हेतु खेत की जल निकासी नालियों को साफ करें'
                      : act.id === 'farm-2'
                      ? 'बारिश के दौरान रासायनिक छिड़काव एवं यूरिया डालना बंद रखें'
                      : act.id === 'farm-3'
                      ? 'कटी हुई उपज को सुरक्षित व ढके हुए स्थान पर रखें'
                      : 'बारिश के बाद फसल में कीट व फफूंद संक्रमण की जांच करें'
                    : act.title;

                const actDeadline =
                  language === 'pa'
                    ? act.id === 'farm-1'
                      ? 'ਸ਼ਾਮ 18:00 IST ਤੋਂ ਪਹਿਲਾਂ'
                      : act.id === 'farm-2'
                      ? 'ਅਗਲੇ 48 ਘੰਟੇ'
                      : act.id === 'farm-3'
                      ? 'ਤੁਰੰਤ'
                      : 'ਅਗਲੇ 3 ਦਿਨ'
                    : language === 'hi'
                    ? act.id === 'farm-1'
                      ? '18:00 IST से पूर्व'
                      : act.id === 'farm-2'
                      ? 'आगामी 48 घंटे'
                      : act.id === 'farm-3'
                      ? 'तत्काल'
                      : 'आगामी 3 दिन'
                    : act.deadline;

                const statusLabel = isDone
                  ? language === 'pa' ? 'ਮੁਕੰਮਲ' : language === 'hi' ? 'पूर्ण' : 'Completed'
                  : isInProg
                  ? language === 'pa' ? 'ਚਾਲੂ ਹੈ' : language === 'hi' ? 'प्रगति पर' : 'In Progress'
                  : language === 'pa' ? 'ਬਾਕੀ ਹੈ' : language === 'hi' ? 'लंबित' : 'Pending';

                const buttonLabel = isDone
                  ? language === 'pa' ? 'ਦੁਬਾਰਾ ਖੋਲ੍ਹੋ' : language === 'hi' ? 'पुनः खोलें' : 'Reopen'
                  : language === 'pa' ? 'ਹੋ ਗਿਆ' : language === 'hi' ? 'संपन्न' : 'Done';

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
                          {actTitle}
                        </p>
                        <span className="text-[10px] text-slate-400 font-mono block">
                          {actDeadline}
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
                        {statusLabel}
                      </span>

                      <button
                        type="button"
                        onClick={() => toggleFarmAction(act.id)}
                        className={`text-[11px] px-2 py-0.5 rounded-lg border font-medium transition-colors cursor-pointer ${
                          isDone
                            ? 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                            : 'bg-emerald-800 border-emerald-800 text-white hover:bg-emerald-900'
                        }`}
                      >
                        {buttonLabel}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* 5. FIELD DIAGNOSTICS: SOIL MOISTURE SATURATION TRAJECTORY */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              {language === 'pa' ? '48 ਘੰਟੇ ਜ਼ਮੀਨੀ ਨਮੀ ਦਾ ਅਨੁਮਾਨ (% Soil Moisture)' : language === 'hi' ? '48 घंटे मृदा नमी स्तर अनुमान (% Soil Moisture)' : '48-Hour Soil Saturation Trajectory (% Volumetric Water Content)'}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {language === 'pa' ? 'ਖੇਤਰੀ ਸਮਰੱਥਾ (38%) ਪਾਰ ਹੋਈ • ਜ਼ਮੀਨ ਵਿੱਚ ਵਾਧੂ ਪਾਣੀ ਭਰਨ ਦਾ ਖ਼ਤਰਾ' : language === 'hi' ? 'क्षेत्रीय क्षमता (38%) पार • भूमि में अतिरिक्त जलभराव जोखिम' : 'Field Capacity (38%) breached at 06:00 IST • Elevated Hypoxia Risk'}
            </p>
          </div>
          <div className="flex items-center gap-3 text-[11px] font-mono">
            <span className="flex items-center gap-1.5 text-blue-600 font-semibold">
              <span className="w-2.5 h-2.5 rounded-sm bg-blue-500" />
              {language === 'pa' ? 'ਦਰਜ ਨਮੀ' : language === 'hi' ? 'दर्ज नमी' : 'Observed Moisture'}
            </span>
            <span className="flex items-center gap-1.5 text-red-500 font-semibold">
              <span className="w-3 h-0.5 bg-red-500" />
              {language === 'pa' ? 'ਖ਼ਤਰੇ ਦੀ ਹੱਦ (38%)' : language === 'hi' ? 'खतरे की सीमा (38%)' : 'Saturation Threshold (38%)'}
            </span>
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={soilMoistureData}>
              <defs>
                <linearGradient id="moistureGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} />
              <YAxis domain={[30, 48]} stroke="#94a3b8" fontSize={11} unit="%" />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', border: 'none', color: '#fff' }}
                formatter={(val: any) => [`${val}%`, language === 'pa' ? 'ਜ਼ਮੀਨੀ ਨਮੀ' : language === 'hi' ? 'मृदा नमी' : 'Soil Moisture']}
              />
              <ReferenceLine y={38} stroke="#ef4444" strokeDasharray="4 4" label={{ value: language === 'pa' ? 'ਖੇਤਰੀ ਸਮਰੱਥਾ 38%' : language === 'hi' ? 'क्षेत्रीय क्षमता 38%' : 'Field Capacity 38%', fill: '#ef4444', fontSize: 10, position: 'insideTopRight' }} />
              <Area type="monotone" dataKey="moisture" stroke="#2563eb" strokeWidth={2.5} fillOpacity={1} fill="url(#moistureGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 6. OFFICIAL AGRICULTURAL SUPPORT HELPLINES (BOTTOM-MOST SECTION) */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <Building2 className="w-5 h-5 text-emerald-600" />
            <div>
              <h3 className="text-base font-bold text-slate-900">
                {language === 'pa' ? 'ਸਰਕਾਰੀ ਕਿਸਾਨ ਹੈਲਪਲਾਈਨ' : language === 'hi' ? 'सरकारी कृषि हेल्पलाइन एवं सहायता' : 'Official Agricultural Support Helplines'}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                {language === 'pa' ? 'ਮੁਫ਼ਤ ਸਰਕਾਰੀ ਸਲਾਹ ਤੇ ਫ਼ਸਲ ਬਚਾਓ ਸਹਾਇਤਾ ਨੰਬਰ' : language === 'hi' ? 'मुफ्त सरकारी परामर्श एवं फसल सुरक्षा सहायता' : 'Toll-free verified helpline numbers for farmers'}
              </p>
            </div>
          </div>
          <span className="text-xs font-mono px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-md font-semibold">
            {language === 'pa' ? 'ਮੁਫ਼ਤ 24x7' : language === 'hi' ? 'टोल-फ्री 24x7' : 'Toll-Free 24x7'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
          {/* Kisan Call Center */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg hover:bg-white hover:border-emerald-300 cursor-pointer">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded font-mono">
                  {language === 'pa' ? 'ਮੁਫ਼ਤ ਕਾਲ' : language === 'hi' ? 'टोल-फ्री' : 'TOLL-FREE 24X7'}
                </span>
                <button
                  type="button"
                  onClick={() => handleCopy('1800-180-1551')}
                  className="text-xs text-slate-400 hover:text-slate-700 flex items-center gap-1 cursor-pointer"
                  title="Copy number"
                >
                  {copiedNumber === '1800-180-1551' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span className="text-[11px] font-medium">{copiedNumber === '1800-180-1551' ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <span className="text-xl font-bold text-slate-950 font-mono block mt-2">1800-180-1551</span>
              <p className="text-xs font-medium text-slate-600 mt-1">
                {language === 'pa' ? 'ਰਾਸ਼ਟਰੀ ਕਿਸਾਨ ਕਾਲ ਸੈਂਟਰ' : language === 'hi' ? 'राष्ट्रीय किसान कॉल सेंटर' : 'National Kisan Call Center'}
              </p>
            </div>
            <a
              href="tel:18001801551"
              className="mt-3 w-full py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-colors"
            >
              <PhoneCall className="w-3.5 h-3.5" />
              <span>{language === 'pa' ? 'ਕਾਲ ਕਰੋ' : language === 'hi' ? 'कॉल करें' : 'Call Now'}</span>
            </a>
          </div>

          {/* PAU Ludhiana Agronomy Desk */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg hover:bg-white hover:border-blue-300 cursor-pointer">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-blue-700 bg-blue-100 px-2 py-0.5 rounded font-mono">
                  {language === 'pa' ? 'ਮਾਹਿਰ ਸਲਾਹ' : language === 'hi' ? 'वैज्ञानिक परामर्श' : 'AGRI EXPERTS'}
                </span>
                <button
                  type="button"
                  onClick={() => handleCopy('0161-2401960')}
                  className="text-xs text-slate-400 hover:text-slate-700 flex items-center gap-1 cursor-pointer"
                  title="Copy number"
                >
                  {copiedNumber === '0161-2401960' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span className="text-[11px] font-medium">{copiedNumber === '0161-2401960' ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <span className="text-xl font-bold text-slate-950 font-mono block mt-2">0161-2401960</span>
              <p className="text-xs font-medium text-slate-600 mt-1">
                {language === 'pa' ? 'ਪੀ.ਏ.ਯੂ. ਲੁਧਿਆਣਾ ਖੇਤੀ ਡੈਸਕ' : language === 'hi' ? 'पी.ए.यू. लुधियाना कृषि वैज्ञानिक' : 'PAU Ludhiana Agronomy Desk'}
              </p>
            </div>
            <a
              href="tel:01612401960"
              className="mt-3 w-full py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-colors"
            >
              <PhoneCall className="w-3.5 h-3.5" />
              <span>{language === 'pa' ? 'ਕਾਲ ਕਰੋ' : language === 'hi' ? 'कॉल करें' : 'Call Now'}</span>
            </a>
          </div>

          {/* District Disaster & Agri Relief Desk */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg hover:bg-white hover:border-amber-300 cursor-pointer">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 bg-amber-100 px-2 py-0.5 rounded font-mono">
                  {language === 'pa' ? 'ਜ਼ਿਲ੍ਹਾ ਕੰਟਰੋਲ' : language === 'hi' ? 'जिला कंट्रोल' : 'DISTRICT RELIEF'}
                </span>
                <button
                  type="button"
                  onClick={() => handleCopy('1077')}
                  className="text-xs text-slate-400 hover:text-slate-700 flex items-center gap-1 cursor-pointer"
                  title="Copy number"
                >
                  {copiedNumber === '1077' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span className="text-[11px] font-medium">{copiedNumber === '1077' ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <span className="text-xl font-bold text-slate-950 font-mono block mt-2">1077</span>
              <p className="text-xs font-medium text-slate-600 mt-1">
                {language === 'pa' ? 'ਪਟਿਆਲਾ ਆਫ਼ਤ ਤੇ ਕਿਸਾਨ ਰਾਹਤ ਕੰਟਰੋਲ' : language === 'hi' ? 'पटियाला आपदा एवं किसान राहत कक्ष' : 'Patiala DEOC Flood & Crop Relief'}
              </p>
            </div>
            <a
              href="tel:1077"
              className="mt-3 w-full py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-colors"
            >
              <PhoneCall className="w-3.5 h-3.5" />
              <span>{language === 'pa' ? 'ਕਾਲ ਕਰੋ' : language === 'hi' ? 'कॉल करें' : 'Call Now'}</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
