import json
import importlib
import os
from pathlib import Path

import speech_recognition as sr

try:
    vosk_module = importlib.import_module("vosk")
except ImportError:
    vosk_module = None

if vosk_module is not None:
    KaldiRecognizer = vosk_module.KaldiRecognizer
    Model = vosk_module.Model
    SetLogLevel = vosk_module.SetLogLevel
else:
    KaldiRecognizer = None
    Model = None
    SetLogLevel = None


LANGUAGE_CONFIG = {
    "English": {
        "google_code": "en-IN",
        "vosk_paths": ["models/vosk-en", "models/vosk-model-small-en-in-0.4"],
        "env_var": "VOSK_MODEL_EN",
    },
    "Hindi": {
        "google_code": "hi-IN",
        "vosk_paths": ["models/vosk-hi", "models/vosk-model-small-hi-0.22"],
        "env_var": "VOSK_MODEL_HI",
    },
}


class SpeechService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 250
        self.recognizer.pause_threshold = 0.8
        self.recognizer.dynamic_energy_threshold = True
        self._vosk_models = {}

        if SetLogLevel is not None:
            SetLogLevel(-1)

    def available_engines(self, language_name):
        engines = ["Google"]
        if self._resolve_vosk_model_path(language_name):
            engines.insert(0, "Vosk")
        return engines

    def listen_and_transcribe(self, language_name, engine_name="Auto"):
        if language_name not in LANGUAGE_CONFIG:
            raise ValueError("Unsupported language selected.")

        with self._open_microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
            last_unknown_error = None

            for _ in range(2):
                try:
                    audio = self.recognizer.listen(source, timeout=6, phrase_time_limit=12)
                    selected_engine = self._select_engine(language_name, engine_name)
                    return self._transcribe(audio, language_name, selected_engine)
                except sr.WaitTimeoutError as exc:
                    raise RuntimeError("Listening timed out. Select the cell and speak again.") from exc
                except sr.UnknownValueError as exc:
                    last_unknown_error = exc

        raise RuntimeError(
            "Speech was not clear enough to understand. Speak closer to the microphone and try again."
        ) from last_unknown_error

    def _open_microphone(self):
        try:
            return sr.Microphone(sample_rate=16000)
        except OSError as exc:
            raise RuntimeError("Microphone not found. Please connect a microphone and try again.") from exc

    def _select_engine(self, language_name, engine_name):
        if engine_name == "Auto":
            return "Vosk" if self._resolve_vosk_model_path(language_name) else "Google"

        if engine_name == "Vosk" and not self._resolve_vosk_model_path(language_name):
            raise RuntimeError(
                f"Vosk model for {language_name} was not found. Add a model folder or switch engine to Google."
            )

        return engine_name

    def _transcribe(self, audio, language_name, engine_name):
        if engine_name == "Vosk":
            return self._transcribe_with_vosk(audio, language_name)

        return self._transcribe_with_google(audio, language_name)

    def _transcribe_with_google(self, audio, language_name):
        try:
            text = self.recognizer.recognize_google(
                audio,
                language=LANGUAGE_CONFIG[language_name]["google_code"],
            )
        except sr.RequestError as exc:
            raise RuntimeError(f"Google Speech API error: {exc}") from exc
        except sr.UnknownValueError:
            raise

        return {
            "text": text,
            "confidence": None,
            "engine": "Google",
        }

    def _transcribe_with_vosk(self, audio, language_name):
        model = self._load_vosk_model(language_name)
        recognizer = KaldiRecognizer(model, audio.sample_rate)
        recognizer.SetWords(True)
        recognizer.AcceptWaveform(audio.get_raw_data(convert_rate=16000, convert_width=2))

        result = json.loads(recognizer.FinalResult() or "{}")
        text = (result.get("text") or "").strip()
        if not text:
            raise sr.UnknownValueError()

        confidence = None
        if result.get("result"):
            confidences = [entry.get("conf", 0.0) for entry in result["result"]]
            if confidences:
                confidence = round(sum(confidences) / len(confidences), 2)

        return {
            "text": text,
            "confidence": confidence,
            "engine": "Vosk",
        }

    def _load_vosk_model(self, language_name):
        if language_name in self._vosk_models:
            return self._vosk_models[language_name]

        model_path = self._resolve_vosk_model_path(language_name)
        if not model_path:
            raise RuntimeError(f"Vosk model for {language_name} was not found.")

        self._vosk_models[language_name] = Model(model_path)
        return self._vosk_models[language_name]

    def _resolve_vosk_model_path(self, language_name):
        if Model is None:
            return None

        env_path = os.environ.get(LANGUAGE_CONFIG[language_name]["env_var"])
        candidates = []
        if env_path:
            candidates.append(Path(env_path))

        candidates.extend(Path(path) for path in LANGUAGE_CONFIG[language_name]["vosk_paths"])

        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                return str(candidate)

        return None
