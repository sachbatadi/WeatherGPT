import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { Phone, PhoneCall, Copy, Check, ShieldAlert, HeartHandshake, PhoneForwarded } from 'lucide-react';

export const EmergencyHelplineBar: React.FC = () => {
  const { language } = useLanguage();
  const [copiedNumber, setCopiedNumber] = useState<string | null>(null);

  const helplines = [
    {
      number: '112',
      tel: '112',
      title: language === 'pa' ? '112 ਕੌਮੀ ਐਮਰਜੈਂਸੀ ਹੈਲਪਲਾਈਨ' : language === 'hi' ? '112 राष्ट्रीय आपातकालीन सेवा' : '112 National Emergency',
      subtitle: language === 'pa' ? 'ਪੁਲਿਸ, ਅੱਗ ਬੁਝਾਊ, ਐਸ.ਡੀ.ਆਰ.ਐਫ. ਬਚਾਅ' : language === 'hi' ? 'पुलिस, अग्निशमन, एसडीआरएफ बचाव' : 'Police, Fire, SDRF Flood Rescue',
      tag: language === 'pa' ? '24x7 ਸਰਗਰਮ' : language === 'hi' ? '24x7 सक्रिय' : '24x7 Direct',
      isPrimary: true,
    },
    {
      number: '1077',
      tel: '1077',
      title: language === 'pa' ? '1077 ਜ਼ਿਲ੍ਹਾ ਆਫ਼ਤ ਕੰਟਰੋਲ ਰੂਮ' : language === 'hi' ? '1077 जिला आपदा नियंत्रण कक्ष' : '1077 District Disaster Room',
      subtitle: language === 'pa' ? 'ਪਟਿਆਲਾ ਡੀ.ਈ.ਓ.ਸੀ. ਹੜ੍ਹ ਸਹਾਇਤਾ' : language === 'hi' ? 'पटियाला डीईओसी बाढ़ सहायता' : 'Patiala DEOC Flood Response',
      tag: language === 'pa' ? 'ਟੋਲ-ਫ੍ਰੀ' : language === 'hi' ? 'टोल-फ्री' : 'Toll-Free',
      isPrimary: false,
    },
    {
      number: '108',
      tel: '108',
      title: language === 'pa' ? '108 ਐਂਬੂਲੈਂਸ ਤੇ ਮੈਡੀਕਲ' : language === 'hi' ? '108 एम्बुलेंस व चिकित्सा सेवा' : '108 Medical Ambulance',
      subtitle: language === 'pa' ? 'ਮੈਡੀਕਲ ਐਮਰਜੈਂਸੀ ਤੇ ਜ਼ਖ਼ਮੀ ਸਹਾਇਤਾ' : language === 'hi' ? 'चिकित्सा आपातकाल व प्राथमिक उपचार' : 'Emergency Trauma & Hospital Transport',
      tag: language === 'pa' ? 'ਮੁਫ਼ਤ ਸੇਵਾ' : language === 'hi' ? 'निःशुल्क सेवा' : 'Free 24x7',
      isPrimary: false,
    },
    {
      number: '1800-180-1551',
      tel: '18001801551',
      title: language === 'pa' ? '1800-180-1551 ਕਿਸਾਨ ਕਾਲ ਸੈਂਟਰ' : language === 'hi' ? '1800-180-1551 किसान कॉल सेंटर' : '1800-180-1551 Kisan Center',
      subtitle: language === 'pa' ? 'ਭਾਰਤ ਸਰਕਾਰ ਖੇਤੀਬਾੜੀ ਸਲਾਹ' : language === 'hi' ? 'कृषि मंत्रालय भारत सरकार' : 'GoI Ministry of Agriculture',
      tag: language === 'pa' ? 'ਕਿਸਾਨ ਸਹਾਇਤਾ' : language === 'hi' ? 'किसान सहायता' : 'Agri Support',
      isPrimary: false,
    },
  ];

  const handleCopy = (num: string) => {
    navigator.clipboard.writeText(num.replace(/[^0-9]/g, ''));
    setCopiedNumber(num);
    setTimeout(() => setCopiedNumber(null), 2000);
  };

  return (
    <div className="bg-white rounded-xl border border-red-200 p-4 shadow-xs">
      <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-red-50 text-red-700 border border-red-200">
            <PhoneCall className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              {language === 'pa'
                ? 'ਅਧਿਕਾਰਤ ਐਮਰਜੈਂਸੀ ਤੇ ਆਫ਼ਤ ਹੈਲਪਲਾਈਨ ਨੰਬਰ'
                : language === 'hi'
                ? 'अधिकृत आपातकालीन एवं आपदा हेल्पलाइन नंबर'
                : 'Official Emergency & Disaster Hotlines'}
            </h3>
            <p className="text-[11px] text-slate-500">
              {language === 'pa'
                ? 'ਕਿਸੇ ਵੀ ਖ਼ਤਰੇ ਦੀ ਸੂਰਤ ਵਿੱਚ ਤੁਰੰਤ ਕਾਲ ਕਰੋ'
                : language === 'hi'
                ? 'किसी भी आपात स्थिति में तत्काल संपर्क करें'
                : 'Direct touch-to-call links verified with Punjab Disaster Management'}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
        {helplines.map((line) => (
          <div
            key={line.number}
            className={`p-3 rounded-lg border flex flex-col justify-between transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg cursor-pointer ${
              line.isPrimary
                ? 'border-red-200 bg-red-50/40 text-slate-900 hover:border-red-300 hover:bg-red-50/80'
                : 'border-slate-200 bg-slate-50/60 text-slate-900 hover:bg-white hover:border-blue-300'
            }`}
          >
            <div>
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-700">
                  {line.tag}
                </span>
                <button
                  type="button"
                  onClick={() => handleCopy(line.number)}
                  className="text-[11px] text-slate-500 hover:text-slate-800 flex items-center gap-1"
                  title="Copy number"
                >
                  {copiedNumber === line.number ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-600" />
                      <span className="text-[10px] text-emerald-700 font-medium">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span className="text-[10px]">Copy</span>
                    </>
                  )}
                </button>
              </div>

              <div className="text-base font-bold font-mono text-slate-900 mt-1">
                {line.number}
              </div>
              <div className="text-xs font-semibold text-slate-800 line-clamp-1 mt-0.5">
                {line.title}
              </div>
              <div className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">
                {line.subtitle}
              </div>
            </div>

            <div className="mt-3 pt-2 border-t border-slate-200/60">
              <a
                href={`tel:${line.tel}`}
                className={`w-full py-1.5 px-3 rounded-md text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors ${
                  line.isPrimary
                    ? 'bg-red-600 hover:bg-red-700 text-white shadow-xs'
                    : 'bg-slate-900 hover:bg-slate-800 text-white shadow-xs'
                }`}
              >
                <Phone className="w-3 h-3" />
                <span>
                  {language === 'pa' ? 'ਹੁਣੇ ਕਾਲ ਕਰੋ' : language === 'hi' ? 'अभी कॉल करें' : 'Call Now'}
                </span>
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
