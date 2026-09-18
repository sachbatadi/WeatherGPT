// Single-Voice Speech Synthesizer:
// 1. Punjabi (pa): Google Text-to-Speech (gTTS lang="pa")
// 2. Hindi (hi): Microsoft Edge TTS (edge-tts hi-IN-MadhurNeural)
// 3. English (en): Microsoft Edge TTS (edge-tts en-IN-NeerjaNeural)
//
// Guaranteed immediate audio termination on stop. All other TTS engines/fallbacks removed.

import { Language } from '../types';

let currentAudio: HTMLAudioElement | null = null;
let activeSessionId = 0;

/**
 * Immediately halts any active voice alert audio playback and cancels any pending requests.
 */
export const stopSpeaking = () => {
  activeSessionId++;

  if (currentAudio) {
    // Unbind listeners first so no callbacks trigger on abort
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

  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    try {
      window.speechSynthesis.cancel();
    } catch {
      // ignore
    }
  }
};

/**
 * Speaks the text using strictly the single provided audio voice for the chosen language:
 * - 'pa': gTTS (lang="pa")
 * - 'hi': edge-tts (hi-IN)
 * - 'en': edge-tts (en-IN)
 */
export const speakText = (
  text: string,
  lang: Language,
  onStart?: () => void,
  onEnd?: () => void
) => {
  // Immediately stop any prior audio
  stopSpeaking();

  const sessionId = ++activeSessionId;

  // Clean the text from markdown, emojis, or formatting
  const cleanText = text
    .replace(/[#*_`~[\]()]/g, '')
    .replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '')
    .trim();

  if (!cleanText) {
    onEnd?.();
    return;
  }

  const ttsUrl = `/api/tts?lang=${encodeURIComponent(lang)}&text=${encodeURIComponent(cleanText)}`;
  const audio = new Audio(ttsUrl);
  currentAudio = audio;

  audio.onplay = () => {
    // If the user cancelled while the audio was buffering/loading, halt immediately
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
    onStart?.();
  };

  audio.onended = () => {
    if (currentAudio === audio) {
      currentAudio = null;
    }
    if (sessionId === activeSessionId) {
      onEnd?.();
    }
  };

  audio.onerror = () => {
    if (currentAudio === audio) {
      currentAudio = null;
    }
    if (sessionId === activeSessionId) {
      onEnd?.();
    }
  };

  audio.play().catch(() => {
    if (currentAudio === audio) {
      currentAudio = null;
    }
    if (sessionId === activeSessionId) {
      onEnd?.();
    }
  });
};
