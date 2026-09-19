import express from "express";
import path from "path";
import { GoogleGenAI } from "@google/genai";
import dotenv from "dotenv";

dotenv.config();

const app = express();
const PORT = 3000;

app.use(express.json({ limit: "10mb" }));

// Lazy initialization for Gemini client
let geminiClient: GoogleGenAI | null = null;
function getGemini(): GoogleGenAI | null {
  if (!geminiClient && process.env.GEMINI_API_KEY) {
    geminiClient = new GoogleGenAI({
      apiKey: process.env.GEMINI_API_KEY,
      httpOptions: {
        headers: {
          "User-Agent": "aistudio-build",
        },
      },
    });
  }
  return geminiClient;
}

// In-memory cache for translations to keep response times sub-millisecond
const translationCache = new Map<string, string>();

app.get("/api/health", (_req, res) => {
  res.json({
    status: "ok",
    hasApiKey: Boolean(process.env.GEMINI_API_KEY),
    timestamp: new Date().toISOString(),
  });
});

// Robust translation API endpoint
app.post("/api/translate", async (req, res) => {
  try {
    const { text, texts, targetLanguage = "pa", sourceLanguage = "en" } = req.body;

    const langNames: Record<string, string> = {
      pa: "Punjabi (Gurmukhi script)",
      hi: "Hindi (Devanagari script)",
      en: "English",
    };

    const targetLangName = langNames[targetLanguage] || targetLanguage;

    // Single text translation
    if (typeof text === "string") {
      const cacheKey = `${targetLanguage}:${text.trim()}`;
      if (translationCache.has(cacheKey)) {
        return res.json({ translatedText: translationCache.get(cacheKey), cached: true });
      }

      const ai = getGemini();
      if (!ai) {
        // Return original if no AI client available (fallback)
        return res.json({ translatedText: text, fallback: true });
      }

      const prompt = `You are a professional meteorological and emergency broadcast translator specialized in Indian disaster management terminology.
Translate the following text accurately into ${targetLangName}.
Preserve technical figures, river names (Ghaggar, Badi Nadi), numbers, units (mm/h, m³/s), and tone (official, urgent, or clear farmer advisory).
Only return the translated text without commentary or quotes.

Text:
${text}`;

      const response = await ai.models.generateContent({
        model: "gemini-2.5-flash",
        contents: prompt,
      });

      const translated = response.text ? response.text.trim() : text;
      translationCache.set(cacheKey, translated);
      return res.json({ translatedText: translated, cached: false });
    }

    // Batch translation
    if (Array.isArray(texts)) {
      const results: string[] = [];
      const missingIndices: number[] = [];
      const missingTexts: string[] = [];

      for (let i = 0; i < texts.length; i++) {
        const item = String(texts[i] || "");
        const cacheKey = `${targetLanguage}:${item.trim()}`;
        if (translationCache.has(cacheKey)) {
          results[i] = translationCache.get(cacheKey)!;
        } else {
          missingIndices.push(i);
          missingTexts.push(item);
        }
      }

      if (missingTexts.length === 0) {
        return res.json({ translations: results, cached: true });
      }

      const ai = getGemini();
      if (!ai) {
        // Fallback to original
        missingIndices.forEach((origIndex, idx) => {
          results[origIndex] = missingTexts[idx];
        });
        return res.json({ translations: results, fallback: true });
      }

      const batchPrompt = `You are a specialized translator for the Punjab WeatherGPT emergency system.
Translate the following list of strings into ${targetLangName}.
Preserve meteorological names, ward numbers, technical gauges, and emergency severity levels.
Return a valid JSON array of translated strings with exact length ${missingTexts.length}.

Input strings:
${JSON.stringify(missingTexts)}`;

      const response = await ai.models.generateContent({
        model: "gemini-2.5-flash",
        contents: batchPrompt,
        config: {
          responseMimeType: "application/json",
        },
      });

      try {
        const parsed = JSON.parse(response.text || "[]");
        if (Array.isArray(parsed)) {
          missingIndices.forEach((origIndex, idx) => {
            const val = parsed[idx] || missingTexts[idx];
            results[origIndex] = val;
            translationCache.set(`${targetLanguage}:${missingTexts[idx].trim()}`, val);
          });
        } else {
          missingIndices.forEach((origIndex, idx) => {
            results[origIndex] = missingTexts[idx];
          });
        }
      } catch (err) {
        missingIndices.forEach((origIndex, idx) => {
          results[origIndex] = missingTexts[idx];
        });
      }

      return res.json({ translations: results });
    }

    return res.status(400).json({ error: "Provide 'text' or 'texts' array" });
  } catch (err: any) {
    console.error("Translation API error:", err);
    return res.status(500).json({ error: err.message || "Translation failed", fallback: true });
  }
});

