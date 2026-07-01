import time
import logging
import numpy as np
import sounddevice as sd
import whisper
import threading
from pynput import keyboard


from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.threads import deferToThread

from config import (
    WHISPER_MODEL_SIZE,
    WHISPER_LANGUAGE,
    AUDIO_SAMPLE_RATE,
    MAX_RECORD_SECONDS,
    SILENCE_THRESHOLD,
    SILENCE_DURATION,
    SILENCE_CHUNK_SIZE,
    DONE_KEY,
)

log = logging.getLogger("stt")
_whisper_model = None

_done_event = threading.Event()
_last_stop_reason = "silence"

def signal_done():
    _done_event.set()

def was_done_signalled() -> bool:
    return _last_stop_reason == "done_signal"

def reset_done_signal():
    _done_event.clear()

def _start_key_listener():
    def _listen():
        try:
            from pynput.keyboard import Key as PynputKey

            def on_press(key):
                try:
                    if key == PynputKey.space or getattr(key, "char", None) == DONE_KEY:
                        log.info("Done-key pressed, signalling done.")
                        signal_done()
                except Exception as e:
                    log.warning(f"on_press error: {e}")

            with keyboard.Listener(on_press=on_press) as listener:
                listener.join()

        except Exception as e:
            log.warning(f"Key listener failed: {e}")

    t = threading.Thread(target=_listen, daemon=True)
    t.start()

def load_whisper():
    global _whisper_model
    if _whisper_model is None:
        log.info(f"Loading Whisper '{WHISPER_MODEL_SIZE}' model...")
        _whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
        log.info("Whisper ready.")
    return _whisper_model


def _get_whisper():
    if _whisper_model is None:
        return load_whisper()
    return _whisper_model

def _record_until_done() -> tuple:
    global _last_stop_reason

    already_signalled = _done_event.is_set()
    _done_event.clear()
    if already_signalled:
        _last_stop_reason = "done_signal"
        return np.array([], dtype=np.float32), 0.0, False
    
    chunks             = []
    silent_chunks      = 0
    speech_started     = False
    first_speech_time  = None
    start_time         = time.time()
    stop_reason       = "max_duration"

    silence_chunks_needed = int(
        SILENCE_DURATION * AUDIO_SAMPLE_RATE / SILENCE_CHUNK_SIZE
    )
    max_chunks = int(MAX_RECORD_SECONDS * AUDIO_SAMPLE_RATE / SILENCE_CHUNK_SIZE)

    log.info("Listening...")

    with sd.InputStream(
        samplerate = AUDIO_SAMPLE_RATE,
        channels   = 1,
        dtype      = "float32",
        blocksize  = SILENCE_CHUNK_SIZE,
    ) as stream:
        for _ in range(max_chunks):
            if _done_event.is_set():
                stop_reason = "done_signal"
                break

            chunk, _ = stream.read(SILENCE_CHUNK_SIZE)
            chunk    = chunk.flatten()
            chunks.append(chunk)

            rms = float(np.sqrt(np.mean(chunk ** 2)))

            if rms > SILENCE_THRESHOLD:
                silent_chunks = 0
                if not speech_started:
                    speech_started    = True
                    first_speech_time = time.time()
            else:
                if speech_started:
                    silent_chunks += 1
                    if silent_chunks >= silence_chunks_needed:
                        log.info("Silence detected, stopping recording.")
                        stop_reason = "silence"
                        break
    signal_done()

    audio   = np.concatenate(chunks) if chunks else np.array([], dtype=np.float32)
    latency = (first_speech_time - start_time) if first_speech_time else (time.time() - start_time)

    log.info(
            f"Recording stopped ({stop_reason}) | "
            f"duration={len(audio)/AUDIO_SAMPLE_RATE:.1f}s | "
            f"latency={latency:.1f}s"
        )
    
    _last_stop_reason = stop_reason
    return audio, latency, speech_started

def _transcribe(audio: np.ndarray) -> str:
    if len(audio) < AUDIO_SAMPLE_RATE * 0.3:
        log.info("Audio too short, returning empty transcript.")
        return ""

    model  = _get_whisper()
    result = model.transcribe(audio, language=WHISPER_LANGUAGE, fp16=False)
    text   = result.get("text", "").strip()

    log.info(f"Whisper --> '{text}'")
    return text

@inlineCallbacks
def listen_for_response():
    audio, latency, speech_detected = yield deferToThread(_record_until_done)
    transcript = yield deferToThread(_transcribe, audio)

    returnValue((transcript, latency, speech_detected))

_start_key_listener()
