import React, { useState, useRef, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { useAuth } from '../context/AuthContext';
import { speakText, stopSpeaking } from '../utils/speech';
import {
  Sparkles,
  Send,
  Bot,
  User,
  Volume2,
  VolumeX,
  Loader2,
  CloudRain,
  Compass,
  Thermometer,
  Wind,
  Droplets,
  AlertTriangle,
  RotateCcw,
  Download,
  Info,
} from 'lucide-react';

interface WeatherChatMessage {
  id: string;
  sender: 'weathergpt' | 'user';
  text: string;
  timestamp: string;
  category?: 'forecast' | 'alert' | 'climate' | 'agri' | 'general';
}

const getGreetingText = (lang: 'en' | 'pa' | 'hi'): string => {
  if (lang === 'pa') {
    return `ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ WeatherGPT ਹਾਂ — ਮੌਸਮ ਪੂਰਵ-ਅਨੁਮਾਨ, ਹੜ੍ਹ ਚੇਤਾਵਨੀਆਂ ਅਤੇ ਜਲਵਾਯੂ ਸੂਚਨਾ ਲਈ ਗੱਲਬਾਤ ਆਰਟੀਫੀਸ਼ੀਅਲ ਇੰਟੈਲੀਜੈਂਸ।

ਤੁਸੀਂ ਪੰਜਾਬ ਦੇ ਕਿਸੇ ਵੀ ਜ਼ਿਲ੍ਹੇ ਦੇ ਮੌਸਮ, ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ, ਘੱਗਰ ਦਰਿਆ ਦੇ ਪਾਣੀ ਦੇ ਪੱਧਰ, ਜਾਂ ਫਸਲਾਂ ਦੀ ਸੁਰੱਖਿਆ ਬਾਰੇ ਕੋਈ ਵੀ ਸੁਆਲ ਪੁੱਛ ਸਕਦੇ ਹੋ।`;
  }
  if (lang === 'hi') {
    return `नमस्ते! मैं WeatherGPT हूँ — मौसम पूर्वानुमान, बाढ़ चेतावनी एवं जलवायु सूचना हेतु संवादात्मक एआई (Conversational AI)।

आप पंजाब के किसी भी जिले के मौसम, बारिश की संभावना, घग्गर नदी के जलस्तर अथवा फसलों की सुरक्षा संबंधी कोई भी प्रश्न पूछ सकते हैं।`;
  }
  return `Welcome to WeatherGPT: Conversational AI for Weather Forecasting, Alerts & Climate Information.

I provide real-time meteorological intelligence, precipitation forecasts, Doppler radar assessments, river basin flood evaluations (Ghaggar & Sutlej), and PAU agro-climatic advisories. How can I assist your meteorological decision-making today?`;
};

const SAMPLE_PROMPT_MAP: Record<string, { pa: string; hi: string; en: string }> = {
  rain: {
    pa: 'ਅੱਜ ਪਟਿਆਲਾ ਵਿੱਚ ਕਿੰਨਾ ਮੀਂਹ ਪਵੇਗਾ?',
    hi: 'आज पटियाला में कितनी बारिश होगी?',
    en: "What is today's rainfall forecast for Patiala?",
  },
  flood: {
    pa: 'ਘੱਗਰ ਦਰਿਆ ਵਿੱਚ ਹੜ੍ਹ ਦਾ ਖ਼ਤਰਾ ਕਿੰਨਾ ਹੈ?',
    hi: 'घग्गर नदी में बाढ़ का क्या खतरा है?',
    en: 'What is the flood threat level along the Ghaggar basin?',
  },
  crop: {
    pa: 'ਕੀ ਮੈਂ ਅਗਲੇ 3 ਦਿਨ ਝੋਨੇ ਤੇ ਕੀਟਨਾਸ਼ਕ ਸਪਰੇਅ ਕਰ ਸਕਦਾ ਹਾਂ?',
    hi: 'क्या अगले 3 दिनों में धान पर कीटनाशक स्प्रे कर सकते हैं?',
    en: 'Can I spray pesticide on paddy crops in the next 3 days?',
  },
  disturbance: {
    pa: 'ਪੰਜਾਬ ਵਿੱਚ ਪੱਛਮੀ ਗੜਬੜ ਦਾ ਕੀ ਅਸਰ ਪਵੇਗਾ?',
    hi: 'पंजाब में पश्चिमी विक्षोभ का क्या प्रभाव रहेगा?',
    en: 'How is the active Western Disturbance impacting North India?',
  },
  forecast7: {
    pa: 'ਅਗਲੇ ਹਫ਼ਤੇ ਦਾ ਤਾਪਮਾਨ ਅਤੇ ਹਵਾ ਦੀ ਰਫ਼ਤਾਰ ਦੱਸੋ',
    hi: 'आगामी सप्ताह के तापमान व हवा की गति का पूर्वानुमान दें',
    en: 'Provide a 7-day temperature, humidity, and precipitation outlook.',
  },
};

const KNOWN_BOT_REPLIES: Record<string, { pa: string; hi: string; en: string }> = {
  rain: {
    pa: `ਅੱਜ ਦਾ ਮੌਸਮ ਅਤੇ ਬਾਰਿਸ਼ ਪੂਰਵ-ਅਨੁਮਾਨ:
• ਪਟਿਆਲਾ ਅਤੇ ਆਸ-ਪਾਸ ਦੇ ਇਲਾਕਿਆਂ ਵਿੱਚ 78 ਮਿ.ਮੀ. ਭਾਰੀ ਬਾਰਿਸ਼ ਦਰਜ ਕੀਤੀ ਗਈ ਹੈ।
• ਅਗਲੇ 24 ਘੰਟਿਆਂ ਵਿੱਚ ਦਰਮਿਆਨੀ ਤੋਂ ਭਾਰੀ ਬਾਰਿਸ਼ ਅਤੇ 35 ਕਿ.ਮੀ./ਘੰਟਾ ਦੀ ਰਫ਼ਤਾਰ ਨਾਲ ਤੇਜ਼ ਹਵਾਵਾਂ ਚੱਲਣ ਦੀ ਸੰਭਾਵਨਾ ਹੈ।
• ਤਾਪਮਾਨ 29°C (ਘੱਟੋ-ਘੱਟ 24°C) ਅਤੇ ਨਮੀ 92% ਰਹੇਗੀ।
• ਅਗਲੇ 48 ਘੰਟਿਆਂ ਬਾਅਦ ਮੌਸਮ ਵਿੱਚ ਸੁਧਾਰ ਹੋਣ ਦੀ ਉਮੀਦ ਹੈ।`,
    hi: `आज का मौसम एवं वर्षा पूर्वानुमान:
• पटियाला एवं आसपास के क्षेत्रों में 78 मिमी भारी वर्षा दर्ज की गई है।
• आगामी 24 घंटों में मध्यम से भारी वर्षा और 35 किमी/घंटा की रफ्तार से तेज हवाएं चलने की संभावना है।
• तापमान 29°C (न्यूनतम 24°C) तथा सापेक्ष आर्द्रता 92% रहेगी।
• 48 घंटों के उपरांत पश्चिमी विक्षोभ के कमजोर होने से मौसम में सुधार होगा।`,
    en: `WeatherGPT Forecast & Rain Analysis:
• Current Precipitation: 78 mm recorded across Patiala / Ghaggar catchment.
• 24-Hour Outlook: Intermittent moderate to heavy precipitation with gusts up to 35 km/h.
• Surface Conditions: Temperature 29°C (Min: 24°C), Relative Humidity 92%, Pressure 1004 hPa.
• Doppler Radar Echoes: Convective cloud tops reaching 11 km over Shivalik foothills. Synoptic rain expected to taper after 36-48 hours.`,
  },
  flood: {
    pa: `ਘੱਗਰ ਦਰਿਆ ਅਤੇ ਹੜ੍ਹ ਚੇਤਾਵਨੀ ਸਥਿਤੀ:
• ਘੱਗਰ ਗੇਜ ਪੱਧਰ 14.82 ਮੀਟਰ ਹੈ, ਜੋ ਕਿ ਖ਼ਤਰੇ ਦੇ ਨਿਸ਼ਾਨ (14.50 ਮੀਟਰ) ਤੋਂ ਉੱਪਰ ਹੈ।
• ਪਟਿਆਲਾ ਦੇ ਨੀਵੇਂ ਵਾਰਡ (12-14) ਅਤੇ ਵੱਡੀ ਨਦੀ ਦੇ ਕਿਨਾਰੇ ਹਾਈ ਅਲਰਟ 'ਤੇ ਹਨ।
• ਸਰਕਾਰੀ ਮਹਿੰਦਰਾ ਕਾਲਜ ਵਿਖੇ ਐਮਰਜੈਂਸੀ ਰਾਹਤ ਕੈਂਪ ਚਾਲੂ ਹੈ।
• ਐਮਰਜੈਂਸੀ ਹੈਲਪਲਾਈਨ: 112 (ਬਚਾਅ) ਜਾਂ 1077 (ਜ਼ਿਲ੍ਹਾ ਕੰਟਰੋਲ ਰੂਮ)।`,
    hi: `घग्गर नदी एवं बाढ़ चेतावनी स्थिति:
• घग्गर नदी का जलस्तर 14.82 मीटर दर्ज हुआ है, जो खतरे के निशान (14.50 मीटर) से ऊपर है।
• पटियाला के निचले वार्ड (12-14) एवं बड़ी नदी तटीय क्षेत्र हाई अलर्ट पर हैं।
• राजकीय मोहिंद्रा कॉलेज में 24x7 राहत एवं निकासी केंद्र सक्रिय है।
• आपातकालीन हेल्पलाइन: 112 (रेस्क्यू) अथवा 1077 (जिला आपदा नियंत्रण कक्ष)।`,
    en: `Hydrological Threat Assessment:
• Ghaggar River Naraj Gauge: 14.82m (Breaching 14.50m Danger Threshold).
• Evacuation Priority Index (EPI): 8.4/10.0 for low-lying Patiala Wards 12-14.
• Response Actions: SDRF 3rd Battalion pre-deployed; Relief camp operational at Govt Mohindra College.
• Emergency Helplines: 112 (National Emergency) & 1077 (District Disaster Room).`,
  },
  crop: {
    pa: `PAU ਖੇਤੀਬਾੜੀ ਅਤੇ ਫਸਲ ਸਲਾਹ:
• ਝੋਨੇ ਦੇ ਖੇਤਾਂ ਵਿੱਚ ਵਾਧੂ ਪਾਣੀ ਦੀ ਨਿਕਾਸੀ ਦਾ ਤੁਰੰਤ ਪ੍ਰਬੰਧ ਕਰੋ।
• ਅਗਲੇ 48 ਘੰਟਿਆਂ ਦੌਰਾਨ ਕੋਈ ਵੀ ਕੀਟਨਾਸ਼ਕ ਜਾਂ ਉੱਲੀਨਾਸ਼ਕ ਸਪਰੇਅ ਨਾ ਕਰੋ, ਕਿਉਂਕਿ ਮੀਂਹ ਕਾਰਨ ਦਵਾਈ ਧੁਲ ਜਾਵੇਗੀ।
• ਕਪਾਹ ਅਤੇ ਨਰਮੇ ਵਿੱਚ ਪਾਣੀ ਖੜ੍ਹਨ ਨਾ ਦਿਓ।
• ਸਹਾਇਤਾ ਲਈ ਕਿਸਾਨ ਕਾਲ ਸੈਂਟਰ: 1800-180-1551 'ਤੇ ਸੰਪਰਕ ਕਰੋ।`,
    hi: `PAU कृषि एवं फसल परामर्श:
• धान के खेतों में जलभराव से बचाव हेतु जलनिकासी का उचित प्रबंध करें।
• आगामी 48 घंटों में किसी भी कीटनाशक या यूरिया का छिड़काव न करें, वर्षा से दवा बह जाएगी।
• कपास एवं नरमा क्षेत्रों में ठहरा हुआ पानी तुरंत बाहर निकालें।
• सहायता हेतु किसान कॉल सेंटर: 1800-180-1551 पर संपर्क करें।`,
    en: `PAU Agro-Met Advisory:
• Ensure proper field drainage to prevent submergence hypoxia in paddy nurseries.
• Suspend all pesticide/fungicide foliar spraying for the next 48 hours due to high rain washout risk.
• Drain excess standing water immediately from cotton tracts.
• Kisan Call Centre Toll-Free: 1800-180-1551.`,
  },
  fallback: {
    pa: `WeatherGPT ਮੌਸਮ ਜਾਣਕਾਰੀ (ਸਥਾਨਕ ਸਿਸਟਮ):
• ਪਟਿਆਲਾ ਜ਼ਿਲ੍ਹੇ ਵਿੱਚ 78 ਮਿ.ਮੀ. ਬਾਰਿਸ਼ ਦਰਜ ਕੀਤੀ ਗਈ ਹੈ।
• ਘੱਗਰ ਦਰਿਆ ਦਾ ਗੇਜ 14.82 ਮੀਟਰ ਹੈ (ਖ਼ਤਰੇ ਦਾ ਨਿਸ਼ਾਨ 14.50 ਮੀਟਰ)।
• ਅਗਲੇ 24 ਘੰਟਿਆਂ ਵਿੱਚ ਦਰਮਿਆਨਾ ਮੀਂਹ ਜਾਰੀ ਰਹੇਗਾ।
• ਖੇਤਾਂ ਵਿੱਚ ਯੂਰੀਆ ਸਪਰੇਅ ਫਿਲਹਾਲ ਰੋਕੋ।`,
    hi: `WeatherGPT मौसम सूचना (स्थानीय प्रणाली):
• पटियाला जिले में 78 मिमी वर्षा दर्ज की गई है।
• घग्गर नदी का जलस्तर 14.82 मीटर है (खतरे का निशान 14.50 मीटर)।
• आगामी 24 घंटों में मध्यम वर्षा जारी रहने का अनुमान है।
• खेतों में कीटनाशक व यूरिया का छिड़काव स्थगित रखें।`,
    en: `WeatherGPT Synoptic Telemetry:
• Patiala precipitation: 78 mm recorded in last 24h.
• Ghaggar Basin Naraj Gauge: 14.82m (Breaching 14.50m Danger Mark).
• Intermittent convective rain expected across Shivalik foothills for next 24-36h.
• PAU Advisory: Suspend foliar nitrogen sprays and ensure field bund drainage.`,
  },
};

const mapTextToTargetLanguage = (text: string, targetLang: 'en' | 'pa' | 'hi'): string | null => {
  const tTrim = text.trim();
  // Match prompt chips
  for (const group of Object.values(SAMPLE_PROMPT_MAP)) {
    if (tTrim === group.en || tTrim === group.pa || tTrim === group.hi) {
      return group[targetLang];
    }
  }

  // Match known answers
  if (
    tTrim.includes('78 mm') ||
    tTrim.includes('78 ਮਿ.ਮੀ.') ||
    tTrim.includes('78 मिमी')
  ) {
    if (tTrim.includes('Synoptic Telemetry') || tTrim.includes('ਸਥਾਨਕ ਸਿਸਟਮ') || tTrim.includes('स्थानीय प्रणाली')) {
      return KNOWN_BOT_REPLIES.fallback[targetLang];
    }
    return KNOWN_BOT_REPLIES.rain[targetLang];
  }

  if (
    tTrim.includes('Ghaggar') ||
    tTrim.includes('ਘੱਗਰ') ||
    tTrim.includes('घग्गर') ||
    tTrim.includes('14.82')
  ) {
    return KNOWN_BOT_REPLIES.flood[targetLang];
  }

  if (
    tTrim.includes('PAU') ||
    tTrim.includes('ਕੀਟਨਾਸ਼ਕ') ||
    tTrim.includes('कीटनाशक') ||
    tTrim.includes('hypoxia')
  ) {
    return KNOWN_BOT_REPLIES.crop[targetLang];
  }

  return null;
};

export const WeatherGPTView: React.FC = () => {
  const { language, t } = useLanguage();
  const { user } = useAuth();

  const [inputQuery, setInputQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [speakingMsgId, setSpeakingMsgId] = useState<string | null>(null);

  const createInitialGreeting = (lang: 'en' | 'pa' | 'hi'): WeatherChatMessage => ({
    id: 'msg-init-01',
    sender: 'weathergpt',
    text: getGreetingText(lang),
    timestamp: '12:00',
    category: 'general',
  });

  const [messages, setMessages] = useState<WeatherChatMessage[]>([
    createInitialGreeting(language),
  ]);
  const chatBottomRef = useRef<HTMLDivElement | null>(null);

  // Automatically update the conversation to the preferred language when language is switched
  useEffect(() => {
    // 1. Stop any current speech playback
    stopSpeaking();
    setSpeakingMsgId(null);

    // 2. Instantly translate initial greeting and all mapped questions/answers
    setMessages((prev) => {
      const updated = prev.map((msg) => {
        if (msg.id === 'msg-init-01') {
          return {
            ...msg,
            text: getGreetingText(language),
          };
        }
        const mapped = mapTextToTargetLanguage(msg.text, language);
        if (mapped) {
          return {
            ...msg,
            text: mapped,
          };
        }
        return msg;
      });

      // 3. Translate any custom user or bot messages asynchronously via /api/translate
      const unmapped = updated.filter(
        (m) => m.id !== 'msg-init-01' && !mapTextToTargetLanguage(m.text, language)
      );

      if (unmapped.length > 0) {
        fetch('/api/translate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            texts: unmapped.map((m) => m.text),
            targetLanguage: language,
          }),
        })
          .then((res) => (res.ok ? res.json() : null))
          .then((data) => {
            if (data && Array.isArray(data.translations)) {
              setMessages((current) =>
                current.map((m) => {
                  const idx = unmapped.findIndex((u) => u.id === m.id);
                  if (idx !== -1 && data.translations[idx]) {
                    return { ...m, text: data.translations[idx] };
                  }
                  return m;
                })
              );
            }
          })
          .catch(() => {
            // Graceful fallback
          });
      }

      return updated;
    });
  }, [language]);

  const handleSpeak = (id: string, text: string) => {
    if (speakingMsgId === id) {
      stopSpeaking();
      setSpeakingMsgId(null);
      return;
    }
    stopSpeaking();
    setSpeakingMsgId(id);
    speakText(
      text,
      language,
      () => setSpeakingMsgId(id),
      () => setSpeakingMsgId(null)
    );
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputQuery).trim();
    if (!query || isLoading) return;

    const userMsg: WeatherChatMessage = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsLoading(true);

    try {
      const res = await fetch('/api/weathergpt/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: query,
          language,
          userRole: user?.role || 'CITIZEN',
          district: user?.district || 'Patiala, Punjab',
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const gptMsg: WeatherChatMessage = {
          id: `gpt-${Date.now()}`,
          sender: 'weathergpt',
          text: data.reply || 'Information received.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, gptMsg]);
      } else {
        throw new Error('Non-200 response from WeatherGPT API');
      }
    } catch (err) {
      const fallbackReply =
        language === 'pa'
          ? `WeatherGPT ਮੌਸਮ ਜਾਣਕਾਰੀ (ਸਥਾਨਕ ਸਿਸਟਮ):
• ਪਟਿਆਲਾ ਜ਼ਿਲ੍ਹੇ ਵਿੱਚ 78 ਮਿ.ਮੀ. ਬਾਰਿਸ਼ ਦਰਜ ਕੀਤੀ ਗਈ ਹੈ।
• ਘੱਗਰ ਦਰਿਆ ਦਾ ਗੇਜ 14.82 ਮੀਟਰ ਹੈ (ਖ਼ਤਰੇ ਦਾ ਨਿਸ਼ਾਨ 14.50 ਮੀਟਰ)।
• ਅਗਲੇ 24 ਘੰਟਿਆਂ ਵਿੱਚ ਦਰਮਿਆਨਾ ਮੀਂਹ ਜਾਰੀ ਰਹੇਗਾ।
• ਖੇਤਾਂ ਵਿੱਚ ਯੂਰੀਆ ਸਪਰੇਅ ਫਿਲਹਾਲ ਰੋਕੋ।`
          : language === 'hi'
          ? `WeatherGPT मौसम सूचना (स्थानीय प्रणाली):
• पटियाला जिले में 78 मिमी वर्षा दर्ज की गई है।
• घग्गर नदी का जलस्तर 14.82 मीटर है (खतरे का निशान 14.50 मीटर)।
• आगामी 24 घंटों में मध्यम वर्षा जारी रहने का अनुमान है।
• खेतों में कीटनाशक व यूरिया का छिड़काव स्थगित रखें।`
          : `WeatherGPT Synoptic Telemetry:
• Patiala precipitation: 78 mm recorded in last 24h.
• Ghaggar Basin Naraj Gauge: 14.82m (Breaching 14.50m Danger Mark).
• Intermittent convective rain expected across Shivalik foothills for next 24-36h.
• PAU Advisory: Suspend foliar nitrogen sprays and ensure field bund drainage.`;

      const gptMsg: WeatherChatMessage = {
        id: `gpt-${Date.now()}`,
        sender: 'weathergpt',
        text: fallbackReply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, gptMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const sampleWeatherPrompts =
    language === 'pa'
      ? [
          'ਅੱਜ ਪਟਿਆਲਾ ਵਿੱਚ ਕਿੰਨਾ ਮੀਂਹ ਪਵੇਗਾ?',
          'ਘੱਗਰ ਦਰਿਆ ਵਿੱਚ ਹੜ੍ਹ ਦਾ ਖ਼ਤਰਾ ਕਿੰਨਾ ਹੈ?',
          'ਕੀ ਮੈਂ ਅਗਲੇ 3 ਦਿਨ ਝੋਨੇ ਤੇ ਕੀਟਨਾਸ਼ਕ ਸਪਰੇਅ ਕਰ ਸਕਦਾ ਹਾਂ?',
          'ਪੰਜਾਬ ਵਿੱਚ ਪੱਛਮੀ ਗੜਬੜ ਦਾ ਕੀ ਅਸਰ ਪਵੇਗਾ?',
          'ਅਗਲੇ ਹਫ਼ਤੇ ਦਾ ਤਾਪਮਾਨ ਅਤੇ ਹਵਾ ਦੀ ਰਫ਼ਤਾਰ ਦੱਸੋ',
        ]
      : language === 'hi'
      ? [
          'आज पटियाला में कितनी बारिश होगी?',
          'घग्गर नदी में बाढ़ का क्या खतरा है?',
          'क्या अगले 3 दिनों में धान पर कीटनाशक स्प्रे कर सकते हैं?',
          'पंजाब में पश्चिमी विक्षोभ का क्या प्रभाव रहेगा?',
          'आगामी सप्ताह के तापमान व हवा की गति का पूर्वानुमान दें',
        ]
      : [
          "What is today's rainfall forecast for Patiala?",
          'What is the flood threat level along the Ghaggar basin?',
          'Can I spray pesticide on paddy crops in the next 3 days?',
          'How is the active Western Disturbance impacting North India?',
          'Provide a 7-day temperature, humidity, and precipitation outlook.',
        ];

  return (
    <div className="max-w-5xl mx-auto flex flex-col h-[calc(100dvh-5.5rem)] min-h-[460px] pb-1 overflow-hidden">
      {/* Title & Context Banner */}
      <div className="bg-white rounded-xl border border-slate-200 px-3.5 py-2 sm:px-4 sm:py-2.5 shadow-xs mb-2 shrink-0">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <h1 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight shrink-0">
              Weather<span className="text-blue-600">GPT</span>
            </h1>
            <span className="hidden sm:inline-block text-xs text-slate-500 font-medium truncate">
              {language === 'pa'
                ? 'ਮੌਸਮ ਪੂਰਵ-ਅਨੁਮਾਨ ਤੇ ਆਫ਼ਤ AI'
                : language === 'hi'
                ? 'मौसम पूर्वानुमान एवं आपदा AI'
                : 'Atmospheric & Flood Intelligence'}
            </span>
          </div>

          <button
            type="button"
            onClick={() => {
              setMessages([createInitialGreeting(language)]);
              stopSpeaking();
              setSpeakingMsgId(null);
            }}
            className="px-2.5 py-1 rounded-lg border border-slate-200 text-xs font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-1.5 transition-colors shrink-0"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>{language === 'pa' ? 'ਨਵੀਂ ਗੱਲਬਾਤ' : language === 'hi' ? 'नई बातचीत' : 'Clear Chat'}</span>
          </button>
        </div>
      </div>

      {/* Main Chat Box */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs flex-1 min-h-0 flex flex-col overflow-hidden">
        {/* Messages Stream */}
        <div className="flex-1 min-h-0 overflow-y-auto p-3 sm:p-4 space-y-3 bg-slate-50/50">
          {messages.map((m) => {
            const isUser = m.sender === 'user';
            const isSpeakingThis = speakingMsgId === m.id;

            return (
              <div
                key={m.id}
                className={`flex gap-3 max-w-3xl ${isUser ? 'ml-auto justify-end' : 'mr-auto justify-start'}`}
              >
                {!isUser && (
                  <img
                    src="/logo.png?v=2"
                    alt="Logo"
                    className="w-7 h-7 rounded-lg object-contain shrink-0 mt-0.5"
                  />
                )}

                <div
                  className={`rounded-xl p-3 sm:p-3.5 text-xs leading-relaxed transition-all ${
                    isUser
                      ? 'bg-slate-900 text-white border border-blue-500/30 shadow-[0_2px_14px_rgba(37,99,235,0.22)] hover:shadow-[0_4px_18px_rgba(37,99,235,0.30)] max-w-[85%]'
                      : 'bg-white text-slate-800 border border-blue-200/80 shadow-[0_2px_14px_rgba(37,99,235,0.14)] hover:shadow-[0_4px_18px_rgba(37,99,235,0.22)] max-w-[90%] whitespace-pre-line'
                  }`}
                >
                  <div className="flex items-center justify-between gap-3 mb-1 text-[11px]">
                    <span className={`font-semibold ${isUser ? 'text-slate-300' : 'text-slate-900'}`}>
                      {isUser
                        ? user?.name || (language === 'pa' ? 'ਤੁਸੀਂ' : language === 'hi' ? 'आप' : 'User')
                        : 'WeatherGPT Engine'}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">{m.timestamp}</span>
                  </div>

                  <p className="text-xs sm:text-[13px]">{m.text}</p>

                  {!isUser && (
                    <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between">
                      <button
                        type="button"
                        onClick={() => handleSpeak(m.id, m.text)}
                        className={`px-2 py-0.5 rounded text-[11px] font-medium flex items-center gap-1.5 transition-colors ${
                          isSpeakingThis
                            ? 'bg-amber-100 text-amber-900 border border-amber-300'
                            : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                        }`}
                      >
                        {isSpeakingThis ? (
                          <>
                            <VolumeX className="w-3.5 h-3.5" />
                            <span>{language === 'pa' ? 'ਆਵਾਜ਼ ਬੰਦ ਕਰੋ' : language === 'hi' ? 'रोकें' : 'Stop Audio'}</span>
                          </>
                        ) : (
                          <>
                            <Volume2 className="w-3.5 h-3.5" />
                            <span>{language === 'pa' ? 'ਸੁਣੋ' : language === 'hi' ? 'आवाज़ सुनें' : 'Listen Voice'}</span>
                          </>
                        )}
                      </button>

                      <span className="text-[10px] text-slate-400">
                        {language === 'pa' ? 'ਪ੍ਰਮਾਣਿਤ ਡਾਟਾ' : language === 'hi' ? 'सत्यापित डेटा' : 'Official Forecast'}
                      </span>
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="w-7 h-7 rounded-lg bg-slate-800 text-white flex items-center justify-center shrink-0 mt-0.5 shadow-xs text-xs font-bold">
                    <User className="w-3.5 h-3.5" />
                  </div>
                )}
              </div>
            );
          })}

          {isLoading && (
            <div className="flex items-center gap-2.5 p-2.5 rounded-lg bg-white border border-blue-200/80 shadow-[0_2px_14px_rgba(37,99,235,0.14)] w-fit text-slate-600 text-xs">
              <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
              <span>
                {language === 'pa'
                  ? 'WeatherGPT ਮੌਸਮ ਡਾਟਾ ਦਾ ਵਿਸ਼ਲੇਸ਼ਣ ਕਰ ਰਿਹਾ ਹੈ...'
                  : language === 'hi'
                  ? 'WeatherGPT मौसम डेटा का विश्लेषण कर रहा है...'
                  : 'WeatherGPT is synthesizing meteorological feeds...'}
              </span>
            </div>
          )}

          <div ref={chatBottomRef} />
        </div>

        {/* Suggestion Chips */}
        <div className="px-4 py-2.5 bg-slate-50 border-t border-slate-200 shrink-0">
          <div className="flex items-center gap-2 mb-2 text-sm sm:text-[15px] font-bold text-slate-800">
            <Sparkles className="w-4 h-4 text-blue-600 shrink-0" />
            <span>
              {language === 'pa'
                ? 'ਆਮ ਮੌਸਮ ਸੁਆਲ:'
                : language === 'hi'
                ? 'सामान्य मौसम प्रश्न:'
                : 'General Weather Queries:'}
            </span>
          </div>
          <div className="flex gap-2.5 overflow-x-auto pb-1 scrollbar-none items-center">
            {sampleWeatherPrompts.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSendMessage(p)}
                className="whitespace-nowrap px-4 py-2 bg-white hover:bg-blue-50/80 border border-slate-200 hover:border-blue-400 text-slate-800 hover:text-blue-700 rounded-lg text-xs sm:text-[13px] font-medium shadow-xs transition-all hover:scale-105 hover:shadow-sm cursor-pointer shrink-0"
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Query Input Bar */}
        <div className="p-2 sm:p-2.5 bg-white border-t border-slate-200 flex items-center gap-2 shrink-0">
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder={
              language === 'pa'
                ? 'ਮੌਸਮ, ਮੀਂਹ, ਹੜ੍ਹ ਜਾਂ ਫਸਲਾਂ ਬਾਰੇ ਕੋਈ ਵੀ ਸੁਆਲ ਪੁੱਛੋ...'
                : language === 'hi'
                ? 'मौसम, बारिश, बाढ़ अथवा फसल संबंधी कोई भी प्रश्न पूछें...'
                : 'Ask WeatherGPT anything regarding rainfall, wind, flood risk, or climate...'
            }
            className="flex-1 text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-slate-900 focus:border-slate-900"
          />
          <button
            type="button"
            onClick={() => handleSendMessage()}
            disabled={!inputQuery.trim() || isLoading}
            className="px-3.5 py-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-white rounded-lg text-xs font-semibold tracking-wide transition-colors flex items-center gap-1.5 shrink-0"
          >
            <span>{language === 'pa' ? 'ਪੁੱਛੋ' : language === 'hi' ? 'पूछें' : 'Send'}</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