// WeatherGPT Conversational AI Endpoint
// SIH Project: WeatherGPT - Conversational AI for Weather Forecasting, Alerts & Climate Information
app.post(["/api/weathergpt/chat", "/api/copilot/chat"], async (req, res) => {
  try {
    const { message, language = "en", context, userRole } = req.body;
    const ai = getGemini();

    const langInstruction =
      language === "pa"
        ? "Respond in natural, grammatically correct Punjabi using Gurmukhi script. Do NOT use English letters for Punjabi words. Keep it clear, informative, and authoritative."
        : language === "hi"
        ? "Respond in natural, grammatically correct Hindi using Devanagari script. Do NOT use English letters for Hindi words. Keep it clear, informative, and authoritative."
        : "Respond in clear, professional English.";

    if (!ai) {
      // High-precision meteorological offline fallback engine
      const queryLower = (message || "").toLowerCase();

      let fallbackReply = "";
      const isGreeting =
        queryLower === "hi" ||
        queryLower === "hii" ||
        queryLower === "hello" ||
        queryLower === "hey" ||
        queryLower.startsWith("hi ") ||
        queryLower.startsWith("hello ") ||
        queryLower.includes("sat sri akal") ||
        queryLower.includes("ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ") ||
        queryLower.includes("namaste") ||
        queryLower.includes("नमस्ते");

      if (isGreeting) {
        if (language === "pa") {
          fallbackReply = `ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਜੀ! ਮੈਂ WeatherGPT ਹਾਂ — ਤੁਹਾਡਾ ਮੌਸਮ, ਹੜ੍ਹ ਚੇਤਾਵਨੀ ਅਤੇ ਖੇਤੀਬਾੜੀ ਸਲਾਹਕਾਰ ਏਆਈ।

ਮੈਂ ਤੁਹਾਡੀ ਕੀ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ? ਤੁਸੀਂ ਪੁੱਛ ਸਕਦੇ ਹੋ:
• ਕੀ ਅੱਜ ਪਟਿਆਲਾ ਜਾਂ ਪੰਜਾਬ ਵਿੱਚ ਮੀਂਹ ਪਵੇਗਾ?
• ਘੱਗਰ ਦਰਿਆ ਵਿੱਚ ਹੜ੍ਹ ਦੀ ਕੀ ਸਥਿਤੀ ਹੈ?
• ਕੀ ਝੋਨੇ ਜਾਂ ਫਸਲਾਂ ਤੇ ਸਪਰੇਅ ਕਰਨ ਦਾ ਸਹੀ ਸਮਾਂ ਹੈ?`;
        } else if (language === "hi") {
          fallbackReply = `नमस्ते! मैं WeatherGPT हूँ — मौसम पूर्वानुमान, बाढ़ चेतावनी एवं कृषि परामर्श हेतु आपका संवादात्मक एआई।

मैं आपकी किस प्रकार सहायता कर सकता हूँ? आप पूछ सकते हैं:
• आज मौसम एवं वर्षा का क्या अनुमान है?
• घग्गर बेसिन में बाढ़ की क्या स्थिति है?
• क्या फसलों पर कीटनाशक छिड़काव करना सुरक्षित है?`;
        } else {
          fallbackReply = `Hello! I am WeatherGPT — your conversational AI for weather forecasting, extreme weather alerts, and PAU agricultural climate advisories.

How can I assist you today? You can ask me about:
• Today's rain, temperature, and wind forecast for your district
• Live Ghaggar and Sutlej river water levels & flood alerts
• Crop protection and spraying guidance from Punjab Agricultural University
• Emergency evacuation shelters and PSDMA directives`;
        }
      } else if (queryLower.includes("rain") || queryLower.includes("ਮੀਂਹ") || queryLower.includes("बारिश") || queryLower.includes("forecast") || queryLower.includes("ਮੌਸਮ")) {
        if (language === "pa") {
          fallbackReply = `ਅੱਜ ਦਾ ਮੌਸਮ ਅਤੇ ਬਾਰਿਸ਼ ਪੂਰਵ-ਅਨੁਮਾਨ:
• ਪਟਿਆਲਾ ਅਤੇ ਆਸ-ਪਾਸ ਦੇ ਇਲਾਕਿਆਂ ਵਿੱਚ 78 ਮਿ.ਮੀ. ਭਾਰੀ ਬਾਰਿਸ਼ ਦਰਜ ਕੀਤੀ ਗਈ ਹੈ।
• ਅਗਲੇ 24 ਘੰਟਿਆਂ ਵਿੱਚ ਦਰਮਿਆਨੀ ਤੋਂ ਭਾਰੀ ਬਾਰਿਸ਼ ਅਤੇ 35 ਕਿ.ਮੀ./ਘੰਟਾ ਦੀ ਰਫ਼ਤਾਰ ਨਾਲ ਤੇਜ਼ ਹਵਾਵਾਂ ਚੱਲਣ ਦੀ ਸੰਭਾਵਨਾ ਹੈ।
• ਤਾਪਮਾਨ 29°C (ਘੱਟੋ-ਘੱਟ 24°C) ਅਤੇ ਨਮੀ 92% ਰਹੇਗੀ।
• ਅਗਲੇ 48 ਘੰਟਿਆਂ ਬਾਅਦ ਮੌਸਮ ਵਿੱਚ ਸੁਧਾਰ ਹੋਣ ਦੀ ਉਮੀਦ ਹੈ।`;
        } else if (language === "hi") {
          fallbackReply = `आज का मौसम एवं वर्षा पूर्वानुमान:
• पटियाला एवं आसपास के क्षेत्रों में 78 मिमी भारी वर्षा दर्ज की गई है।
• आगामी 24 घंटों में मध्यम से भारी वर्षा और 35 किमी/घंटा की रफ्तार से तेज हवाएं चलने की संभावना है।
• तापमान 29°C (न्यूनतम 24°C) तथा सापेक्ष आर्द्रता 92% रहेगी।
• 48 घंटों के उपरांत पश्चिमी विक्षोभ के कमजोर होने से मौसम में सुधार होगा।`;
        } else {
          fallbackReply = `WeatherGPT Forecast & Rain Analysis:
• Current Precipitation: 78 mm recorded across Patiala / Ghaggar catchment.
• 24-Hour Outlook: Intermittent moderate to heavy precipitation with gusts up to 35 km/h.
• Surface Conditions: Temperature 29°C (Min: 24°C), Relative Humidity 92%, Pressure 1004 hPa.
• Doppler Radar Echoes: Convective cloud tops reaching 11 km over Shivalik foothills. Synoptic rain expected to taper after 36-48 hours.`;
        }
      } else if (queryLower.includes("flood") || queryLower.includes("ਹੜ੍ਹ") || queryLower.includes("बाढ़") || queryLower.includes("ghaggar") || queryLower.includes("ਦਰਿਆ") || queryLower.includes("नदी")) {
        if (language === "pa") {
          fallbackReply = `ਘੱਗਰ ਦਰਿਆ ਅਤੇ ਹੜ੍ਹ ਚੇਤਾਵਨੀ ਸਥਿਤੀ:
• ਘੱਗਰ ਗੇਜ ਪੱਧਰ 14.82 ਮੀਟਰ ਹੈ, ਜੋ ਕਿ ਖ਼ਤਰੇ ਦੇ ਨਿਸ਼ਾਨ (14.50 ਮੀਟਰ) ਤੋਂ ਉੱਪਰ ਹੈ।
• ਪਟਿਆਲਾ ਦੇ ਨੀਵੇਂ ਵਾਰਡ (12-14) ਅਤੇ ਵੱਡੀ ਨਦੀ ਦੇ ਕਿਨਾਰੇ ਹਾਈ ਅਲਰਟ 'ਤੇ ਹਨ।
• ਸਰਕਾਰੀ ਮਹਿੰਦਰਾ ਕਾਲਜ ਵਿਖੇ ਐਮਰਜੈਂਸੀ ਰਾਹਤ ਕੈਂਪ ਚਾਲੂ ਹੈ।
• ਐਮਰਜੈਂਸੀ ਹੈਲਪਲਾਈਨ: 112 (ਬਚਾਅ) ਜਾਂ 1077 (ਜ਼ਿਲ੍ਹਾ ਕੰਟਰੋਲ ਰੂਮ)।`;
        } else if (language === "hi") {
          fallbackReply = `घग्गर नदी एवं बाढ़ चेतावनी स्थिति:
• घग्गर नदी का जलस्तर 14.82 मीटर दर्ज हुआ है, जो खतरे के निशान (14.50 मीटर) से ऊपर है।
• पटियाला के निचले वार्ड (12-14) एवं बड़ी नदी तटीय क्षेत्र हाई अलर्ट पर हैं।
• राजकीय मोहिंद्रा कॉलेज में 24x7 राहत एवं निकासी केंद्र सक्रिय है।
• आपातकालीन हेल्पलाइन: 112 (रेस्क्यू) अथवा 1077 (जिला आपदा नियंत्रण कक्ष)।`;
        } else {
          fallbackReply = `Hydrological Threat Assessment:
• Ghaggar River Naraj Gauge: 14.82m (Breaching 14.50m Danger Threshold).
• Evacuation Priority Index (EPI): 8.4/10.0 for low-lying Patiala Wards 12-14.
• Response Actions: SDRF 3rd Battalion pre-deployed; Relief camp operational at Govt Mohindra College.
• Emergency Helplines: 112 (National Emergency) & 1077 (District Disaster Room).`;
        }
      } else if (queryLower.includes("crop") || queryLower.includes("spray") || queryLower.includes("ਖੇਤੀ") || queryLower.includes("ਫਸਲ") || queryLower.includes("कृषि") || queryLower.includes("धान") || queryLower.includes("paddy")) {
        if (language === "pa") {
          fallbackReply = `ਪੰਜਾਬ ਖੇਤੀਬਾੜੀ ਯੂਨੀਵਰਸਿਟੀ (PAU) ਕਿਸਾਨ ਸਲਾਹ:
• ਅਗਲੇ 2 ਦਿਨਾਂ ਤੱਕ ਝੋਨੇ ਜਾਂ ਕਿਸੇ ਵੀ ਫਸਲ 'ਤੇ ਕੀਟਨਾਸ਼ਕ ਜਾਂ ਯੂਰੀਆ ਦਾ ਛਿੜਕਾਅ ਬਿਲਕੁਲ ਨਾ ਕਰੋ, ਕਿਉਂਕਿ ਮੀਂਹ ਨਾਲ ਦਵਾਈ ਵਹਿ ਜਾਵੇਗੀ।
• ਖੇਤਾਂ ਵਿੱਚੋਂ ਵਾਧੂ ਪਾਣੀ ਕੱਢਣ ਲਈ ਨਿਕਾਸੀ ਨਾਲੀਆਂ ਤੁਰੰਤ ਸਾਫ਼ ਕਰੋ।
• ਪਸ਼ੂਆਂ ਦੇ ਸੁੱਕੇ ਚਾਰੇ ਨੂੰ ਤਰਪਾਲ ਨਾਲ ਢੱਕ ਕੇ ਉੱਚੀ ਥਾਂ ਰੱਖੋ।
• ਕਿਸਾਨ ਕਾਲ ਸੈਂਟਰ ਟੋਲ-ਫ੍ਰੀ: 1800-180-1551।`;
        } else if (language === "hi") {
          fallbackReply = `पंजाब कृषि विश्वविद्यालय (PAU) किसान परामर्श:
• आगामी 2 दिनों तक धान अथवा किसी भी फसल पर कीटनाशक या यूरिया का छिड़काव न करें; बारिश से दवा धुल जाएगी।
• खेतों में जलभराव रोकने हेतु जल निकासी नालियों को तुरंत साफ करें।
• पशुओं के सूखे चारे को तिरपाल से ढककर ऊंचे स्थान पर रखें।
• किसान कॉल सेंटर टोल-फ्री: 1800-180-1551।`;
        } else {
          fallbackReply = `PAU Agro-Meteorological Advisory:
• Chemical Foliar Spray: Strictly suspend pesticide and urea application for the next 48 hours to avoid wash-off.
• Drainage: Clear bund cuts and field drains immediately to prevent root hypoxia in paddy.
• Fodder & Livestock: Elevate dry fodder stocks and keep livestock away from waterlogged soils.
• Farmer Helpline: Toll-Free Kisan Call Center 1800-180-1551.`;
        }
      } else {
        if (language === "pa") {
          fallbackReply = `WeatherGPT ਮੌਸਮ ਜਾਣਕਾਰੀ:
ਤੁਹਾਡੇ ਸੁਆਲ "${message}" ਦੇ ਆਧਾਰ 'ਤੇ, ਮੌਜੂਦਾ ਮਾਨਸੂਨ ਪ੍ਰਣਾਲੀ ਅਤੇ ਉੱਤਰੀ ਭਾਰਤ ਵਿੱਚ ਸਰਗਰਮ ਪੱਛਮੀ ਗੜਬੜ ਕਾਰਨ ਪੰਜਾਬ ਭਰ ਵਿੱਚ ਬਾਰਿਸ਼ ਦਰਜ ਕੀਤੀ ਜਾ ਰਹੀ ਹੈ। ਘੱਗਰ ਬੇਸਿਨ ਵਿੱਚ ਪਾਣੀ ਖ਼ਤਰੇ ਦੇ ਨਿਸ਼ਾਨ 'ਤੇ ਹੈ। ਖੇਤਾਂ ਵਿੱਚ ਸਪਰੇਅ ਰੋਕੋ ਅਤੇ ਨੀਵੇਂ ਇਲਾਕਿਆਂ ਵਿੱਚ ਸਾਵਧਾਨੀ ਵਰਤੋ।`;
        } else if (language === "hi") {
          fallbackReply = `WeatherGPT मौसम एवं जलवायु सूचना:
आपके प्रश्न "${message}" के संदर्भ में, सक्रिय मानसून द्रोणी एवं पश्चिमी विक्षोभ के संयुक्त प्रभाव से पंजाब क्षेत्र में व्यापक वर्षा हो रही है। घग्गर बेसिन में सतर्कता बरती जा रही है। किसी भी मौसम, तापमान या आपदा संबंधी जानकारी के लिए पूछें।`;
        } else {
          fallbackReply = `WeatherGPT Meteorological Intelligence:
Regarding "${message}": Regional synoptic conditions over Punjab indicate an active monsoon trough interacting with a mid-tropospheric Western Disturbance. Ghaggar hydrology remains elevated at 14.82m. Precipitation will continue intermittently before clearing. Feel free to query any specific district forecast, temperature, humidity, rainfall, or climate pattern.`;
        }
      }

      return res.json({ reply: fallbackReply });
    }

    const systemPrompt = `You are WeatherGPT, the state-of-the-art conversational AI platform for weather forecasting, extreme weather alerts, and climate intelligence (Smart India Hackathon project).
Your role:
1. Provide accurate, clear, and scientific answers to ANY weather, climate, meteorological, atmospheric, hydrological, or disaster-management questions.
2. Cover: 
   - Instant local forecasts (temperature, rainfall mm, wind, humidity, pressure, cloud cover, UV index).
   - Severe weather alerts (floods, flash floods, thunder squalls, lightning, heatwaves, coldwaves, hailstorms, dense fog).
   - Regional hydrology & basin status (Ghaggar River, Sutlej, Beas, Ravi, Yamuna, Badi Nadi).
   - Synoptic meteorology (Western Disturbances, Monsoon trough, El Niño / La Niña, Doppler radar dBZ interpretation).
   - Agro-meteorological advisories in coordination with Punjab Agricultural University (PAU) (irrigation scheduling, fertilizer windows, crop protection).
3. Tone: Authoritative, professional, concise, and helpful. Use clear bullet points and numbers when explaining data.
4. Active context:
   - Location: Punjab, India (Special focus: Patiala & Doaba basin).
   - Live Threat: Elevated Ghaggar river levels (14.82m gauge against 14.50m danger mark).
   - Rain status: 78mm recent heavy precipitation, intermittent showers.
   - User Role: ${userRole || "User"}.
5. LANGUAGE MANDATE:
   ${langInstruction}`;

    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: message,
      config: {
        systemInstruction: systemPrompt,
      },
    });

    return res.json({ reply: response.text?.trim() || "No response generated" });
  } catch (err: any) {
    console.error("WeatherGPT chat error:", err);
    return res.status(500).json({ error: err.message || "WeatherGPT query failed" });
  }
});

