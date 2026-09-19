// Universal Speech Synthesizer for WeatherGPT:
// 1. Attempts high-fidelity cloud / server audio (/api/tts) if available.
// 2. Instantly and automatically falls back to native Web Speech API (window.speechSynthesis)
//    if the server route returns 404, errors, times out, or runs client-side (Vercel / Vite).
// 3. Language-aware voice matching:
//    - Punjabi ('pa'): Punjabi voice (pa-IN / pa) -> Hindi voice (hi-IN) -> Indian English -> default
//    - Hindi ('hi'): Hindi voice (hi-IN / hi / Madhur / Swara) -> default
//    - English ('en'): Indian English (en-IN / Neerja / Prabhat) -> English (en-US / en) -> default
// 4. Chunking to prevent Chromium long-speech freeze.
// 5. Global references to avoid Chromium V8 garbage-collection cutoff bug.
// 6. Guaranteed immediate audio termination on stopSpeaking().

import { Language } from '../types';

let currentAudio: HTMLAudioElement | null = null;
let activeSessionId = 0;
let activeUtterances: SpeechSynthesisUtterance[] = [];
let speechPulseTimer: any = null;
let cachedVoices: SpeechSynthesisVoice[] = [];

// Populate and cache voices when speech synthesis is available
const updateVoices = () => {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    try {
      const v = window.speechSynthesis.getVoices();
      if (v && v.length > 0) {
        cachedVoices = v;
      }
    } catch {
      // ignore
    }
  }
};

if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
  updateVoices();
  if (window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = updateVoices;
  }
}

/**
 * Finds the highest quality available voice for the target language.
 */
const getBestVoice = (lang: Language): { voice: SpeechSynthesisVoice | null; langCode: string } => {
  updateVoices();
  const voices = cachedVoices;

  if (lang === 'pa') {
    // 1. Look for native Punjabi voice
    const paVoice = voices.find(
      (v) =>
        v.lang.toLowerCase().startsWith('pa') ||
        v.name.toLowerCase().includes('punjabi') ||
        v.name.toLowerCase().includes('gurmukhi')
    );
    if (paVoice) return { voice: paVoice, langCode: paVoice.lang || 'pa-IN' };

    // 2. Look for Hindi voice (shares phonetic roots for Indian terminology & geographical names)
    const hiVoice = voices.find(
      (v) =>
        v.lang.toLowerCase().startsWith('hi') ||
        v.name.toLowerCase().includes('hindi') ||
        v.name.toLowerCase().includes('madhur') ||
        v.name.toLowerCase().includes('swara') ||
        v.name.toLowerCase().includes('kalpana')
    );
    if (hiVoice) return { voice: hiVoice, langCode: 'hi-IN' };

    // 3. Look for Indian English voice
    const enInVoice = voices.find((v) => v.lang.toLowerCase().startsWith('en-in'));
    if (enInVoice) return { voice: enInVoice, langCode: 'en-IN' };

    return { voice: null, langCode: 'pa-IN' };
  }

  if (lang === 'hi') {
    // 1. Look for Hindi voice
    const hiVoice = voices.find(
      (v) =>
        v.lang.toLowerCase().startsWith('hi') ||
        v.name.toLowerCase().includes('hindi') ||
        v.name.toLowerCase().includes('madhur') ||
        v.name.toLowerCase().includes('swara') ||
        v.name.toLowerCase().includes('kalpana')
    );
    if (hiVoice) return { voice: hiVoice, langCode: hiVoice.lang || 'hi-IN' };

    // 2. Look for Indian English voice as fallback
    const enInVoice = voices.find((v) => v.lang.toLowerCase().startsWith('en-in'));
    if (enInVoice) return { voice: enInVoice, langCode: 'en-IN' };

    return { voice: null, langCode: 'hi-IN' };
  }

  // English
  const enInVoice = voices.find(
    (v) =>
      v.lang.toLowerCase().startsWith('en-in') ||
      v.name.toLowerCase().includes('neerja') ||
      v.name.toLowerCase().includes('prabhat') ||
      v.name.toLowerCase().includes('india')
  );
  if (enInVoice) return { voice: enInVoice, langCode: enInVoice.lang || 'en-IN' };

  const enVoice = voices.find((v) => v.lang.toLowerCase().startsWith('en'));
  if (enVoice) return { voice: enVoice, langCode: enVoice.lang || 'en-US' };

  return { voice: null, langCode: 'en-US' };
};

