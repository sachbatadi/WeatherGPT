import React, { useState, useRef, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { useAuth } from '../context/AuthContext';
import { speakText, stopSpeaking } from '../utils/speech';
import { X, Send, Bot, User, Loader2, Sparkles, Volume2, VolumeX, RotateCcw } from 'lucide-react';
import { askGeminiWeatherGPT } from '../services/geminiService';

interface AgentCopilotDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

interface Message {
  id: string;
  sender: 'weathergpt' | 'user';
  text: string;
  time: string;
}

export const AgentCopilotDrawer: React.FC<AgentCopilotDrawerProps> = ({ isOpen, onClose }) => {
  const { language, t } = useLanguage();
  const { user } = useAuth();
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [speakingMsgId, setSpeakingMsgId] = useState<string | null>(null);

  const getGreeting = () => ({
    id: 'msg-init',
    sender: 'weathergpt' as const,
    text:
      language === 'pa'
        ? `ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ WeatherGPT ਹਾਂ — ਮੌਸਮ ਪੂਰਵ-ਅਨੁਮਾਨ, ਹੜ੍ਹ ਚੇਤਾਵਨੀਆਂ ਅਤੇ ਜਲਵਾਯੂ ਸੂਚਨਾ ਲਈ ਗੱਲਬਾਤ ਆਰਟੀਫੀਸ਼ੀਅਲ ਇੰਟੈਲੀਜੈਂਸ।

ਤੁਸੀਂ ਪੰਜਾਬ ਦੇ ਕਿਸੇ ਵੀ ਜ਼ਿਲ੍ਹੇ ਦੇ ਮੌਸਮ, ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ, ਘੱਗਰ ਦਰਿਆ ਦੇ ਪਾਣੀ ਦੇ ਪੱਧਰ, ਜਾਂ ਫਸਲਾਂ ਦੀ ਸੁਰੱਖਿਆ ਬਾਰੇ ਕੋਈ ਵੀ ਸੁਆਲ ਪੁੱਛ ਸਕਦੇ ਹੋ।`
        : language === 'hi'
        ? `नमस्ते! मैं WeatherGPT हूँ — मौसम पूर्वानुमान, चेतावनी एवं जलवायु सूचना हेतु संवादात्मक एआई।

आप पंजाब के किसी भी जिले के मौसम, बारिश की संभावना, घग्गर नदी के जलस्तर अथवा फसलों की सुरक्षा संबंधी कोई भी प्रश्न पूछ सकते हैं।`
        : `Welcome to WeatherGPT: Conversational AI for Weather Forecasting, Alerts & Climate Information. Ingesting live hydrological telemetry from Ghaggar basin and PAU Agro-Met station. How may I assist your meteorological operations?`,
    time: '12:00',
  });

  const [messages, setMessages] = useState<Message[]>([getGreeting()]);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setMessages((prev) =>
      prev.map((m) => {
        if (m.id === 'msg-init') {
          return getGreeting();
        }
        return m;
      })
    );
  }, [language]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  if (!isOpen) return null;

  const quickPrompts =
    language === 'pa'
      ? [
          'ਘੱਗਰ ਦਰਿਆ ਵਿੱਚ ਪਾਣੀ ਦਾ ਮੌਜੂਦਾ ਪੱਧਰ ਕੀ ਹੈ?',
          'ਵਾਰਡ 12-14 ਲਈ ਨਿਕਾਸੀ ਹਦਾਇਤਾਂ',
          'ਝੋਨੇ ਦੀ ਫਸਲ ਵਿੱਚ ਪਾਣੀ ਖੜ੍ਹਨ ਤੋਂ ਬਚਾਓ',
          'ਅੱਜ ਕਿੰਨਾ ਮੀਂਹ ਪਵੇਗਾ?',
        ]
      : language === 'hi'
      ? [
          'घग्गर नदी में वर्तमान जलस्तर क्या है?',
          'वार्ड 12-14 के लिए निकासी निर्देश',
          'धान की फसल में जलभराव से बचाव',
          'आज कितनी बारिश होगी?',
        ]
      : [
          'Current Ghaggar River gauge level at Naraj',
          'Ward 12-14 evacuation directives & shelter',
          'Paddy nursery root hypoxia mitigation',
          "Today's rainfall and storm outlook",
        ];

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

  const handleSend = async (queryText?: string) => {
    const query = (queryText || input).trim();
    if (!query || loading) return;

    const userMsg: Message = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: query,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const { reply } = await askGeminiWeatherGPT(
        query,
        language,
        user?.district || 'Patiala, Punjab',
        user?.role || 'OFFICER'
      );
      const gptMsg: Message = {
        id: `gpt-${Date.now()}`,
        sender: 'weathergpt',
        text: reply,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, gptMsg]);
    } catch (err) {
      const gptMsg: Message = {
        id: `gpt-${Date.now()}`,
        sender: 'weathergpt',
        text:
          language === 'pa'
            ? 'WeatherGPT ਸਿਸਟਮ ਇਸ ਵੇਲੇ ਉਪਲਬਧ ਨਹੀਂ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।'
            : language === 'hi'
            ? 'WeatherGPT प्रणाली वर्तमान में अनुपलब्ध है। कृपया पुनः प्रयास करें।'
            : 'WeatherGPT system could not process the query. Please verify your connection.',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, gptMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/50 backdrop-blur-xs flex justify-end">
      <div className="w-full max-w-lg bg-white h-full shadow-2xl flex flex-col border-l border-slate-200 animate-in slide-in-from-right duration-200">
        {/* Drawer Header */}
        <div className="px-5 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <img
              src="/logo.png?v=2"
              alt="Logo"
              className="w-7 h-7 rounded-lg object-contain"
            />
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-900">WeatherGPT</h2>
                <span className="px-1.5 py-0.2 bg-blue-100 text-blue-800 text-[10px] font-semibold rounded">
                  AI Assistant
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                {language === 'pa'
                  ? 'ਮੌਸਮ ਪੂਰਵ-ਅਨੁਮਾਨ, ਹੜ੍ਹ ਚੇਤਾਵਨੀ ਤੇ ਜਲਵਾਯੂ ਏ.ਆਈ.'
                  : language === 'hi'
                  ? 'मौसम पूर्वानुमान, चेतावनी एवं जलवायु संवादात्मक एआई'
                  : 'Conversational Weather & Flood Decision AI'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => {
                setMessages([getGreeting()]);
                stopSpeaking();
                setSpeakingMsgId(null);
              }}
              className="p-1.5 text-slate-400 hover:text-slate-700 rounded-md hover:bg-slate-200 transition-colors"
              title="Reset conversation"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => {
                stopSpeaking();
                onClose();
              }}
              className="p-1.5 text-slate-400 hover:text-slate-700 rounded-md hover:bg-slate-200 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Message Feed */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-slate-50/50">
          {messages.map((m) => {
            const isUser = m.sender === 'user';
            const isSpeakingThis = speakingMsgId === m.id;

            return (
              <div
                key={m.id}
                className={`flex gap-2.5 ${isUser ? 'ml-auto justify-end' : 'mr-auto justify-start'}`}
              >
                {!isUser && (
                  <div className="w-6 h-6 rounded bg-blue-600 text-white flex items-center justify-center shrink-0 mt-0.5 text-[10px] font-bold">
                    W
                  </div>
                )}

                <div
                  className={`rounded-lg p-3 text-xs leading-relaxed max-w-[85%] ${
                    isUser
                      ? 'bg-slate-900 text-white'
                      : 'bg-white text-slate-800 border border-slate-200 shadow-xs whitespace-pre-line'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-1 text-[10px]">
                    <span className={`font-semibold ${isUser ? 'text-slate-300' : 'text-slate-900'}`}>
                      {isUser ? user?.name || 'User' : 'WeatherGPT'}
                    </span>
                    <span className="text-slate-400 font-mono">{m.time}</span>
                  </div>

                  <p className="text-xs">{m.text}</p>

                  {!isUser && (
                    <div className="mt-2 pt-1.5 border-t border-slate-100 flex items-center justify-between">
                      <button
                        type="button"
                        onClick={() => handleSpeak(m.id, m.text)}
                        className={`px-2 py-0.5 rounded text-[10px] font-medium flex items-center gap-1 transition-colors ${
                          isSpeakingThis
                            ? 'bg-amber-100 text-amber-900 border border-amber-300'
                            : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                        }`}
                      >
                        {isSpeakingThis ? (
                          <>
                            <VolumeX className="w-3 h-3" />
                            <span>Stop</span>
                          </>
                        ) : (
                          <>
                            <Volume2 className="w-3 h-3" />
                            <span>{language === 'pa' ? 'ਸੁਣੋ' : language === 'hi' ? 'सुनें' : 'Listen'}</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="w-6 h-6 rounded bg-slate-800 text-white flex items-center justify-center shrink-0 mt-0.5 text-[10px] font-bold">
                    <User className="w-3.5 h-3.5" />
                  </div>
                )}
              </div>
            );
          })}

          {loading && (
            <div className="flex items-center gap-2 p-2.5 rounded-lg bg-white border border-slate-200 w-fit text-slate-600 text-xs">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-600" />
              <span>Analyzing meteorological telemetry...</span>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Quick Prompts */}
        <div className="p-3 bg-white border-t border-slate-200">
          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
            {language === 'pa' ? 'ਸੁਝਾਏ ਗਏ ਸੁਆਲ:' : language === 'hi' ? 'सुझाए गए प्रश्न:' : 'Quick Questions:'}
          </div>
          <div className="flex flex-wrap gap-1.5">
            {quickPrompts.map((q, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleSend(q)}
                className="text-left text-[11px] px-2.5 py-1 bg-slate-100 hover:bg-slate-200 rounded text-slate-700 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Query Input */}
        <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={
              language === 'pa'
                ? 'WeatherGPT ਨੂੰ ਮੌਸਮ ਜਾਂ ਹੜ੍ਹ ਬਾਰੇ ਪੁੱਛੋ...'
                : language === 'hi'
                ? 'WeatherGPT से मौसम या बाढ़ संबंधी प्रश्न पूछें...'
                : 'Ask WeatherGPT anything regarding weather, flood, or crops...'
            }
            className="flex-1 text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-slate-900 focus:border-slate-900 bg-white"
          />
          <button
            type="button"
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            className="px-3.5 py-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-white rounded-lg text-xs font-semibold transition-colors flex items-center gap-1"
          >
            <span>{language === 'pa' ? 'ਭੇਜੋ' : language === 'hi' ? 'भेजें' : 'Send'}</span>
            <Send className="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  );
};
