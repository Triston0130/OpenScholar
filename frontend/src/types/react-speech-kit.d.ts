declare module 'react-speech-kit' {
  export interface Voice {
    default: boolean;
    lang: string;
    localService: boolean;
    name: string;
    voiceURI: string;
  }

  export interface SpeakOptions {
    text: string;
    voice?: Voice;
    rate?: number;
    pitch?: number;
    volume?: number;
    onEnd?: () => void;
    onError?: (error: any) => void;
    onStart?: () => void;
    onPause?: () => void;
    onResume?: () => void;
  }

  export interface UseSpeechSynthesisReturn {
    speak: (options: SpeakOptions) => void;
    cancel: () => void;
    pause: () => void;
    resume: () => void;
    speaking: boolean;
    supported: boolean;
    voices: Voice[];
  }

  export function useSpeechSynthesis(): UseSpeechSynthesisReturn;
}