import React, { useState, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { useAuth } from '../context/AuthContext';
import { Language, NavigationTab } from '../types';
import { speakText, stopSpeaking } from '../utils/speech';
import {
  MapPin,
  Clock,
  RefreshCw,
  ChevronDown,
  Globe,
  Volume2,
  VolumeX,
  SlidersHorizontal,
  Shield,
  User,
  MessageSquare,
  Activity,
  Home,
  Map,
  AlertTriangle,
  Sprout,
  LogIn,
  LogOut,
  Sun,
  Moon,
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

interface HeaderProps {
  activeTab: NavigationTab;
  onTabChange: (tab: NavigationTab) => void;
  onOpenCopilot: () => void;
  onRefresh: () => void;
  selectedLocation: string;
  onLocationChange: (loc: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  onOpenCopilot,
  onRefresh,
  selectedLocation,
  onLocationChange,
}) => {
  const { language, setLanguage, t, setIsLanguageModalOpen, isSimpleMode, setIsSimpleMode } =
    useLanguage();
  const { user, login, setIsLoginModalOpen } = useAuth();
  const { isDarkMode, toggleTheme } = useTheme();

  const isCitizen = user?.role === 'CITIZEN';

  const [timeString, setTimeString] = useState<string>('12:00:00 IST');
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isLangDropdownOpen, setIsLangDropdownOpen] = useState<boolean>(false);
  const [isLocDropdownOpen, setIsLocDropdownOpen] = useState<boolean>(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState<boolean>(false);
  const [isVoiceSpeaking, setIsVoiceSpeaking] = useState<boolean>(false);

  // Live IST Clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const options: Intl.DateTimeFormatOptions = {
        timeZone: 'Asia/Kolkata',
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      };
      const formatted = new Intl.DateTimeFormat('en-GB', options).format(now);
      setTimeString(`${formatted} IST`);
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleRefreshClick = () => {
    setIsRefreshing(true);
    onRefresh();
    setTimeout(() => setIsRefreshing(false), 800);
  };

  const handleToggleGlobalVoice = () => {
    if (isVoiceSpeaking) {
      stopSpeaking();
      setIsVoiceSpeaking(false);
      return;
    }

    const warningText =
      language === 'pa'
        ? 'ਜ਼ਰੂਰੀ ਸੂਚਨਾ: ਪਟਿਆਲਾ ਵਿੱਚ ਘੱਗਰ ਦਰਿਆ ਦਾ ਪਾਣੀ ਖ਼ਤਰੇ ਦੇ ਨਿਸ਼ਾਨ ਤੋਂ ਉੱਪਰ ਹੈ। ਨੀਵੇਂ ਇਲਾਕੇ ਖਾਲੀ ਕਰੋ ਅਤੇ ਉੱਚੀ ਥਾਂ ਜਾਓ। ਮਦਦ ਲਈ ਇੱਕ ਸੌ ਬਾਰਾਂ ਤੇ ਫ਼ੋਨ ਕਰੋ।'
        : language === 'hi'
        ? 'महत्वपूर्ण सूचना: पटियाला में घग्गर नदी का पानी खतरे के निशान से ऊपर है। निचले इलाके खाली करें और ऊंचे स्थान पर जाएं। सहायता हेतु एक सौ बारह पर फोन करें।'
        : 'Emergency Warning: Ghaggar river water is above danger mark in Patiala. Evacuate low areas to high ground. Call 112 for rescue.';

    setIsVoiceSpeaking(true);
    speakText(
      warningText,
      language,
      () => setIsVoiceSpeaking(true),
      () => setIsVoiceSpeaking(false)
    );
  };

  const locations = [
    'Patiala, Punjab',
    'Jalandhar (Doaba)',
    'Ludhiana Central',
    'Hoshiarpur Foothills',
    'Kapurthala Riverine',
    'Bathinda Cotton Belt',
  ];

  const languageLabels: Record<Language, { label: string; code: string }> = {
    pa: { label: 'ਪੰਜਾਬੀ', code: 'PA' },
    hi: { label: 'हिन्दी', code: 'HI' },
    en: { label: 'English', code: 'EN' },
  };

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-slate-200">
      <div className="max-w-[1500px] mx-auto px-3 sm:px-6 h-16 flex items-center justify-between gap-2 sm:gap-3 min-w-0">
        {/* Left Side: Brand Logo & Main Nav Tabs */}
        <div className="flex items-center gap-4 lg:gap-6">
          <div
            onClick={() => onTabChange('weathergpt')}
            className="flex items-center gap-2.5 cursor-pointer select-none"
            title="WeatherGPT Home"
          >
            <img
              src="/logo.png?v=2"
              alt="Logo"
              className="w-9 h-9 rounded-lg object-contain"
            />
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-base font-bold tracking-tight text-slate-900 font-sans">
                  Weather<span className="text-blue-600">GPT</span>
                </span>
              </div>
              <p className="hidden sm:block text-[10px] text-slate-500 font-medium -mt-0.5">
                {language === 'pa'
                  ? 'ਮੌਸਮ ਪੂਰਵ-ਅਨੁਮਾਨ ਤੇ ਆਫ਼ਤ ਸੂਚਨਾ AI'
                  : language === 'hi'
                  ? 'मौसम पूर्वानुमान एवं आपदा सूचना AI'
                  : 'Conversational Weather & Alert AI'}
              </p>
            </div>
          </div>

          {/* Desktop Navigation Tabs */}
          <nav className="hidden md:flex items-center gap-1 text-xs font-semibold">
            {isCitizen ? (
              <>
                {/* Citizen Navigation */}
                <button
                  id="tab-weathergpt-primary"
                  type="button"
                  onClick={() => onTabChange('weathergpt')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition-colors ${
                    activeTab === 'weathergpt'
                      ? 'bg-blue-600 text-white shadow-xs font-bold'
                      : 'text-blue-700 bg-blue-50/80 hover:bg-blue-100 border border-blue-200/70'
                  }`}
                >
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span>WEATHERGPT</span>
                </button>

                <button
                  id="tab-citizen-home"
                  type="button"
                  onClick={() => onTabChange('citizen')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition-colors ${
                    activeTab === 'citizen'
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-700 hover:text-slate-950 hover:bg-slate-100'
                  }`}
                >
                  <Home className="w-3.5 h-3.5" />
                  <span>{language === 'pa' ? 'ਮੌਸਮ ਡੈਸ਼ਬੋਰਡ' : language === 'hi' ? 'मौसम डैशबोर्ड' : 'Weather Dashboard'}</span>
                </button>

                <button
                  id="tab-disaster-emergency"
                  type="button"
                  onClick={() => onTabChange('emergency')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition-colors ${
                    activeTab === 'emergency'
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-700 hover:text-slate-950 hover:bg-slate-100'
                  }`}
                >
                  <AlertTriangle className="w-3.5 h-3.5 text-red-500" />
                  <span>{language === 'pa' ? 'ਐਮਰਜੈਂਸੀ ਹੈਲਪਲਾਈਨ' : language === 'hi' ? 'आपातकालीन सहायता' : 'Emergency Help'}</span>
                </button>

                <button
                  id="tab-agriculture"
                  type="button"
                  onClick={() => onTabChange('agriculture')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition-colors ${
                    activeTab === 'agriculture'
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-700 hover:text-slate-950 hover:bg-slate-100'
                  }`}
                >
                  <Sprout className="w-3.5 h-3.5 text-emerald-600" />
                  <span>{language === 'pa' ? 'ਖੇਤੀਬਾੜੀ ਸਲਾਹ' : language === 'hi' ? 'कृषि परामर्श' : 'Farmer Advisory'}</span>
                </button>

                <button
                  id="tab-risk-map"
                  type="button"
                  onClick={() => onTabChange('risk')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition-colors ${
                    activeTab === 'risk'
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-700 hover:text-slate-950 hover:bg-slate-100'
                  }`}
                >
                  <Map className="w-3.5 h-3.5" />
                  <span>{language === 'pa' ? 'ਜੋਖਮ ਨਕਸ਼ਾ' : language === 'hi' ? 'जोखिम नक्शा' : 'Risk Map'}</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-red-600" />
                </button>
              </>
            ) : (
              <>
                {/* Officer Navigation */}
                <button
                  id="tab-weathergpt-primary"
                  type="button"
                  onClick={() => onTabChange('weathergpt')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition-colors ${
                    activeTab === 'weathergpt'
                      ? 'bg-blue-600 text-white shadow-xs font-bold'
                      : 'text-blue-700 bg-blue-50/80 hover:bg-blue-100 border border-blue-200/70'
                  }`}
                >
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span>WEATHERGPT</span>
                </button>

                <button
                  id="tab-command-center"
                  type="button"
                  onClick={() => onTabChange('command')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition-colors ${
                    activeTab === 'command'
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-700 hover:text-slate-950 hover:bg-slate-100'
                  }`}
                >
                  <Home className="w-3.5 h-3.5" />
                  <span>
                    {language === 'pa' ? 'ਮੌਸਮ ਡੈਸ਼ਬੋਰਡ' : language === 'hi' ? 'मौसम डैशबोर्ड' : 'Weather Dashboard'}
                  </span>
                </button>

                <button
                  id="tab-disaster-emergency"
                  type="button"
                  onClick={() => onTabChange('emergency')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition-colors ${
                    activeTab === 'emergency'
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-700 hover:text-slate-950 hover:bg-slate-100'
                  }`}
                >
                  <AlertTriangle className="w-3.5 h-3.5 text-red-500" />
                  <span>{language === 'pa' ? 'ਐਮਰਜੈਂਸੀ ਹੈਲਪਲਾਈਨ' : language === 'hi' ? 'आपातकालीन सहायता' : 'Emergency Help'}</span>
                </button>

                <button
                  id="tab-agriculture"
                  type="button"
                  onClick={() => onTabChange('agriculture')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition-colors ${
                    activeTab === 'agriculture'
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-700 hover:text-slate-950 hover:bg-slate-100'
                  }`}
                >
                  <Sprout className="w-3.5 h-3.5 text-emerald-600" />
                  <span>{language === 'pa' ? 'ਖੇਤੀਬਾੜੀ ਸਲਾਹ' : language === 'hi' ? 'कृषि परामर्श' : 'Farmer Advisory'}</span>
                </button>

                <button
                  id="tab-risk-map"
                  type="button"
                  onClick={() => onTabChange('risk')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition-colors ${
                    activeTab === 'risk'
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-700 hover:text-slate-950 hover:bg-slate-100'
                  }`}
                >
                  <Map className="w-3.5 h-3.5" />
                  <span>{language === 'pa' ? 'ਜੋਖਮ ਨਕਸ਼ਾ' : language === 'hi' ? 'जोखिम नक्शा' : 'Risk Map'}</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-red-600" />
                </button>
              </>
            )}
          </nav>
        </div>

        {/* Right Side Controls */}
        <div className="flex items-center gap-1 sm:gap-2 min-w-0 shrink">
          {/* Dark / Light Mode Switcher */}
          <button
            id="btn-theme-toggle"
            type="button"
            onClick={toggleTheme}
            className="p-1.5 sm:px-2.5 sm:py-1.5 rounded-lg border text-xs font-semibold flex items-center justify-center gap-1.5 transition-all shrink-0 bg-white hover:bg-slate-50 text-slate-700 border-slate-200 cursor-pointer shadow-xs"
            title={
              isDarkMode
                ? language === 'pa' ? 'ਲਾਈਟ ਮੋਡ' : language === 'hi' ? 'लाइट मोड' : 'Switch to Light Mode'
                : language === 'pa' ? 'ਡਾਰਕ ਮੋਡ' : language === 'hi' ? 'डार्क मोड' : 'Switch to Dark Mode'
            }
            aria-label="Toggle Dark or Light Mode"
          >
            {isDarkMode ? (
              <Sun className="w-3.5 h-3.5 text-amber-400" />
            ) : (
              <Moon className="w-3.5 h-3.5 text-slate-600" />
            )}
          </button>

          {/* Audio Speak Alert Button */}
          <button
            type="button"
            onClick={handleToggleGlobalVoice}
            className={`px-2 sm:px-2.5 py-1.5 rounded-lg border text-xs font-semibold flex items-center gap-1.5 transition-colors shrink-0 ${
              isVoiceSpeaking
                ? 'bg-amber-100 text-amber-900 border-amber-300'
                : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'
            }`}
            title="Emergency audio broadcast"
          >
            {isVoiceSpeaking ? (
              <>
                <VolumeX className="w-3.5 h-3.5 text-amber-700" />
                <span className="hidden sm:inline">{language === 'pa' ? 'ਬੰਦ ਕਰੋ' : language === 'hi' ? 'रोकें' : 'Stop'}</span>
              </>
            ) : (
              <>
                <Volume2 className="w-3.5 h-3.5 text-slate-600" />
                <span className="hidden sm:inline">{language === 'pa' ? 'ਸੁਣੋ' : language === 'hi' ? 'सुनें' : 'Listen'}</span>
              </>
            )}
          </button>

          {/* Location Selector */}
          <div className="relative shrink-0">
            <button
              type="button"
              onClick={() => {
                setIsLocDropdownOpen(!isLocDropdownOpen);
                setIsLangDropdownOpen(false);
                setIsUserMenuOpen(false);
              }}
              className="flex items-center gap-1 px-2 sm:px-2.5 py-1.5 text-xs font-semibold text-slate-800 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg transition-colors"
            >
              <MapPin className="w-3.5 h-3.5 text-blue-600" />
              <span className="hidden sm:inline truncate sm:max-w-[120px]">
                {t('loc.' + selectedLocation, selectedLocation)}
              </span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {isLocDropdownOpen && (
              <div className="absolute right-0 mt-1 w-52 bg-white border border-slate-200 rounded-lg shadow-lg py-1.5 z-50 text-xs">
                <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  {language === 'pa' ? 'ਜ਼ਿਲ੍ਹਾ ਚੁਣੋ' : language === 'hi' ? 'ज़िला चुनें' : 'Select District'}
                </div>
                {locations.map((loc) => (
                  <button
                    key={loc}
                    type="button"
                    onClick={() => {
                      onLocationChange(loc);
                      setIsLocDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3 py-2 hover:bg-slate-50 flex items-center justify-between transition-colors ${
                      selectedLocation === loc ? 'font-bold text-blue-600 bg-blue-50/50' : 'text-slate-700'
                    }`}
                  >
                    <span>{t('loc.' + loc, loc)}</span>
                    {selectedLocation === loc && <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Language Selector */}
          <div className="relative shrink-0">
            <button
              id="language-selector-dropdown"
              type="button"
              onClick={() => {
                setIsLangDropdownOpen(!isLangDropdownOpen);
                setIsLocDropdownOpen(false);
                setIsUserMenuOpen(false);
              }}
              className="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-2.5 py-1.5 text-xs font-semibold text-slate-800 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg transition-colors"
            >
              <Globe className="w-3.5 h-3.5 text-slate-500" />
              <span className="sm:hidden">{languageLabels[language].code}</span>
              <span className="hidden sm:inline">{languageLabels[language].label}</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {isLangDropdownOpen && (
              <div className="absolute right-0 mt-1 w-44 bg-white border border-slate-200 rounded-lg shadow-lg py-1.5 z-50 text-xs">
                {(['pa', 'hi', 'en'] as Language[]).map((lng) => (
                  <button
                    key={lng}
                    type="button"
                    onClick={() => {
                      setLanguage(lng);
                      setIsLangDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3 py-2 hover:bg-slate-50 flex items-center justify-between transition-colors ${
                      language === lng ? 'font-bold text-blue-600 bg-blue-50/50' : 'text-slate-700'
                    }`}
                  >
                    <span>{languageLabels[lng].label}</span>
                    {language === lng && <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* User Auth / Login Button */}
          <button
            type="button"
            onClick={() => setIsLoginModalOpen(true)}
            className="flex items-center gap-1.5 px-2 sm:px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-800 transition-colors shrink-0"
          >
            {user?.role === 'OFFICER' ? (
              <Shield className="w-3.5 h-3.5 text-blue-600" />
            ) : user?.role === 'SCIENTIST' ? (
              <Sprout className="w-3.5 h-3.5 text-emerald-600" />
            ) : (
              <User className="w-3.5 h-3.5 text-slate-600" />
            )}
            <span className="hidden sm:inline max-w-[100px] truncate">
              {user ? user.name.split(' ')[0] : 'Sign In'}
            </span>
          </button>
        </div>
      </div>

      {/* Mobile Tab Navigation — contained chip scroller; does not widen the page */}
      <div className="md:hidden border-t border-slate-200 bg-slate-50 w-full min-w-0 max-w-full">
        <nav
          className="flex w-full min-w-0 max-w-full items-center gap-1.5 overflow-x-auto overscroll-x-contain px-3 py-1.5 text-xs font-medium touch-pan-x"
          aria-label="Mobile navigation"
        >
        {isCitizen ? (
          <>
            <button
              type="button"
              onClick={() => onTabChange('weathergpt')}
              className={`shrink-0 min-h-9 px-3 py-2 rounded-md whitespace-nowrap flex items-center gap-1 transition-colors ${
                activeTab === 'weathergpt' ? 'bg-blue-600 text-white font-semibold' : 'text-blue-700 bg-white border border-blue-200'
              }`}
            >
              <MessageSquare className="w-3 h-3" />
              <span>WEATHERGPT</span>
            </button>

            <button
              type="button"
              onClick={() => onTabChange('citizen')}
              className={`shrink-0 min-h-9 px-3 py-2 rounded-md whitespace-nowrap flex items-center gap-1 transition-colors ${
                activeTab === 'citizen' ? 'bg-slate-900 text-white font-semibold' : 'text-slate-700 bg-white'
              }`}
            >
              <Home className="w-3 h-3" />
              <span>{language === 'pa' ? 'ਡੈਸ਼ਬੋਰਡ' : language === 'hi' ? 'डैशबोर्ड' : 'Dashboard'}</span>
            </button>

            <button
              type="button"
              onClick={() => onTabChange('emergency')}
              className={`shrink-0 min-h-9 px-3 py-2 rounded-md whitespace-nowrap transition-colors ${
                activeTab === 'emergency' ? 'bg-slate-900 text-white font-semibold' : 'text-slate-700 bg-white'
              }`}
            >
              {language === 'pa' ? 'ਹੈਲਪਲਾਈਨ' : language === 'hi' ? 'सहायता' : 'Emergency'}
            </button>

            <button
              type="button"
              onClick={() => onTabChange('agriculture')}
              className={`shrink-0 min-h-9 px-3 py-2 rounded-md whitespace-nowrap transition-colors ${
                activeTab === 'agriculture' ? 'bg-slate-900 text-white font-semibold' : 'text-slate-700 bg-white'
              }`}
            >
              {language === 'pa' ? 'ਖੇਤੀ' : language === 'hi' ? 'कृषि' : 'Agri'}
            </button>

            <button
              type="button"
              onClick={() => onTabChange('risk')}
              className={`shrink-0 min-h-9 px-3 py-2 rounded-md whitespace-nowrap transition-colors ${
                activeTab === 'risk' ? 'bg-slate-900 text-white font-semibold' : 'text-slate-700 bg-white'
              }`}
            >
              {language === 'pa' ? 'ਨਕਸ਼ਾ' : language === 'hi' ? 'नक्शा' : 'Map'}
            </button>
          </>
        ) : (
          <>
            <button
              type="button"
              onClick={() => onTabChange('weathergpt')}
              className={`shrink-0 min-h-9 px-3 py-2 rounded-md whitespace-nowrap flex items-center gap-1 transition-colors ${
                activeTab === 'weathergpt' ? 'bg-blue-600 text-white font-semibold' : 'text-blue-700 bg-white border border-blue-200'
              }`}
            >
              <MessageSquare className="w-3 h-3" />
              <span>WEATHERGPT</span>
            </button>

            <button
              type="button"
              onClick={() => onTabChange('command')}
              className={`shrink-0 min-h-9 px-3 py-2 rounded-md whitespace-nowrap flex items-center gap-1 transition-colors ${
                activeTab === 'command' ? 'bg-slate-900 text-white font-semibold' : 'text-slate-700 bg-white'
              }`}
            >
              <Home className="w-3 h-3" />
              <span>{language === 'pa' ? 'ਡੈਸ਼ਬੋਰਡ' : language === 'hi' ? 'डैशबोर्ड' : 'Dashboard'}</span>
            </button>

            <button
              type="button"
              onClick={() => onTabChange('emergency')}
              className={`shrink-0 min-h-9 px-3 py-2 rounded-md whitespace-nowrap transition-colors ${
                activeTab === 'emergency' ? 'bg-slate-900 text-white font-semibold' : 'text-slate-700 bg-white'
              }`}
            >
              {language === 'pa' ? 'ਹੈਲਪਲਾਈਨ' : language === 'hi' ? 'सहायता' : 'Emergency'}
            </button>

            <button
              type="button"
              onClick={() => onTabChange('agriculture')}
              className={`shrink-0 min-h-9 px-3 py-2 rounded-md whitespace-nowrap transition-colors ${
                activeTab === 'agriculture' ? 'bg-slate-900 text-white font-semibold' : 'text-slate-700 bg-white'
              }`}
            >
              {language === 'pa' ? 'ਖੇਤੀ' : language === 'hi' ? 'कृषि' : 'Agri'}
            </button>

            <button
              type="button"
              onClick={() => onTabChange('risk')}
              className={`shrink-0 min-h-9 px-3 py-2 rounded-md whitespace-nowrap transition-colors ${
                activeTab === 'risk' ? 'bg-slate-900 text-white font-semibold' : 'text-slate-700 bg-white'
              }`}
            >
              {language === 'pa' ? 'ਨਕਸ਼ਾ' : language === 'hi' ? 'नक्शा' : 'Map'}
            </button>
          </>
        )}
        </nav>
      </div>
    </header>
  );
};