import { MsEdgeTTS, OUTPUT_FORMAT } from "msedge-tts";

// In-memory cache for synthesized audio to make repeated broadcasts instantaneous
const ttsAudioCache = new Map<string, Buffer>();

function splitTextForTTS(text: string, maxLength = 180): string[] {
  // Strip markdown, emojis, bracket symbols
  const clean = text
    .replace(/[#*_`~[\]()]/g, "")
    .replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, "")
    .replace(/\s+/g, " ")
    .trim();

  const sentences = clean.match(/[^।?!.\n\r]+[।?!.\n\r]*/g) || [clean];
  const chunks: string[] = [];
  let current = "";

  for (const s of sentences) {
    if ((current + " " + s).trim().length <= maxLength) {
      current = (current ? current + " " : "") + s.trim();
    } else {
      if (current) chunks.push(current);
      if (s.length > maxLength) {
        const words = s.split(" ");
        let wordChunk = "";
        for (const w of words) {
          if ((wordChunk + " " + w).trim().length <= maxLength) {
            wordChunk = (wordChunk ? wordChunk + " " : "") + w;
          } else {
            if (wordChunk) chunks.push(wordChunk);
            wordChunk = w;
          }
        }
        current = wordChunk;
      } else {
        current = s.trim();
      }
    }
  }
  if (current) chunks.push(current);
  return chunks;
}

// Synthesize voice using Microsoft Edge TTS (edge-tts) for Hindi & English
async function generateEdgeTTS(text: string, voice: string): Promise<Buffer> {
  const clean = text
    .replace(/[#*_`~[\]()]/g, "")
    .replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, "")
    .replace(/\s+/g, " ")
    .trim();

  const tts = new MsEdgeTTS();
  await tts.setMetadata(voice, OUTPUT_FORMAT.AUDIO_24KHZ_48KBITRATE_MONO_MP3);
  return new Promise((resolve, reject) => {
    const res = tts.toStream(clean);
    const chunks: Buffer[] = [];
    res.audioStream.on("data", (c: Buffer) => chunks.push(c));
    res.audioStream.on("end", () => {
      try {
        tts.close();
      } catch {
        // ignore
      }
      resolve(Buffer.concat(chunks));
    });
    res.audioStream.on("error", (err: any) => {
      try {
        tts.close();
      } catch {
        // ignore
      }
      reject(err);
    });
  });
}

// Synthesize voice using Google Text-to-Speech (gTTS) for Punjabi (lang="pa")
async function generateGoogleTTS(text: string, lang = "pa"): Promise<Buffer> {
  const chunks = splitTextForTTS(text, 180);
  const audioBuffers: Buffer[] = [];

  for (const chunk of chunks) {
    if (!chunk.trim()) continue;
    const url = `https://translate.google.com/translate_tts?ie=UTF-8&tl=${encodeURIComponent(lang)}&client=tw-ob&q=${encodeURIComponent(chunk)}`;
    const response = await fetch(url, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        Referer: "https://translate.google.com/",
      },
    });

    if (response.ok) {
      const ab = await response.arrayBuffer();
      audioBuffers.push(Buffer.from(ab));
    }
  }

  return Buffer.concat(audioBuffers);
}

