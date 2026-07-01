import re
import logging
from typing import Optional
import numpy as np

from state_detection import (
    string_similarity,
    semantic_similarity,
    is_real_word,
    is_prefix_attempt,
    _best_word_match,
)
from config import RESPONSE_LATENCY_THRESHOLD

log = logging.getLogger("features")

FEATURE_NAMES = [
    "is_empty",                  # 1 if transcript is blank
    "speech_detected",           # 1 if mic detected sound but ASR got nothing
    "asr_confidence",            # Whisper avg_logprob  (negative float)
    "latency",                   # seconds to first speech
    "latency_over_threshold",    # 1 if latency >= RESPONSE_LATENCY_THRESHOLD
    "word_count",                # number of words in transcript
    "char_count",                # number of characters
    "str_sim_full",              # string_similarity(transcript, target)
    "best_pho",                  # best per-word phoneme similarity against target
    "sem_sim",                   # sentence-transformer cosine similarity (full transcript)
    "best_sem",                  # best per-word semantic similarity against target
    "any_real_word",             # 1 if at least one word is in the dictionary
    "has_prefix_attempt",        # 1 if any word is a valid prefix of the target
    "target_in_transcript",      # 1 if the exact target word appears verbatim
]


def extract_features(
    transcript:      str,
    target_word:     str,
    latency:         float = 0.0,
    asr_confidence:  float = 0.0,
    speech_detected: bool  = False,
) -> dict:
    t_clean = transcript.strip().lower()
    g_clean = target_word.strip().lower()

    words = [w.strip("?!.,[]() '") for w in re.split(r'[\s\-]+', t_clean)]
    words = [w for w in words if w]

    is_empty   = 1 if not t_clean or not words else 0
    word_count = len(words)
    char_count = len(t_clean)

    lat_over = 1 if latency >= RESPONSE_LATENCY_THRESHOLD else 0

    str_sim_full = string_similarity(t_clean, g_clean)  if not is_empty else 0.0

    if words and not is_empty:
        _, _ , best_pho = _best_word_match(words, g_clean)
    else:
        _, _ , best_pho = "", 0.0, 0.0

    sem_sim  = semantic_similarity(t_clean, g_clean) if not is_empty else 0.0
    best_sem = max(
        semantic_similarity(w, g_clean) for w in words
    ) if words and not is_empty else 0.0

    any_real   = 1 if words and any(is_real_word(w) for w in words)  else 0

    has_prefix = 1 if any(is_prefix_attempt(w, g_clean) for w in words) else 0
    target_in  = 1 if g_clean in words else 0

    values = {
        "is_empty":              float(is_empty),
        "speech_detected":       float(speech_detected),
        "asr_confidence":        float(asr_confidence),
        "latency":               float(latency),
        "latency_over_threshold":float(lat_over),
        "word_count":            float(word_count),
        "char_count":            float(char_count),
        "str_sim_full":          float(str_sim_full),
        "best_pho":              float(best_pho),
        "sem_sim":               float(sem_sim),
        "best_sem":              float(best_sem),
        "any_real_word":         float(any_real),
        "has_prefix_attempt":    float(has_prefix),
        "target_in_transcript":  float(target_in),
    }

    vector = np.array([values[n] for n in FEATURE_NAMES], dtype=np.float32)

    return {
        "names":  FEATURE_NAMES,
        "values": values,
        "vector": vector,
    }


def extract_feature_matrix(samples: list[dict]) -> np.ndarray:
    rows = []
    for s in samples:
        feat = extract_features(
            transcript      = s["transcript"],
            target_word     = s["target_word"],
            latency         = s.get("latency", 0.0),
            asr_confidence  = s.get("asr_confidence", 0.0),
            speech_detected = s.get("speech_detected", False),
        )
        rows.append(feat["vector"])
    return np.vstack(rows)