/**
 * Splits text into natural sentence chunks to prevent Chromium utterance timeouts.
 */
const splitIntoSentences = (text: string, maxLength = 160): string[] => {
  const sentences = text.match(/[^।?!.\n\r]+[।?!.\n\r]*/g) || [text];
  const chunks: string[] = [];
  let current = '';

  for (const s of sentences) {
    const trimmed = s.trim();
    if (!trimmed) continue;

    if ((current + ' ' + trimmed).trim().length <= maxLength) {
      current = (current ? current + ' ' : '') + trimmed;
    } else {
      if (current) chunks.push(current);
      if (trimmed.length > maxLength) {
        const words = trimmed.split(' ');
        let wordChunk = '';
        for (const w of words) {
          if ((wordChunk + ' ' + w).trim().length <= maxLength) {
            wordChunk = (wordChunk ? wordChunk + ' ' : '') + w;
          } else {
            if (wordChunk) chunks.push(wordChunk);
            wordChunk = w;
          }
        }
        current = wordChunk;
      } else {
        current = trimmed;
      }
    }
  }
  if (current) chunks.push(current);
  return chunks.length > 0 ? chunks : [text];
};

/**
 * Immediately halts all active voice alert playback (both Audio element and Web Speech API).
 */
export const stopSpeaking = () => {
  activeSessionId++;

  if (speechPulseTimer) {
    clearInterval(speechPulseTimer);
    speechPulseTimer = null;
  }

  // 1. Stop HTML Audio element
  if (currentAudio) {
    currentAudio.onplay = null;
    currentAudio.onended = null;
    currentAudio.onerror = null;
    currentAudio.onpause = null;

    try {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      currentAudio.removeAttribute('src');
      currentAudio.load();
    } catch {
      // ignore
    }
    currentAudio = null;
  }

  // 2. Stop Web Speech API
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    try {
      activeUtterances.forEach((u) => {
        u.onstart = null;
        u.onend = null;
        u.onerror = null;
      });
      activeUtterances = [];
      window.speechSynthesis.cancel();
    } catch {
      // ignore
    }
  }
};

/**
 * Plays speech using the browser's built-in Web Speech API (zero server requirement).
 */
const speakWithSpeechSynthesis = (
  cleanText: string,
  lang: Language,
  sessionId: number,
  onStart?: () => void,
  onEnd?: () => void
) => {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
    onEnd?.();
    return;
  }

  try {
    window.speechSynthesis.cancel();
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
  } catch {
    // ignore
  }

  const chunks = splitIntoSentences(cleanText, 160);
  const { voice, langCode } = getBestVoice(lang);

  activeUtterances = [];
  let currentIndex = 0;
  let started = false;

  const playNextChunk = () => {
    if (sessionId !== activeSessionId) return;

    if (currentIndex >= chunks.length) {
      activeUtterances = [];
      if (speechPulseTimer) {
        clearInterval(speechPulseTimer);
        speechPulseTimer = null;
      }
      onEnd?.();
      return;
    }

    const chunk = chunks[currentIndex];
    const utterance = new SpeechSynthesisUtterance(chunk);
    utterance.lang = langCode;
    if (voice) {
      utterance.voice = voice;
    }
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    // Retain reference in module array to prevent Chromium garbage-collection bug
    activeUtterances.push(utterance);

    utterance.onstart = () => {
      if (sessionId !== activeSessionId) return;
      if (!started) {
        started = true;
        onStart?.();
      }
    };

    utterance.onend = () => {
      if (sessionId !== activeSessionId) return;
      currentIndex++;
      playNextChunk();
    };

    utterance.onerror = (e) => {
      if (sessionId !== activeSessionId) return;
      if (e.error === 'interrupted' || e.error === 'canceled') {
        return;
      }
      currentIndex++;
      playNextChunk();
    };

    try {
      window.speechSynthesis.speak(utterance);
    } catch {
      currentIndex++;
      playNextChunk();
    }
  };

  // Chromium keep-alive pulse: prevents browser speech engine from pausing after 14 seconds
  if (speechPulseTimer) {
    clearInterval(speechPulseTimer);
  }
  speechPulseTimer = setInterval(() => {
    if (sessionId !== activeSessionId || !window.speechSynthesis.speaking) {
      if (speechPulseTimer) {
        clearInterval(speechPulseTimer);
        speechPulseTimer = null;
      }
      return;
    }
    window.speechSynthesis.pause();
    window.speechSynthesis.resume();
  }, 10000);

  // Trigger first chunk
  playNextChunk();
};