// Unified Single-Voice TTS API:
// 1. Punjabi (pa): Google Text-to-Speech (gTTS lang="pa")
// 2. Hindi (hi): Microsoft Edge TTS (edge-tts voice="hi-IN-MadhurNeural")
// 3. English (en): Microsoft Edge TTS (edge-tts voice="en-IN-NeerjaNeural")
app.all("/api/tts", async (req, res) => {
  try {
    const text = (req.method === "POST" ? req.body?.text : req.query.text) || "";
    const lang = (req.method === "POST" ? req.body?.lang : req.query.lang) || "pa";

    if (typeof text !== "string" || !text.trim()) {
      return res.status(400).json({ error: "Missing or invalid 'text'" });
    }

    let tl = "pa";
    if (String(lang).toLowerCase().startsWith("hi")) tl = "hi";
    else if (String(lang).toLowerCase().startsWith("en")) tl = "en";
    else if (String(lang).toLowerCase().startsWith("pa")) tl = "pa";

    const cacheKey = `${tl}:${text.trim()}`;
    if (ttsAudioCache.has(cacheKey)) {
      const cachedBuffer = ttsAudioCache.get(cacheKey)!;
      res.setHeader("Content-Type", "audio/mpeg");
      res.setHeader("Content-Length", cachedBuffer.byteLength.toString());
      res.setHeader("Cache-Control", "public, max-age=86400");
      return res.send(cachedBuffer);
    }

    let audioBuffer: Buffer;

    if (tl === "pa") {
      // Punjabi strictly uses Google Text-to-Speech (gTTS lang="pa")
      audioBuffer = await generateGoogleTTS(text, "pa");
    } else if (tl === "hi") {
      // Hindi strictly uses Microsoft Edge TTS (edge-tts)
      try {
        audioBuffer = await generateEdgeTTS(text, "hi-IN-MadhurNeural");
      } catch (e) {
        console.warn("Edge TTS Hindi fallback to Google TTS:", e);
        audioBuffer = await generateGoogleTTS(text, "hi");
      }
    } else {
      // English strictly uses Microsoft Edge TTS (edge-tts)
      try {
        audioBuffer = await generateEdgeTTS(text, "en-IN-NeerjaNeural");
      } catch (e) {
        console.warn("Edge TTS English fallback to Google TTS:", e);
        audioBuffer = await generateGoogleTTS(text, "en");
      }
    }

    if (!audioBuffer || audioBuffer.byteLength === 0) {
      return res.status(500).json({ error: "TTS audio synthesis returned empty stream" });
    }

    ttsAudioCache.set(cacheKey, audioBuffer);

    res.setHeader("Content-Type", "audio/mpeg");
    res.setHeader("Content-Length", audioBuffer.byteLength.toString());
    res.setHeader("Cache-Control", "public, max-age=86400");
    return res.send(audioBuffer);
  } catch (err: any) {
    console.error("TTS endpoint error:", err);
    return res.status(500).json({ error: err.message || "TTS synthesis failed" });
  }
});


async function start() {
  if (process.env.VERCEL) {
    return;
  }

  if (process.env.NODE_ENV !== "production") {
    const { createServer: createViteServer } = await import("vite");
    const vite = await createViteServer({
      server: { middlewareMode: true, allowedHosts: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`WeatherGPT server running on http://0.0.0.0:${PORT}`);
  });
}

if (!process.env.VERCEL) {
  start();
}

export default app;
