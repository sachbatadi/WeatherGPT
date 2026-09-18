import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { speakText, stopSpeaking } from '../utils/speech';
import {
  Sun,
  Moon,
  CloudRain,
  CloudSun,
  CloudLightning,
  Cloud,
  Droplets,
  Wind as WindIcon,
  Volume2,
  VolumeX,
} from 'lucide-react';

interface HourlyData {
  time: string;
  timeLabelPa: string;
  timeLabelHi: string;
  tempC: number;
  tempF: number;
  precipPct: number;
  windKmh: number;
  condition: string;
}

interface DailyForecast {
  dayName: string;
  dayPa: string;
  dayHi: string;
  highC: number;
  lowC: number;
  highF: number;
  lowF: number;
  condition: 'clear' | 'cloudy' | 'rain' | 'thunder' | 'partlyCloudy';
  conditionTextEn: string;
  conditionTextPa: string;
  conditionTextHi: string;
  hourly: HourlyData[];
}

export const GoogleWeatherCard: React.FC<{
  locationName?: string;
}> = ({ locationName = 'Patiala, Punjab' }) => {
  const { language } = useLanguage();
  const [unit, setUnit] = useState<'C' | 'F'>('C');
  const [activeTab, setActiveTab] = useState<'temp' | 'precip' | 'wind'>('temp');
  const [selectedDayIndex, setSelectedDayIndex] = useState<number>(0);
  const [hoveredHourIndex, setHoveredHourIndex] = useState<number | null>(null);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);

  // 8-Day Forecast data mirroring Google Weather structure
  const forecastDays: DailyForecast[] = [
    {
      dayName: 'Wed',
      dayPa: 'ਬੁੱਧ',
      dayHi: 'बुध',
      highC: 34,
      lowC: 23,
      highF: 93,
      lowF: 73,
      condition: 'clear',
      conditionTextEn: 'Clear',
      conditionTextPa: 'ਸਾਫ਼',
      conditionTextHi: 'साफ',
      hourly: [
        { time: '3 am', timeLabelPa: '3 ਸਵੇਰੇ', timeLabelHi: '3 पूर्वाह्न', tempC: 24, tempF: 75, precipPct: 0, windKmh: 5, condition: 'clear' },
        { time: '6 am', timeLabelPa: '6 ਸਵੇਰੇ', timeLabelHi: '6 पूर्वाह्न', tempC: 24, tempF: 75, precipPct: 0, windKmh: 5, condition: 'clear' },
        { time: '9 am', timeLabelPa: '9 ਸਵੇਰੇ', timeLabelHi: '9 पूर्वाह्न', tempC: 27, tempF: 81, precipPct: 0, windKmh: 7, condition: 'clear' },
        { time: '12 pm', timeLabelPa: '12 ਦੁਪਹਿਰ', timeLabelHi: '12 दोपहर', tempC: 32, tempF: 90, precipPct: 0, windKmh: 8, condition: 'clear' },
        { time: '3 pm', timeLabelPa: '3 ਦੁਪਹਿਰ', timeLabelHi: '3 अपराह्न', tempC: 33, tempF: 91, precipPct: 0, windKmh: 9, condition: 'clear' },
        { time: '6 pm', timeLabelPa: '6 ਸ਼ਾਮ', timeLabelHi: '6 शाम', tempC: 32, tempF: 90, precipPct: 0, windKmh: 7, condition: 'clear' },
        { time: '9 pm', timeLabelPa: '9 ਰਾਤ', timeLabelHi: '9 रात', tempC: 28, tempF: 82, precipPct: 0, windKmh: 5, condition: 'clear' },
        { time: '12 am', timeLabelPa: '12 ਰਾਤ', timeLabelHi: '12 रात', tempC: 26, tempF: 79, precipPct: 0, windKmh: 5, condition: 'clear' },
      ],
    },
    {
      dayName: 'Thu',
      dayPa: 'ਵੀਰ',
      dayHi: 'गुरु',
      highC: 31,
      lowC: 23,
      highF: 88,
      lowF: 73,
      condition: 'partlyCloudy',
      conditionTextEn: 'Scattered Showers',
      conditionTextPa: 'ਰੁਕ-ਰੁਕ ਕੇ ਮੀਂਹ',
      conditionTextHi: 'रुक-रुक कर वर्षा',
      hourly: [
        { time: '3 am', timeLabelPa: '3 ਸਵੇਰੇ', timeLabelHi: '3 पूर्वाह्न', tempC: 24, tempF: 75, precipPct: 30, windKmh: 12, condition: 'partlyCloudy' },
        { time: '6 am', timeLabelPa: '6 ਸਵੇਰੇ', timeLabelHi: '6 पूर्वाह्न', tempC: 25, tempF: 77, precipPct: 40, windKmh: 15, condition: 'rain' },
        { time: '9 am', timeLabelPa: '9 ਸਵੇਰੇ', timeLabelHi: '9 पूर्वाह्न', tempC: 28, tempF: 82, precipPct: 50, windKmh: 18, condition: 'rain' },
        { time: '12 pm', timeLabelPa: '12 ਦੁਪਹਿਰ', timeLabelHi: '12 दोपहर', tempC: 31, tempF: 88, precipPct: 45, windKmh: 20, condition: 'partlyCloudy' },
        { time: '3 pm', timeLabelPa: '3 ਦੁਪਹਿਰ', timeLabelHi: '3 अपराह्न', tempC: 31, tempF: 88, precipPct: 35, windKmh: 18, condition: 'partlyCloudy' },
        { time: '6 pm', timeLabelPa: '6 ਸ਼ਾਮ', timeLabelHi: '6 शाम', tempC: 29, tempF: 84, precipPct: 20, windKmh: 14, condition: 'cloudy' },
        { time: '9 pm', timeLabelPa: '9 ਰਾਤ', timeLabelHi: '9 रात', tempC: 26, tempF: 79, precipPct: 15, windKmh: 12, condition: 'partlyCloudy' },
        { time: '12 am', timeLabelPa: '12 ਰਾਤ', timeLabelHi: '12 रात', tempC: 24, tempF: 75, precipPct: 10, windKmh: 8, condition: 'clear' },
      ],
    },
    {
      dayName: 'Fri',
      dayPa: 'ਸ਼ੁੱਕਰ',
      dayHi: 'शुक्र',
      highC: 32,
      lowC: 22,
      highF: 90,
      lowF: 72,
      condition: 'clear',
      conditionTextEn: 'Sunny & Clearing',
      conditionTextPa: 'ਧੁੱਪ ਤੇ ਸਾਫ਼ ਮੌਸਮ',
      conditionTextHi: 'धूप एवं साफ मौसम',
      hourly: [
        { time: '3 am', timeLabelPa: '3 ਸਵੇਰੇ', timeLabelHi: '3 पूर्वाह्न', tempC: 23, tempF: 73, precipPct: 10, windKmh: 8, condition: 'clear' },
        { time: '6 am', timeLabelPa: '6 ਸਵੇਰੇ', timeLabelHi: '6 पूर्वाह्न', tempC: 24, tempF: 75, precipPct: 10, windKmh: 10, condition: 'clear' },
        { time: '9 am', timeLabelPa: '9 ਸਵੇਰੇ', timeLabelHi: '9 पूर्वाह्न', tempC: 28, tempF: 82, precipPct: 5, windKmh: 12, condition: 'clear' },
        { time: '12 pm', timeLabelPa: '12 ਦੁਪਹਿਰ', timeLabelHi: '12 दोपहर', tempC: 31, tempF: 88, precipPct: 5, windKmh: 15, condition: 'clear' },
        { time: '3 pm', timeLabelPa: '3 ਦੁਪਹਿਰ', timeLabelHi: '3 अपराह्न', tempC: 32, tempF: 90, precipPct: 5, windKmh: 14, condition: 'clear' },
        { time: '6 pm', timeLabelPa: '6 ਸ਼ਾਮ', timeLabelHi: '6 शाम', tempC: 30, tempF: 86, precipPct: 5, windKmh: 10, condition: 'clear' },
        { time: '9 pm', timeLabelPa: '9 ਰਾਤ', timeLabelHi: '9 रात', tempC: 26, tempF: 79, precipPct: 0, windKmh: 8, condition: 'clear' },
        { time: '12 am', timeLabelPa: '12 ਰਾਤ', timeLabelHi: '12 रात', tempC: 24, tempF: 75, precipPct: 0, windKmh: 6, condition: 'clear' },
      ],
    },
    {
      dayName: 'Sat',
      dayPa: 'ਸ਼ਨੀ',
      dayHi: 'शनि',
      highC: 33,
      lowC: 23,
      highF: 91,
      lowF: 73,
      condition: 'clear',
      conditionTextEn: 'Mostly Sunny',
      conditionTextPa: 'ਸਾਫ਼ ਤੇ ਨਿੱਘਾ',
      conditionTextHi: 'मुख्यतः धूप',
      hourly: [
        { time: '3 am', timeLabelPa: '3 ਸਵੇਰੇ', timeLabelHi: '3 पूर्वाह्न', tempC: 23, tempF: 73, precipPct: 5, windKmh: 6, condition: 'clear' },
        { time: '6 am', timeLabelPa: '6 ਸਵੇਰੇ', timeLabelHi: '6 पूर्वाह्न', tempC: 24, tempF: 75, precipPct: 5, windKmh: 8, condition: 'clear' },
        { time: '9 am', timeLabelPa: '9 ਸਵੇਰੇ', timeLabelHi: '9 पूर्वाह्न', tempC: 28, tempF: 82, precipPct: 5, windKmh: 10, condition: 'clear' },
        { time: '12 pm', timeLabelPa: '12 ਦੁਪਹਿਰ', timeLabelHi: '12 दोपहर', tempC: 32, tempF: 90, precipPct: 5, windKmh: 12, condition: 'clear' },
        { time: '3 pm', timeLabelPa: '3 ਦੁਪਹਿਰ', timeLabelHi: '3 अपराह्न', tempC: 33, tempF: 91, precipPct: 5, windKmh: 12, condition: 'clear' },
        { time: '6 pm', timeLabelPa: '6 ਸ਼ਾਮ', timeLabelHi: '6 शाम', tempC: 30, tempF: 86, precipPct: 5, windKmh: 8, condition: 'clear' },
        { time: '9 pm', timeLabelPa: '9 ਰਾਤ', timeLabelHi: '9 रात', tempC: 27, tempF: 81, precipPct: 0, windKmh: 6, condition: 'clear' },
        { time: '12 am', timeLabelPa: '12 ਰਾਤ', timeLabelHi: '12 रात', tempC: 24, tempF: 75, precipPct: 0, windKmh: 5, condition: 'clear' },
      ],
    },
    {
      dayName: 'Sun',
      dayPa: 'ਐਤ',
      dayHi: 'रवि',
      highC: 33,
      lowC: 23,
      highF: 91,
      lowF: 73,
      condition: 'clear',
      conditionTextEn: 'Sunny',
      conditionTextPa: 'ਸਾਫ਼ ਧੁੱਪ',
      conditionTextHi: 'साफ धूप',
      hourly: [
        { time: '3 am', timeLabelPa: '3 ਸਵੇਰੇ', timeLabelHi: '3 पूर्वाह्न', tempC: 24, tempF: 75, precipPct: 0, windKmh: 5, condition: 'clear' },
        { time: '6 am', timeLabelPa: '6 ਸਵੇਰੇ', timeLabelHi: '6 पूर्वाह्न', tempC: 25, tempF: 77, precipPct: 0, windKmh: 6, condition: 'clear' },
        { time: '9 am', timeLabelPa: '9 ਸਵੇਰੇ', timeLabelHi: '9 पूर्वाह्न', tempC: 29, tempF: 84, precipPct: 0, windKmh: 8, condition: 'clear' },
        { time: '12 pm', timeLabelPa: '12 ਦੁਪਹਿਰ', timeLabelHi: '12 दोपहर', tempC: 32, tempF: 90, precipPct: 5, windKmh: 10, condition: 'clear' },
        { time: '3 pm', timeLabelPa: '3 ਦੁਪਹਿਰ', timeLabelHi: '3 अपराह्न', tempC: 33, tempF: 91, precipPct: 5, windKmh: 10, condition: 'clear' },
        { time: '6 pm', timeLabelPa: '6 ਸ਼ਾਮ', timeLabelHi: '6 शाम', tempC: 30, tempF: 86, precipPct: 0, windKmh: 7, condition: 'clear' },
        { time: '9 pm', timeLabelPa: '9 ਰਾਤ', timeLabelHi: '9 रात', tempC: 27, tempF: 81, precipPct: 0, windKmh: 5, condition: 'clear' },
        { time: '12 am', timeLabelPa: '12 ਰਾਤ', timeLabelHi: '12 रात', tempC: 25, tempF: 77, precipPct: 0, windKmh: 4, condition: 'clear' },
      ],
    },
    {
      dayName: 'Mon',
      dayPa: 'ਸੋਮ',
      dayHi: 'सोम',
      highC: 34,
      lowC: 24,
      highF: 93,
      lowF: 75,
      condition: 'clear',
      conditionTextEn: 'Sunny & Warm',
      conditionTextPa: 'ਨਿੱਘੀ ਧੁੱਪ',
      conditionTextHi: 'धूप व उष्णता',
      hourly: [
        { time: '3 am', timeLabelPa: '3 ਸਵੇਰੇ', timeLabelHi: '3 पूर्वाह्न', tempC: 24, tempF: 75, precipPct: 0, windKmh: 5, condition: 'clear' },
        { time: '6 am', timeLabelPa: '6 ਸਵੇਰੇ', timeLabelHi: '6 पूर्वाह्न', tempC: 25, tempF: 77, precipPct: 0, windKmh: 6, condition: 'clear' },
        { time: '9 am', timeLabelPa: '9 ਸਵੇਰੇ', timeLabelHi: '9 पूर्वाह्न', tempC: 29, tempF: 84, precipPct: 0, windKmh: 8, condition: 'clear' },
        { time: '12 pm', timeLabelPa: '12 ਦੁਪਹਿਰ', timeLabelHi: '12 दोपहर', tempC: 33, tempF: 91, precipPct: 0, windKmh: 10, condition: 'clear' },
        { time: '3 pm', timeLabelPa: '3 ਦੁਪਹਿਰ', timeLabelHi: '3 अपराह्न', tempC: 34, tempF: 93, precipPct: 0, windKmh: 12, condition: 'clear' },
        { time: '6 pm', timeLabelPa: '6 ਸ਼ਾਮ', timeLabelHi: '6 शाम', tempC: 31, tempF: 88, precipPct: 0, windKmh: 8, condition: 'clear' },
        { time: '9 pm', timeLabelPa: '9 ਰਾਤ', timeLabelHi: '9 रात', tempC: 28, tempF: 82, precipPct: 0, windKmh: 6, condition: 'clear' },
        { time: '12 am', timeLabelPa: '12 ਰਾਤ', timeLabelHi: '12 रात', tempC: 25, tempF: 77, precipPct: 0, windKmh: 5, condition: 'clear' },
      ],
    },
    {
      dayName: 'Tue',
      dayPa: 'ਮੰਗਲ',
      dayHi: 'मंगल',
      highC: 34,
      lowC: 23,
      highF: 93,
      lowF: 73,
      condition: 'clear',
      conditionTextEn: 'Sunny',
      conditionTextPa: 'ਸਾਫ਼ ਅਸਮਾਨ',
      conditionTextHi: 'साफ आसमान',
      hourly: [
        { time: '3 am', timeLabelPa: '3 ਸਵੇਰੇ', timeLabelHi: '3 पूर्वाह्न', tempC: 24, tempF: 75, precipPct: 0, windKmh: 5, condition: 'clear' },
        { time: '6 am', timeLabelPa: '6 ਸਵੇਰੇ', timeLabelHi: '6 पूर्वाह्न', tempC: 25, tempF: 77, precipPct: 0, windKmh: 6, condition: 'clear' },
        { time: '9 am', timeLabelPa: '9 ਸਵੇਰੇ', timeLabelHi: '9 पूर्वाह्न', tempC: 29, tempF: 84, precipPct: 0, windKmh: 8, condition: 'clear' },
        { time: '12 pm', timeLabelPa: '12 ਦੁਪਹਿਰ', timeLabelHi: '12 दोपहर', tempC: 33, tempF: 91, precipPct: 0, windKmh: 10, condition: 'clear' },
        { time: '3 pm', timeLabelPa: '3 ਦੁਪਹਿਰ', timeLabelHi: '3 अपराह्न', tempC: 34, tempF: 93, precipPct: 0, windKmh: 11, condition: 'clear' },
        { time: '6 pm', timeLabelPa: '6 ਸ਼ਾਮ', timeLabelHi: '6 शाम', tempC: 31, tempF: 88, precipPct: 0, windKmh: 8, condition: 'clear' },
        { time: '9 pm', timeLabelPa: '9 ਰਾਤ', timeLabelHi: '9 रात', tempC: 27, tempF: 81, precipPct: 0, windKmh: 6, condition: 'clear' },
        { time: '12 am', timeLabelPa: '12 ਰਾਤ', timeLabelHi: '12 रात', tempC: 24, tempF: 75, precipPct: 0, windKmh: 5, condition: 'clear' },
      ],
    },
    {
      dayName: 'Wed',
      dayPa: 'ਬੁੱਧ',
      dayHi: 'बुध',
      highC: 35,
      lowC: 24,
      highF: 95,
      lowF: 75,
      condition: 'clear',
      conditionTextEn: 'Sunny',
      conditionTextPa: 'ਸਾਫ਼ ਧੁੱਪ',
      conditionTextHi: 'साफ धूप',
      hourly: [
        { time: '3 am', timeLabelPa: '3 ਸਵੇਰੇ', timeLabelHi: '3 पूर्वाह्न', tempC: 24, tempF: 75, precipPct: 0, windKmh: 5, condition: 'clear' },
        { time: '6 am', timeLabelPa: '6 ਸਵੇਰੇ', timeLabelHi: '6 पूर्वाह्न', tempC: 26, tempF: 79, precipPct: 0, windKmh: 7, condition: 'clear' },
        { time: '9 am', timeLabelPa: '9 ਸਵੇਰੇ', timeLabelHi: '9 पूर्वाह्न', tempC: 30, tempF: 86, precipPct: 0, windKmh: 9, condition: 'clear' },
        { time: '12 pm', timeLabelPa: '12 ਦੁਪਹਿਰ', timeLabelHi: '12 दोपहर', tempC: 34, tempF: 93, precipPct: 0, windKmh: 12, condition: 'clear' },
        { time: '3 pm', timeLabelPa: '3 ਦੁਪਹਿਰ', timeLabelHi: '3 अपराह्न', tempC: 35, tempF: 95, precipPct: 0, windKmh: 12, condition: 'clear' },
        { time: '6 pm', timeLabelPa: '6 ਸ਼ਾਮ', timeLabelHi: '6 शाम', tempC: 32, tempF: 90, precipPct: 0, windKmh: 9, condition: 'clear' },
        { time: '9 pm', timeLabelPa: '9 ਰਾਤ', timeLabelHi: '9 रात', tempC: 28, tempF: 82, precipPct: 0, windKmh: 6, condition: 'clear' },
        { time: '12 am', timeLabelPa: '12 ਰਾਤ', timeLabelHi: '12 रात', tempC: 25, tempF: 77, precipPct: 0, windKmh: 5, condition: 'clear' },
      ],
    },
  ];

  const currentDay = forecastDays[selectedDayIndex];
  const hourlyData = currentDay.hourly;

  const currentConditionText =
    language === 'pa'
      ? currentDay.conditionTextPa
      : language === 'hi'
      ? currentDay.conditionTextHi
      : currentDay.conditionTextEn;

  const dayLabel =
    language === 'pa'
      ? currentDay.dayPa + 'ਵਾਰ'
      : language === 'hi'
      ? currentDay.dayHi + 'वार'
      : currentDay.dayName + 'nesday';

  const currentHour = hourlyData[0];
  const currentTemp = unit === 'C' ? currentHour.tempC : currentHour.tempF;

  // Voice narration for meteorological conditions
  const handleSpeakWeather = () => {
    if (isSpeaking) {
      stopSpeaking();
      setIsSpeaking(false);
      return;
    }

    const narration =
      language === 'pa'
        ? `ਪਟਿਆਲਾ ਵਿੱਚ ਅੱਜ ਦਾ ਤਾਪਮਾਨ ${currentHour.tempC} ਡਿਗਰੀ ਸੈਲਸੀਅਸ ਹੈ। ਮੌਸਮ ${currentDay.conditionTextPa} ਹੈ। ਵਰਖਾ ਦੀ ਸੰਭਾਵਨਾ ${currentHour.precipPct} ਪ੍ਰਤੀਸ਼ਤ ਹੈ, ਨਮੀ 90 ਪ੍ਰਤੀਸ਼ਤ ਅਤੇ ਹਵਾ ਦੀ ਰਫ਼ਤਾਰ ${currentHour.windKmh} ਕਿਲੋਮੀਟਰ ਪ੍ਰਤੀ ਘੰਟਾ ਹੈ।`
        : language === 'hi'
        ? `पटियाला में आज का तापमान ${currentHour.tempC} डिग्री सेल्सियस है। मौसम ${currentDay.conditionTextHi} है। वर्षा की संभावना ${currentHour.precipPct} प्रतिशत है, आर्द्रता 90 प्रतिशत और हवा की गति ${currentHour.windKmh} किलोमीटर प्रति घंटा है।`
        : `Today's weather in Patiala is ${currentHour.tempC} degrees Celsius with ${currentDay.conditionTextEn}. Precipitation probability is ${currentHour.precipPct} percent, humidity 90 percent, and wind speed ${currentHour.windKmh} kilometers per hour.`;

    speakText(
      narration,
      language,
      () => setIsSpeaking(true),
      () => setIsSpeaking(false)
    );
  };

  // Weather Icon renderer
  const renderWeatherIcon = (condition: string, size = 'w-10 h-10') => {
    switch (condition) {
      case 'clear':
        return <Sun className={`${size} text-amber-500 fill-amber-400`} />;
      case 'partlyCloudy':
        return <CloudSun className={`${size} text-amber-500`} />;
      case 'cloudy':
        return <Cloud className={`${size} text-slate-400`} />;
      case 'thunder':
        return <CloudLightning className={`${size} text-amber-500`} />;
      case 'rain':
      default:
        return <CloudRain className={`${size} text-blue-500`} />;
    }
  };

  // SVG Chart Calculation
  const chartWidth = 720;
  const chartHeight = 95;
  const paddingX = 36;
  const paddingY = 20;
  const availableWidth = chartWidth - paddingX * 2;
  const availableHeight = chartHeight - paddingY * 2;

  // Values depending on activeTab
  const values = hourlyData.map((d) => {
    if (activeTab === 'temp') return unit === 'C' ? d.tempC : d.tempF;
    if (activeTab === 'precip') return d.precipPct;
    return d.windKmh;
  });

  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const valRange = maxVal === minVal ? 1 : maxVal - minVal;

  const points = values.map((val, idx) => {
    const x = paddingX + (idx / (values.length - 1)) * availableWidth;
    const y = chartHeight - paddingY - ((val - minVal) / valRange) * availableHeight;
    return { x, y, val, hour: hourlyData[idx] };
  });

  // Create smooth Bezier spline path
  const createSmoothPath = () => {
    if (points.length === 0) return '';
    let path = `M ${points[0].x} ${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i];
      const p1 = points[i + 1];
      const cx = (p0.x + p1.x) / 2;
      path += ` C ${cx} ${p0.y}, ${cx} ${p1.y}, ${p1.x} ${p1.y}`;
    }
    return path;
  };

  const linePath = createSmoothPath();
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${chartHeight} L ${points[0].x} ${chartHeight} Z`;

  // Color theme per tab
  const getThemeColor = () => {
    if (activeTab === 'temp') return { stroke: '#f59e0b', fillStart: 'rgba(245, 158, 11, 0.20)', fillEnd: 'rgba(245, 158, 11, 0.01)', dot: '#d97706' };
    if (activeTab === 'precip') return { stroke: '#2563eb', fillStart: 'rgba(37, 99, 235, 0.22)', fillEnd: 'rgba(37, 99, 235, 0.01)', dot: '#2563eb' };
    return { stroke: '#0d9488', fillStart: 'rgba(13, 148, 136, 0.22)', fillEnd: 'rgba(13, 148, 136, 0.01)', dot: '#0f766e' };
  };

  const theme = getThemeColor();

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-5 text-slate-900 overflow-hidden font-sans">
      {/* Top Header: Location, Condition, Big Temperature & Atmospheric Stats */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        {/* Left: Big Temperature Display + Weather Icon */}
        <div className="flex items-center gap-4">
          <div className="shrink-0 flex items-center justify-center">
            {selectedDayIndex === 0 ? (
              <svg viewBox="0 0 36 36" className="w-14 h-14 sm:w-16 sm:h-16 drop-shadow-xs">
                <path
                  fill="#2563eb"
                  d="M24.7 28.5C18 28.5 12.6 23.1 12.6 16.4c0-4.3 2.3-8.2 6-10.3-.4-.1-.8-.1-1.3-.1-7.7 0-14 6.3-14 14s6.3 14 14 14c4 0 7.7-1.7 10.3-4.5-1-.6-2-1-2.9-1z"
                />
              </svg>
            ) : (
              renderWeatherIcon(currentDay.condition, 'w-12 h-12')
            )}
          </div>

          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-5xl sm:text-6xl font-bold text-slate-900 tracking-tight font-sans">
                {currentTemp}
              </span>
              <div className="flex items-center text-sm font-semibold select-none">
                <button
                  type="button"
                  onClick={() => setUnit('C')}
                  className={`cursor-pointer transition-colors ${unit === 'C' ? 'font-bold text-blue-600' : 'text-slate-400 hover:text-slate-700'}`}
                >
                  °C
                </button>
                <span className="mx-1 text-slate-300">|</span>
                <button
                  type="button"
                  onClick={() => setUnit('F')}
                  className={`cursor-pointer transition-colors ${unit === 'F' ? 'font-bold text-blue-600' : 'text-slate-400 hover:text-slate-700'}`}
                >
                  °F
                </button>
              </div>
            </div>

            <div className="flex items-center gap-3 text-xs text-slate-600 mt-1 font-medium">
              <span>{language === 'pa' ? 'ਵਰਖਾ' : language === 'hi' ? 'वर्षा' : 'Rain'}: <strong className="text-slate-900">{currentHour.precipPct}%</strong></span>
              <span>•</span>
              <span>{language === 'pa' ? 'ਨਮੀ' : language === 'hi' ? 'आर्द्रता' : 'Humidity'}: <strong className="text-slate-900">90%</strong></span>
              <span>•</span>
              <span>{language === 'pa' ? 'ਹਵਾ' : language === 'hi' ? 'हवा' : 'Wind'}: <strong className="text-slate-900">{currentHour.windKmh} km/h</strong></span>
            </div>
          </div>
        </div>

        {/* Right: Title, Day/Time, Condition & Audio Speak Button */}
        <div className="flex flex-col sm:items-end text-left sm:text-right w-full sm:w-auto">
          <div className="flex items-center sm:justify-end gap-2">
            <h2 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight font-sans">
              {language === 'pa' ? 'ਅੱਜ ਦਾ ਮੌਸਮ' : language === 'hi' ? 'आज का मौसम' : "Today's Meteorological Conditions"}
            </h2>
            <button
              type="button"
              onClick={handleSpeakWeather}
              title="Hear Voice Forecast"
              aria-label="Hear Voice Forecast"
              className={`p-1.5 rounded-lg border transition-all flex items-center justify-center cursor-pointer ${
                isSpeaking
                  ? 'bg-blue-600 text-white border-blue-600 animate-pulse'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-200'
              }`}
            >
              {isSpeaking ? (
                <VolumeX className="w-4 h-4 text-white" />
              ) : (
                <Volume2 className="w-4 h-4 text-slate-600" />
              )}
            </button>
          </div>

          <div className="text-xs text-slate-500 font-medium mt-0.5">
            {dayLabel}, 2:00 am • <span className="font-semibold text-slate-800">{currentConditionText}</span>
          </div>
          <div className="text-[11px] text-slate-400 font-mono">
            {locationName}
          </div>
        </div>
      </div>

      {/* Weather Tabs: Temperature, Precipitation, Wind */}
      <div className="flex items-center gap-6 border-b border-slate-100 mt-3 text-xs select-none">
        <button
          type="button"
          onClick={() => setActiveTab('temp')}
          className={`pb-2 transition-colors cursor-pointer ${
            activeTab === 'temp'
              ? 'text-blue-600 font-bold border-b-2 border-blue-600'
              : 'text-slate-500 hover:text-slate-800 font-medium'
          }`}
        >
          {language === 'pa' ? 'ਤਾਪਮਾਨ' : language === 'hi' ? 'तापमान' : 'Temperature'}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('precip')}
          className={`pb-2 transition-colors cursor-pointer ${
            activeTab === 'precip'
              ? 'text-blue-600 font-bold border-b-2 border-blue-600'
              : 'text-slate-500 hover:text-slate-800 font-medium'
          }`}
        >
          {language === 'pa' ? 'ਵਰਖਾ' : language === 'hi' ? 'वर्षा' : 'Precipitation'}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('wind')}
          className={`pb-2 transition-colors cursor-pointer ${
            activeTab === 'wind'
              ? 'text-blue-600 font-bold border-b-2 border-blue-600'
              : 'text-slate-500 hover:text-slate-800 font-medium'
          }`}
        >
          {language === 'pa' ? 'ਹਵਾ' : language === 'hi' ? 'हवा' : 'Wind'}
        </button>
      </div>

      {/* Interactive Smooth Hourly Trend Chart */}
      <div className="mt-3 relative overflow-x-auto">
        <div className="min-w-[620px]">
          <svg
            viewBox={`0 0 ${chartWidth} ${chartHeight + 28}`}
            className="w-full h-32 overflow-visible"
          >
            <defs>
              <linearGradient id="curveGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={theme.fillStart} />
                <stop offset="100%" stopColor={theme.fillEnd} />
              </linearGradient>
            </defs>

            {/* Gradient Area Fill */}
            <path d={areaPath} fill="url(#curveGradient)" />

            {/* Baseline guideline */}
            <line
              x1="0"
              y1={chartHeight}
              x2={chartWidth}
              y2={chartHeight}
              stroke="#e2e8f0"
              strokeWidth="1"
            />

            {/* Smooth Bezier Curve Line */}
            <path
              d={linePath}
              fill="none"
              stroke={theme.stroke}
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Points & Numeric Labels */}
            {points.map((p, idx) => {
              const isHovered = hoveredHourIndex === idx;
              const unitLabel = activeTab === 'temp' ? '°' : activeTab === 'precip' ? '%' : 'k';

              return (
                <g
                  key={idx}
                  className="cursor-pointer"
                  onMouseEnter={() => setHoveredHourIndex(idx)}
                  onMouseLeave={() => setHoveredHourIndex(null)}
                >
                  {/* Point circle */}
                  <circle
                    cx={p.x}
                    cy={p.y}
                    r={isHovered ? 5 : 3.5}
                    fill={theme.dot}
                    stroke="#ffffff"
                    strokeWidth="1.5"
                    className="transition-all duration-150"
                  />

                  {/* Value label directly above dot */}
                  <text
                    x={p.x}
                    y={p.y - 8}
                    textAnchor="middle"
                    className={`text-[11px] font-bold fill-slate-800 transition-all ${isHovered ? 'text-xs font-black fill-blue-600' : ''}`}
                  >
                    {p.val}{unitLabel}
                  </text>

                  {/* Time label below chart */}
                  <text
                    x={p.x}
                    y={chartHeight + 18}
                    textAnchor="middle"
                    className="text-[10px] font-medium fill-slate-500"
                  >
                    {language === 'pa'
                      ? p.hour.timeLabelPa
                      : language === 'hi'
                      ? p.hour.timeLabelHi
                      : p.hour.time}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </div>

      {/* 8-Day Forecast Strip: Logo Blue highlight for selected day */}
      <div className="mt-4 pt-3 border-t border-slate-100">
        <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
          {forecastDays.map((fDay, idx) => {
            const isSelected = selectedDayIndex === idx;
            const high = unit === 'C' ? fDay.highC : fDay.highF;
            const low = unit === 'C' ? fDay.lowC : fDay.lowF;
            const dayText =
              language === 'pa'
                ? fDay.dayPa
                : language === 'hi'
                ? fDay.dayHi
                : fDay.dayName;

            return (
              <button
                key={idx}
                type="button"
                onClick={() => setSelectedDayIndex(idx)}
                className={`py-2 px-1 rounded-xl flex flex-col items-center justify-between text-center cursor-pointer select-none transition-all duration-200 transform hover:scale-105 hover:-translate-y-1 hover:shadow-lg active:scale-95 ${
                  isSelected
                    ? 'bg-blue-600 text-white shadow-md border border-blue-600 z-10'
                    : 'bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-800'
                }`}
              >
                <span className={`text-[11px] font-bold uppercase tracking-wider ${isSelected ? 'text-white' : 'text-slate-600'}`}>
                  {dayText}
                </span>

                <div className="my-1">
                  {renderWeatherIcon(fDay.condition, isSelected ? 'w-6 h-6' : 'w-5 h-5')}
                </div>

                <div className="text-[11px] font-medium">
                  <span className={isSelected ? 'text-white font-extrabold' : 'text-slate-900 font-bold'}>
                    {high}°
                  </span>{' '}
                  <span className={isSelected ? 'text-blue-100' : 'text-slate-400'}>
                    {low}°
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
