import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { UserRole, Language } from '../types';
import {
  Shield,
  User,
  Lock,
  Phone,
  ArrowRight,
  Building2,
  Sprout,
  X,
  Sparkles,
  Globe,
  Check,
} from 'lucide-react';

interface LoginPageProps {
  isOpen: boolean;
  onClose?: () => void;
  isInitialScreen?: boolean;
  onLoginSuccess?: (role: UserRole) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({
  isOpen,
  onClose,
  isInitialScreen = false,
  onLoginSuccess,
}) => {
  const { user, login, logout } = useAuth();
  const { language, setLanguage } = useLanguage();

  const [selectedRole, setSelectedRole] = useState<UserRole>('CITIZEN');
  const [officerSubRole, setOfficerSubRole] = useState<'OFFICER' | 'SCIENTIST'>('OFFICER');

  // Citizen form fields
  const [citizenName, setCitizenName] = useState<string>('Harpreet Singh');
  const [citizenPhone, setCitizenPhone] = useState<string>('+91 94172-88776');

  // Officer form fields
  const [officerEmail, setOfficerEmail] = useState<string>('deoc.patiala@punjab.gov.in');
  const [officerPassword, setOfficerPassword] = useState<string>('••••••••••••');

  const [district, setDistrict] = useState<string>('Patiala, Punjab');
  const [authError, setAuthError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleRoleSelect = (role: UserRole) => {
    setSelectedRole(role);
    setAuthError(null);
    if (role === 'OFFICER') {
      setOfficerSubRole('OFFICER');
      setOfficerEmail('deoc.patiala@punjab.gov.in');
      setDistrict('Patiala, Punjab');
    } else if (role === 'SCIENTIST') {
      setOfficerSubRole('SCIENTIST');
      setOfficerEmail('agromet.scientist@pau.edu');
      setDistrict('Ludhiana Central');
    } else {
      setCitizenName('Harpreet Singh');
      setCitizenPhone('+91 94172-88776');
      setDistrict('Patiala, Punjab');
    }
  };

  const handleOfficerSubRoleSelect = (subRole: 'OFFICER' | 'SCIENTIST') => {
    setOfficerSubRole(subRole);
    setSelectedRole(subRole);
    if (subRole === 'OFFICER') {
      setOfficerEmail('deoc.patiala@punjab.gov.in');
      setDistrict('Patiala, Punjab');
    } else {
      setOfficerEmail('agromet.scientist@pau.edu');
      setDistrict('Ludhiana Central');
    }
  };

  const handleCitizenSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login({
      role: 'CITIZEN',
      name: citizenName.trim() || (language === 'pa' ? 'ਪੰਜਾਬ ਨਾਗਰਿਕ' : language === 'hi' ? 'नागरिक' : 'Citizen'),
      phone: citizenPhone.trim() || undefined,
      district,
      designation: language === 'pa' ? 'ਕਿਸਾਨ / ਪੰਜਾਬ ਨਿਵਾਸੀ' : language === 'hi' ? 'किसान / नागरिक' : 'Farmer / Resident',
      organization: `District Administration, ${district}`,
    });
    if (onLoginSuccess) onLoginSuccess('CITIZEN');
    if (onClose) onClose();
  };

  const handleOfficerSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!officerEmail.trim()) {
      setAuthError(
        language === 'pa'
          ? 'ਕਿਰਪਾ ਕਰਕੇ ਸਰਕਾਰੀ ਈਮੇਲ ਦਰਜ ਕਰੋ'
          : language === 'hi'
          ? 'कृपया आधिकारिक ईमेल दर्ज करें'
          : 'Please enter official email'
      );
      return;
    }