/**
 * Universal voice synthesis:
 * Attempts high-fidelity cloud / API audio if reachable, with instant automatic fallback
 * to browser native SpeechSynthesis so voice is ALWAYS produced.
 */
export const speakText = (
  text: string,
  lang: Language,
  onStart?: () => void,
  onEnd?: () => void
) => {
  stopSpeaking();

  const sessionId = ++activeSessionId;

  // Clean the text from markdown, symbols, emojis
  const cleanText = text
    .replace(/[#*_`~[\]()]/g, '')
    .replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '')
    .replace(/\s+/g, ' ')
    .trim();

  if (!cleanText) {
    onEnd?.();
    return;
  }

  // Flag to avoid dual callbacks
  let hasStarted = false;
  const safeOnStart = () => {
    if (!hasStarted && sessionId === activeSessionId) {
      hasStarted = true;
      onStart?.();
    }
  };

  const safeOnEnd = () => {
    if (sessionId === activeSessionId) {
      onEnd?.();
    }
  };

  const ttsUrl = `/api/tts?lang=${encodeURIComponent(lang)}&text=${encodeURIComponent(cleanText)}`;
  let serverFallbackTriggered = false;

  const triggerFallback = () => {
    if (serverFallbackTriggered || sessionId !== activeSessionId) return;
    serverFallbackTriggered = true;
    if (currentAudio) {
      try {
        currentAudio.pause();
        currentAudio.removeAttribute('src');
      } catch {
        // ignore
      }
      currentAudio = null;
    }
    speakWithSpeechSynthesis(cleanText, lang, sessionId, safeOnStart, safeOnEnd);
  };

  // Safety timer: if /api/tts hangs, buffers, or takes > 1200ms without starting, fallback immediately
  const safetyTimeout = setTimeout(() => {
    if (!hasStarted && sessionId === activeSessionId) {
      triggerFallback();
    }
  }, 1200);

  try {
    const audio = new Audio(ttsUrl);
    currentAudio = audio;

    audio.onplay = () => {
      clearTimeout(safetyTimeout);
      if (sessionId !== activeSessionId) {
        try {
          audio.pause();
          audio.removeAttribute('src');
          audio.load();
        } catch {
          // ignore
        }
        return;
      }
      safeOnStart();
    };

    audio.onended = () => {
      clearTimeout(safetyTimeout);
      if (currentAudio === audio) {
        currentAudio = null;
      }
      safeOnEnd();
    };

    audio.onerror = () => {
      clearTimeout(safetyTimeout);
      triggerFallback();
    };

    const playPromise = audio.play();
    if (playPromise !== undefined) {
      playPromise.catch(() => {
        clearTimeout(safetyTimeout);
        triggerFallback();
      });
    }
  } catch {
    clearTimeout(safetyTimeout);
    triggerFallback();
  }
};
