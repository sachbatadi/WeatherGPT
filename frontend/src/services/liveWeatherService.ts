/**
 * Live Meteorological Telemetry Service (Open-Meteo API)
 * Provides real-time weather observations and 7-day forecasts
 * Free, public API with CORS enabled — requires no API key.
 */

export interface HourlyForecastItem {
  time: string;
  timeLabelPa: string;
  timeLabelHi: string;
  tempC: number;
  tempF: number;
  precipPct: number;
  windKmh: number;
  condition: 'clear' | 'cloudy' | 'rain' | 'thunder' | 'partlyCloudy';
}

export interface DailyForecastItem {
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
  hourly: HourlyForecastItem[];
}

export interface LiveWeatherData {
  locationName: string;
  currentTempC: number;
  currentTempF: number;
  humidityPct: number;
  precipPct: number;
  windKmh: number;
  condition: 'clear' | 'cloudy' | 'rain' | 'thunder' | 'partlyCloudy';
  conditionTextEn: string;
  conditionTextPa: string;
  conditionTextHi: string;
  forecastDays: DailyForecastItem[];
  lastUpdated: string;
  isLive: boolean;
}

// Known coordinates for Punjab districts
export const DISTRICT_COORDINATES: Record<string, { lat: number; lon: number; name: string }> = {
  'Patiala, Punjab': { lat: 30.3398, lon: 76.3869, name: 'Patiala' },
  'Jalandhar (Doaba)': { lat: 31.3260, lon: 75.5762, name: 'Jalandhar' },
  'Ludhiana Central': { lat: 30.9010, lon: 75.8573, name: 'Ludhiana' },
  'Hoshiarpur Foothills': { lat: 31.5273, lon: 75.9149, name: 'Hoshiarpur' },
  'Kapurthala Riverine': { lat: 31.3800, lon: 75.3800, name: 'Kapurthala' },
  'Bathinda Cotton Belt': { lat: 30.2110, lon: 74.9455, name: 'Bathinda' },
};

function mapWmoToCondition(code: number): {
  condition: 'clear' | 'cloudy' | 'rain' | 'thunder' | 'partlyCloudy';
  en: string;
  pa: string;
  hi: string;
} {
  if (code === 0) {
    return { condition: 'clear', en: 'Clear & Sunny', pa: 'ਸਾਫ਼ ਧੁੱਪ', hi: 'साफ धूप' };
  }
  if (code === 1 || code === 2) {
    return { condition: 'partlyCloudy', en: 'Partly Cloudy', pa: 'ਅੰਸ਼ਕ ਬੱਦਲਵਾਈ', hi: 'आंशिक बादल' };
  }
  if (code === 3 || code === 45 || code === 48) {
    return { condition: 'cloudy', en: 'Cloudy', pa: 'ਬੱਦਲਵਾਈ', hi: 'बादल छाए' };
  }
  if ([51, 53, 55, 61, 63, 65, 80, 81, 82].includes(code)) {
    return { condition: 'rain', en: 'Rain Showers', pa: 'ਮੀਂਹ ਦੀਆਂ ਬੁਛਾੜਾਂ', hi: 'वर्षा बौछारें' };
  }
  if ([95, 96, 99].includes(code)) {
    return { condition: 'thunder', en: 'Thunderstorm', pa: 'ਗਰਜ ਨਾਲ ਮੀਂਹ', hi: 'गरज के साथ वर्षा' };
  }
  return { condition: 'partlyCloudy', en: 'Scattered Clouds', pa: 'ਬੱਦਲਵਾਈ', hi: 'बादल' };
}

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const DAY_NAMES_PA: Record<string, string> = {
  Sun: 'ਐਤ',
  Mon: 'ਸੋਮ',
  Tue: 'ਮੰਗਲ',
  Wed: 'ਬੁੱਧ',
  Thu: 'ਵੀਰ',
  Fri: 'ਸ਼ੁੱਕਰ',
  Sat: 'ਸ਼ਨੀ',
};
const DAY_NAMES_HI: Record<string, string> = {
  Sun: 'रवि',
  Mon: 'सोम',
  Tue: 'मंगल',
  Wed: 'बुध',
  Thu: 'गुरु',
  Fri: 'शुक्र',
  Sat: 'शनि',
};

// In-memory cache for 5-minute validity
const weatherCache = new Map<string, { data: LiveWeatherData; expiresAt: number }>();

