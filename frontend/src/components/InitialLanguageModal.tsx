import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { Language } from '../types';
import { Check } from 'lucide-react';

export const InitialLanguageModal: React.FC = () => {
  const { language, setLanguage, isLanguageModalOpen, setIsLanguageModalOpen } = useLanguage();
  const [selected, setSelected] = useState<Language>(language);

  if (!isLanguageModalOpen) return null;

  const handleConfirm = () => {
    setLanguage(selected);
    setIsLanguageModalOpen(false);
  };

  const options: {
    id: Language;
    label: string;
    script: string;
    region: string;
    sample: string;
    voiceText: string;
    flag: string;
  }[] = [
    {
      id: 'en',
      label: 'English',
      script: 'Simple Voice',
      region: 'All regions',
      sample: 'Weather & flood safety alerts (Voice enabled)',
      voiceText: 'Welcome! Listen to live weather and flood safety alerts.',
      flag: '🌐 English',
    },
    {
      id: 'pa',
      label: 'ਪੰਜਾਬੀ',
      script: 'ਗੁਰਮੁਖੀ',
      region: 'ਪੰਜਾਬ',
      sample: 'ਮੌਸਮ ਤੇ ਹੜ੍ਹ ਚੇਤਾਵਨੀ (ਸੁਣੋ ਤੇ ਦੇਖੋ)',
      voiceText: 'ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਪੰਜਾਬੀ ਵਿੱਚ ਮੌਸਮ ਅਤੇ ਹੜ੍ਹ ਦੀ ਜਾਣਕਾਰੀ ਸੁਣੋ।',
      flag: '🇮🇳 ਪੰਜਾਬ',
    },
    {
      id: 'hi',
      label: 'हिन्दी',
      script: 'देवनागरी',
      region: 'भारत',
      sample: 'मौसम और बाढ़ चेतावनी (सुनें और देखें)',
      voiceText: 'नमस्ते! हिन्दी में मौसम और बाढ़ की जानकारी सुनें।',
      flag: '🇮🇳 हिन्दी',
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md animate-in fade-in duration-200">
      <div
        id="initial-language-modal"
        className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden"
      >
        {/* Top Header Decorative Banner */}
        <div className="bg-gradient-to-r from-blue-700 via-indigo-700 to-blue-800 px-6 py-6 text-white text-center sm:text-left">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-white/15 backdrop-blur-sm border border-white/20 flex items-center justify-center text-2xl shadow-inner">
              🌧️
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight flex items-center gap-2">
                WeatherGPT
              </h2>
              <p className="text-xs text-blue-100 mt-0.5">
                {selected === 'pa'
                  ? 'ਮੌਸਮ ਤੇ ਹੜ੍ਹ ਸੁਰੱਖਿਆ ਪ੍ਰਣਾਲੀ'
                  : selected === 'hi'
                  ? 'मौसम व बाढ़ सुरक्षा प्रणाली'
                  : 'Weather & Flood Safety'}
              </p>
            </div>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6">
          <div className="mb-4 text-center sm:text-left">
            <h3 className="text-lg font-bold text-slate-900">
              {selected === 'pa'
                ? 'ਆਪਣੀ ਭਾਸ਼ਾ ਚੁਣੋ'
                : selected === 'hi'
                ? 'अपनी भाषा चुनें'
                : 'Select Your Language'}
            </h3>
            <p className="text-xs text-slate-600 mt-1">
              {selected === 'pa'
                ? 'ਮੌਸਮ ਅੱਪਡੇਟ ਲਈ ਆਪਣੀ ਪਸੰਦੀਦਾ ਭਾਸ਼ਾ ਚੁਣੋ'
                : selected === 'hi'
                ? 'मौसम अपडेट हेतु अपनी पसंदीदा भाषा चुनें'
                : 'Choose your preferred language for weather updates'}
            </p>
          </div>

          {/* Language Cards */}
          <div className="space-y-3">
            {options.map((opt) => {
              const isChosen = selected === opt.id;

              return (
                <div
                  key={opt.id}
                  onClick={() => setSelected(opt.id)}
                  className={`cursor-pointer p-4 rounded-2xl border-2 transition-all flex items-center justify-between gap-3 ${
                    isChosen
                      ? 'border-blue-600 bg-blue-50/90 shadow-md ring-2 ring-blue-500/20'
                      : 'border-slate-200 hover:border-blue-300 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-3.5 flex-1">
                    <div
                      className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-base transition-colors ${
                        isChosen ? 'bg-blue-600 text-white shadow-sm' : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {opt.id === 'pa' ? 'ਪੰ' : opt.id === 'hi' ? 'हि' : 'En'}
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-bold text-slate-900">{opt.label}</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">
                          {opt.flag}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">{opt.sample}</p>
                    </div>
                  </div>

                  {/* Radio circle check */}
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center border-2 transition-all ${
                      isChosen ? 'bg-blue-600 border-blue-600 text-white' : 'border-slate-300 bg-white'
                    }`}
                  >
                    {isChosen && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Action button */}
          <div className="mt-6 pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-3">
            <span className="text-xs text-slate-500 flex items-center gap-1.5">
              <span>💡</span>
              {selected === 'pa'
                ? 'ਕੋਈ ਵੀ ਵਿਅਕਤੀ ਆਸਾਨੀ ਨਾਲ ਸਮਝ ਸਕਦਾ ਹੈ'
                : selected === 'hi'
                ? 'कोई भी आसानी से समझ सकता है'
                : 'Designed for simple visual understanding'}
            </span>

            <button
              type="button"
              onClick={handleConfirm}
              className="w-full sm:w-auto px-8 py-3.5 bg-blue-600 hover:bg-blue-700 text-white text-base font-bold rounded-xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2"
            >
              <span>
                {selected === 'pa'
                  ? 'ਅੱਗੇ ਵਧੋ (ਸ਼ੁਰੂ ਕਰੋ) ➔'
                  : selected === 'hi'
                  ? 'आगे बढ़ें (शुरू करें) ➔'
                  : 'Start WeatherGPT ➔'}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