    const assignedRole = officerSubRole === 'OFFICER' ? 'OFFICER' : 'SCIENTIST';
    if (assignedRole === 'OFFICER') {
      login({
        role: 'OFFICER',
        name: 'Harpreet Singh Brar',
        email: officerEmail,
        district,
        badgeNumber: 'PB-DEOC-409',
        designation: 'District Emergency Operations Officer',
        organization: 'Punjab State Disaster Management Authority (PSDMA)',
      });
    } else {
      login({
        role: 'SCIENTIST',
        name: 'Dr. Manjit Kaur Gill',
        email: officerEmail,
        district,
        badgeNumber: 'PAU-SCI-118',
        designation: 'Senior Agro-Meteorologist & Extension Specialist',
        organization: 'Punjab Agricultural University (PAU), Ludhiana',
      });
    }
    if (onLoginSuccess) onLoginSuccess(assignedRole);
    if (onClose) onClose();
  };

  const handleQuickLogin = (role: UserRole) => {
    if (role === 'CITIZEN') {
      login({
        role: 'CITIZEN',
        name: 'Harpreet Singh (Farmer)',
        phone: '+91 94172-88776',
        district: 'Patiala, Punjab',
        designation: 'Farmer / Resident (Ward 14, Patiala)',
        organization: 'Citizen Portal (Patiala Rural)',
      });
    } else if (role === 'OFFICER') {
      login({
        role: 'OFFICER',
        name: 'Harpreet Singh Brar',
        email: 'deoc.patiala@punjab.gov.in',
        district: 'Patiala, Punjab',
        badgeNumber: 'PB-DEOC-409',
        designation: 'District Emergency Operations Officer',
        organization: 'Punjab State Disaster Management Authority (PSDMA)',
      });
    } else {
      login({
        role: 'SCIENTIST',
        name: 'Dr. Manjit Kaur Gill',
        email: 'agromet.scientist@pau.edu',
        district: 'Ludhiana Central',
        badgeNumber: 'PAU-SCI-118',
        designation: 'Senior Agro-Meteorologist',
        organization: 'Punjab Agricultural University (PAU), Ludhiana',
      });
    }
    if (onLoginSuccess) onLoginSuccess(role);
    if (onClose) onClose();
  };

  const districts = [
    'Patiala, Punjab',
    'Jalandhar (Doaba)',
    'Ludhiana Central',
    'Bathinda Cotton Belt',
    'Hoshiarpur Foothills',
    'Kapurthala Riverine',
  ];

  return (
    <div
      className={
        isInitialScreen
          ? 'min-h-screen bg-slate-900 flex flex-col justify-center items-center p-4 sm:p-6 text-slate-100'
          : 'fixed inset-0 z-[9999] flex items-center justify-center bg-slate-950/70 backdrop-blur-xs p-4 overflow-y-auto'
      }
    >
      <div className="w-full max-w-lg max-h-[92vh] flex flex-col bg-white rounded-2xl border border-slate-200 shadow-2xl overflow-hidden text-slate-900 animate-in fade-in zoom-in-95 duration-200">
        {/* Top Header: Brand Logo & Language Selector */}
        <div className="px-6 py-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <img
              src="/logo.png?v=2"
              alt="Logo"
              className="w-9 h-9 rounded-lg object-contain"
            />
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-slate-900 tracking-tight">
                  Weather<span className="text-blue-600">GPT</span>
                </h1>
              </div>
              <p className="text-[11px] text-slate-500 font-medium">
                {language === 'pa'
                  ? 'ਮੌਸਮ ਪੂਰਵ-ਅਨੁਮਾਨ ਤੇ ਆਫ਼ਤ ਸੂਚਨਾ AI'
                  : language === 'hi'
                  ? 'मौसम पूर्वानुमान एवं आपदा सूचना AI'
                  : 'Conversational Weather & Flood AI'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Language Switcher */}
            <div className="flex items-center bg-white border border-slate-200 rounded-lg p-0.5 text-xs font-semibold">
              <button
                type="button"
                onClick={() => setLanguage('pa')}
                className={`px-2 py-1 rounded transition-colors ${
                  language === 'pa' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                ਪੰਜਾਬੀ
              </button>
              <button
                type="button"
                onClick={() => setLanguage('hi')}
                className={`px-2 py-1 rounded transition-colors ${
                  language === 'hi' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                हिन्दी
              </button>
              <button
                type="button"
                onClick={() => setLanguage('en')}
                className={`px-2 py-1 rounded transition-colors ${
                  language === 'en' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                EN
              </button>
            </div>

            {/* Close button if opened as modal */}
            {!isInitialScreen && onClose && (
              <button
                type="button"
                onClick={onClose}
                className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Current status if signed in */}
        {user && (
          <div className="px-6 py-2.5 bg-blue-50 border-b border-blue-100 flex items-center justify-between text-xs shrink-0">
            <div>
              <span className="text-slate-500">
                {language === 'pa' ? 'ਮੌਜੂਦਾ ਲੌਗਇਨ:' : language === 'hi' ? 'सक्रिय सत्र:' : 'Signed in as:'}{' '}
              </span>
              <span className="font-semibold text-slate-900">{user.name}</span>{' '}
              <span className="text-slate-500">({user.role})</span>
            </div>
            <button
              type="button"
              onClick={logout}
              className="text-xs font-semibold text-red-600 hover:text-red-800 underline"
            >
              {language === 'pa' ? 'ਲੌਗਆਊਟ' : language === 'hi' ? 'लॉगआउट' : 'Sign Out'}
            </button>
          </div>
        )}

        <div className="p-6 sm:p-7 overflow-y-auto flex-1">
          {/* Welcome Message */}
          <div className="mb-5 text-center sm:text-left">
            <h2 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight">
              {language === 'pa'
                ? 'WeatherGPT ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ'
                : language === 'hi'
                ? 'WeatherGPT में आपका स्वागत है'
                : 'Welcome to WeatherGPT'}
            </h2>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              {language === 'pa'
                ? 'ਪੰਜਾਬ ਦੇ ਮੌਸਮ, ਹੜ੍ਹ ਚੇਤਾਵਨੀ ਅਤੇ ਖੇਤੀਬਾੜੀ ਸਲਾਹ ਲਈ ਆਪਣੀ ਭੂਮਿਕਾ ਅਨੁਸਾਰ ਲੌਗਇਨ ਕਰੋ।'
                : language === 'hi'
                ? 'पंजाब के मौसम, बाढ़ चेतावनी एवं कृषि परामर्श हेतु अपनी भूमिका अनुसार लॉगिन करें।'
                : 'Select your role to access conversational forecasts, flood alerts, and PAU crop advisories.'}
            </p>
          </div>

          {/* Primary Tabs: Citizen vs Officer (ChatGPT / Gemini Style) */}
          <div className="grid grid-cols-2 p-1 bg-slate-100 rounded-xl border border-slate-200 mb-6">
            <button
              type="button"
              onClick={() => handleRoleSelect('CITIZEN')}
              className={`py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                selectedRole === 'CITIZEN'
                  ? 'bg-white text-slate-900 shadow-xs border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <User className="w-3.5 h-3.5 text-blue-600" />
              <span>
                {language === 'pa' ? 'ਨਾਗਰਿਕ ਤੇ ਕਿਸਾਨ' : language === 'hi' ? 'नागरिक व किसान' : 'Citizen / Farmer'}
              </span>
            </button>

            <button
              type="button"
              onClick={() => handleRoleSelect('OFFICER')}
              className={`py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                selectedRole !== 'CITIZEN'
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Shield className="w-3.5 h-3.5 text-blue-400" />
              <span>
                {language === 'pa' ? 'ਸਰਕਾਰੀ ਅਧਿਕਾਰੀ' : language === 'hi' ? 'सरकारी अधिकारी' : 'Official / Scientist'}
              </span>
            </button>
          </div>

          {/* 1. CITIZEN & FARMER FORM */}
          {selectedRole === 'CITIZEN' ? (
            <form onSubmit={handleCitizenSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  {language === 'pa' ? 'ਤੁਹਾਡਾ ਨਾਮ (ਜਾਂ ਸਿੱਧਾ ਜਾਰੀ ਰੱਖੋ)' : language === 'hi' ? 'आपका नाम (या सीधे जारी रखें)' : 'Full Name'}
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    value={citizenName}
                    onChange={(e) => setCitizenName(e.target.value)}
                    placeholder="e.g. Harpreet Singh"
                    className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-300 text-xs font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold text-slate-700">
                    {language === 'pa' ? 'ਮੋਬਾਈਲ ਨੰਬਰ (ਹੜ੍ਹ SMS ਲਈ)' : language === 'hi' ? 'मोबाइल नंबर (बाढ़ SMS हेतु)' : 'Mobile Phone (for Flood SMS Alerts)'}
                  </label>
                  <span className="text-[10px] text-slate-400 font-medium">Optional</span>
                </div>
                <div className="relative">
                  <Phone className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    value={citizenPhone}
                    onChange={(e) => setCitizenPhone(e.target.value)}
                    placeholder="+91 94172-88776"
                    className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-300 text-xs font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  {language === 'pa' ? 'ਤੁਹਾਡਾ ਜ਼ਿਲ੍ਹਾ / ਇਲਾਕਾ' : language === 'hi' ? 'आपका जिला / क्षेत्र' : 'District / Region in Punjab'}
                </label>
                <select
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-medium text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {districts.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>

              {/* Primary Citizen Submit */}
              <button
                type="submit"
                className="w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold flex items-center justify-center gap-2 shadow-xs transition-colors"
              >
                <span>
                  {language === 'pa'
                    ? 'WeatherGPT ਨਾਲ ਅੱਗੇ ਵਧੋ'
                    : language === 'hi'
                    ? 'WeatherGPT के साथ आगे बढ़ें'
                    : 'Continue to WeatherGPT'}
                </span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>

              {/* Fast 1-Tap Options */}
              <div className="pt-3 border-t border-slate-100 flex flex-col gap-2">
                <button
                  type="button"
                  onClick={() => handleQuickLogin('CITIZEN')}
                  className="w-full py-2 px-3 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-[11px] font-semibold text-slate-700 flex items-center justify-between transition-colors"
                >
                  <span>
                    ⚡ {language === 'pa' ? 'ਤੁਰੰਤ ਕਿਸਾਨ ਲੌਗਇਨ (ਪਟਿਆਲਾ)' : language === 'hi' ? 'त्वरित किसान लॉगिन (पटियाला)' : 'Quick Farmer Access (Patiala)'}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">1-Tap</span>
                </button>
              </div>
            </form>
          ) : (
            /* 2. OFFICIAL / SCIENTIST FORM */
            <form onSubmit={handleOfficerSubmit} className="space-y-4">
              {/* Sub-Role Selector: DEOC vs PAU */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  {language === 'pa' ? 'ਸਰਕਾਰੀ ਵਿਭਾਗ / ਸੰਸਥਾ' : language === 'hi' ? 'शासकीय विभाग / संस्थान' : 'Department Authority'}
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => handleOfficerSubRoleSelect('OFFICER')}
                    className={`p-2.5 rounded-lg border text-left transition-all ${
                      officerSubRole === 'OFFICER'
                        ? 'border-blue-600 bg-blue-50/60 text-blue-900 font-bold'
                        : 'border-slate-200 hover:bg-slate-50 text-slate-700 font-medium'
                    }`}
                  >
                    <div className="flex items-center gap-1.5 text-xs">
                      <Building2 className="w-3.5 h-3.5 text-blue-600" />
                      <span>DEOC Officer</span>
                    </div>
                    <span className="text-[10px] text-slate-500 block mt-0.5">
                      {language === 'pa' ? 'ਆਫ਼ਤ ਪ੍ਰਬੰਧਨ ਅਫ਼ਸਰ' : language === 'hi' ? 'आपदा प्रबंधन अधिकारी' : 'Disaster Operations'}
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleOfficerSubRoleSelect('SCIENTIST')}
                    className={`p-2.5 rounded-lg border text-left transition-all ${
                      officerSubRole === 'SCIENTIST'
                        ? 'border-blue-600 bg-blue-50/60 text-blue-900 font-bold'
                        : 'border-slate-200 hover:bg-slate-50 text-slate-700 font-medium'
                    }`}
                  >
                    <div className="flex items-center gap-1.5 text-xs">
                      <Sprout className="w-3.5 h-3.5 text-emerald-600" />
                      <span>PAU Scientist</span>
                    </div>
                    <span className="text-[10px] text-slate-500 block mt-0.5">
                      {language === 'pa' ? 'ਖੇਤੀ ਵਿਗਿਆਨੀ' : language === 'hi' ? 'कृषि वैज्ञानिक' : 'Agro-Meteorology'}
                    </span>
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  {language === 'pa' ? 'ਸਰਕਾਰੀ ਈਮੇਲ ਜਾਂ ਬੈਜ ਨੰਬਰ' : language === 'hi' ? 'आधिकारिक ईमेल अथवा बैच संख्या' : 'Official Email / Badge ID'}
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    value={officerEmail}
                    onChange={(e) => setOfficerEmail(e.target.value)}
                    placeholder="officer@punjab.gov.in"
                    className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-300 text-xs font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  {language === 'pa' ? 'ਸੁਰੱਖਿਆ ਪਾਸਕੋਡ' : language === 'hi' ? 'सुरक्षा पासकोड' : 'Security Passcode'}
                </label>
                <input
                  type="password"
                  value={officerPassword}
                  onChange={(e) => setOfficerPassword(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  {language === 'pa' ? 'ਜ਼ਿਲ੍ਹਾ ਅਧਿਕਾਰ ਖੇਤਰ' : language === 'hi' ? 'जिला अधिकार क्षेत्र' : 'Jurisdiction District'}
                </label>
                <select
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-medium text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {districts.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>

              {authError && (
                <div className="p-2.5 rounded-lg bg-red-50 text-red-700 text-xs border border-red-200">
                  {authError}
                </div>
              )}

              {/* Primary Officer Submit */}
              <button
                type="submit"
                className="w-full py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold flex items-center justify-center gap-2 shadow-xs transition-colors"
              >
                <Shield className="w-3.5 h-3.5 text-blue-400" />
                <span>
                  {language === 'pa'
                    ? 'ਸਰਕਾਰੀ ਅਧਿਕਾਰ ਪ੍ਰਮਾਣਿਤ ਕਰੋ'
                    : language === 'hi'
                    ? 'आधिकारिक पहुंच प्रमाणित करें'
                    : 'Authenticate Official Access'}
                </span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>

              {/* Fast 1-Tap Officer Options */}
              <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row gap-2">
                <button
                  type="button"
                  onClick={() => handleQuickLogin('OFFICER')}
                  className="flex-1 py-2 px-3 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-[11px] font-semibold text-slate-700 flex items-center justify-between transition-colors"
                >
                  <span>⚡ DEOC Officer</span>
                  <span className="text-[10px] text-slate-400 font-mono">Demo</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleQuickLogin('SCIENTIST')}
                  className="flex-1 py-2 px-3 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-[11px] font-semibold text-slate-700 flex items-center justify-between transition-colors"
                >
                  <span>⚡ PAU Scientist</span>
                  <span className="text-[10px] text-slate-400 font-mono">Demo</span>
                </button>
              </div>
            </form>
          )}

          {/* Guest Access Link */}
          <div className="mt-5 text-center">
            <button
              type="button"
              onClick={() => handleQuickLogin('CITIZEN')}
              className="text-xs font-medium text-slate-500 hover:text-blue-600 underline transition-colors"
            >
              {language === 'pa'
                ? 'ਬਿਨਾਂ ਲੌਗਇਨ ਕੀਤੇ ਮਹਿਮਾਨ ਵਜੋਂ ਦੇਖੋ (Guest Access)'
                : language === 'hi'
                ? 'बिना लॉगिन अतिथि के रूप में देखें (Guest Access)'
                : 'Explore without signing in (Instant Guest Preview)'}
            </button>
          </div>
        </div>

        {/* Footer info */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 text-center text-[11px] text-slate-500">
          {language === 'pa'
            ? 'ਪੰਜਾਬ ਰਾਜ ਆਫ਼ਤ ਪ੍ਰਬੰਧਨ ਅਥਾਰਟੀ (PSDMA) ਅਤੇ PAU ਲੁਧਿਆਣਾ'
            : language === 'hi'
            ? 'पंजाब राज्य आपदा प्रबंधन प्राधिकरण (PSDMA) एवं PAU लुधियाना'
            : 'Operational Under PSDMA & Punjab Agricultural University (PAU)'}
        </div>
      </div>
    </div>
  );
};