export async function fetchLiveWeatherData(locationName = 'Patiala, Punjab'): Promise<LiveWeatherData> {
  const cacheKey = locationName.trim();
  const cached = weatherCache.get(cacheKey);
  const now = Date.now();

  if (cached && cached.expiresAt > now) {
    return cached.data;
  }

  const coords = DISTRICT_COORDINATES[locationName] || { lat: 30.3398, lon: 76.3869, name: locationName };

  try {
    const url = 'https://api.open-meteo.com/v1/forecast?latitude=' + coords.lat + '&longitude=' + coords.lon + '&current_weather=true&hourly=temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=auto';

    const res = await fetch(url);
    if (!res.ok) {
      throw new Error('Open-Meteo HTTP error: ' + res.status);
    }

    const json = await res.json();
    const curr = json.current_weather || {};
    const hourly = json.hourly || {};
    const daily = json.daily || {};

    const currentWmo = mapWmoToCondition(curr.weathercode ?? 0);
    const currentTempC = Math.round(curr.temperature ?? 28);
    const currentTempF = Math.round((currentTempC * 9) / 5 + 32);
    const windKmh = Math.round(curr.windspeed ?? 8);

    const humidityPct = Math.round(hourly.relative_humidity_2m?.[0] ?? 75);
    const precipPct = Math.round(hourly.precipitation_probability?.[0] ?? 10);

    const forecastDays: DailyForecastItem[] = [];
    const dailyTimes: string[] = daily.time || [];
    const maxTemps: number[] = daily.temperature_2m_max || [];
    const minTemps: number[] = daily.temperature_2m_min || [];
    const weatherCodes: number[] = daily.weather_code || [];

    for (let i = 0; i < Math.min(dailyTimes.length, 8); i++) {
      const dateObj = new Date(dailyTimes[i]);
      const dayName = DAY_NAMES[dateObj.getDay()];
      const highC = Math.round(maxTemps[i] ?? 32);
      const lowC = Math.round(minTemps[i] ?? 22);
      const cond = mapWmoToCondition(weatherCodes[i] ?? 0);

      const dayHourlyHours = [3, 6, 9, 12, 15, 18, 21, 24];
      const hourlyItems: HourlyForecastItem[] = dayHourlyHours.map((h) => {
        const globalIdx = i * 24 + (h === 24 ? 23 : h);
        const temp = Math.round(hourly.temperature_2m?.[globalIdx] ?? (lowC + (highC - lowC) * (h >= 12 && h <= 15 ? 1 : 0.4)));
        const rainChance = Math.round(hourly.precipitation_probability?.[globalIdx] ?? (cond.condition === 'rain' ? 45 : 5));
        const wSpeed = Math.round(hourly.wind_speed_10m?.[globalIdx] ?? 10);
        const hourWmo = mapWmoToCondition(hourly.weather_code?.[globalIdx] ?? weatherCodes[i] ?? 0);

        const timeLabel = h === 12 ? '12 pm' : h === 24 ? '12 am' : h < 12 ? h + ' am' : (h - 12) + ' pm';
        const timeLabelPa = h === 12 ? '12 ਦੁਪਹਿਰ' : h === 24 ? '12 ਰਾਤ' : h < 12 ? h + ' ਸਵੇਰੇ' : (h - 12) + ' ਸ਼ਾਮ';
        const timeLabelHi = h === 12 ? '12 दोपहर' : h === 24 ? '12 रात' : h < 12 ? h + ' पूर्वाह्न' : (h - 12) + ' अपराह्न';

        return {
          time: timeLabel,
          timeLabelPa,
          timeLabelHi,
          tempC: temp,
          tempF: Math.round((temp * 9) / 5 + 32),
          precipPct: rainChance,
          windKmh: wSpeed,
          condition: hourWmo.condition,
        };
      });

      forecastDays.push({
        dayName,
        dayPa: DAY_NAMES_PA[dayName] || dayName,
        dayHi: DAY_NAMES_HI[dayName] || dayName,
        highC,
        lowC,
        highF: Math.round((highC * 9) / 5 + 32),
        lowF: Math.round((lowC * 9) / 5 + 32),
        condition: cond.condition,
        conditionTextEn: cond.en,
        conditionTextPa: cond.pa,
        conditionTextHi: cond.hi,
        hourly: hourlyItems,
      });
    }

    const liveData: LiveWeatherData = {
      locationName,
      currentTempC,
      currentTempF,
      humidityPct,
      precipPct,
      windKmh,
      condition: currentWmo.condition,
      conditionTextEn: currentWmo.en,
      conditionTextPa: currentWmo.pa,
      conditionTextHi: currentWmo.hi,
      forecastDays: forecastDays.length > 0 ? forecastDays : getFallbackForecast(locationName),
      lastUpdated: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isLive: true,
    };

    weatherCache.set(cacheKey, { data: liveData, expiresAt: now + 5 * 60 * 1000 });
    return liveData;
  } catch (err) {
    console.warn('[LiveWeather] Using fallback for ' + locationName, err);
    return {
      locationName,
      currentTempC: 28,
      currentTempF: 82,
      humidityPct: 85,
      precipPct: 15,
      windKmh: 10,
      condition: 'partlyCloudy',
      conditionTextEn: 'Partly Cloudy',
      conditionTextPa: 'ਅੰਸ਼ਕ ਬੱਦਲਵਾਈ',
      conditionTextHi: 'आंशिक बादल',
      forecastDays: getFallbackForecast(locationName),
      lastUpdated: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isLive: false,
    };
  }
}

function getFallbackForecast(location: string): DailyForecastItem[] {
  const days = ['Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'Mon', 'Tue', 'Wed'];
  return days.map((day, idx) => ({
    dayName: day,
    dayPa: DAY_NAMES_PA[day] || day,
    dayHi: DAY_NAMES_HI[day] || day,
    highC: 32 + (idx % 3),
    lowC: 23 + (idx % 2),
    highF: 90 + (idx % 4),
    lowF: 73 + (idx % 3),
    condition: idx % 2 === 0 ? 'clear' : 'partlyCloudy',
    conditionTextEn: idx % 2 === 0 ? 'Clear & Sunny' : 'Partly Cloudy',
    conditionTextPa: idx % 2 === 0 ? 'ਸਾਫ਼ ਧੁੱਪ' : 'ਅੰਸ਼ਕ ਬੱਦਲਵਾਈ',
    conditionTextHi: idx % 2 === 0 ? 'साफ धूप' : 'आंशिक बादल',
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
  }));
}
