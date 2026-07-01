import logging
from difflib import SequenceMatcher
from typing import Optional

import numpy as np
import pronouncing
import re
from sentence_transformers import SentenceTransformer

from models import ErrorType, UserState
from config import (
    RESPONSE_LATENCY_THRESHOLD,
    STRING_CORRECT_THRESHOLD,
    SEMANTIC_LOW_THRESHOLD,
    SEMANTIC_HIGH_THRESHOLD,
    USE_CLASSIFIER,
    CLASSIFIER_MODEL_PATH,
)

log = logging.getLogger("state_detection")

_word_check_fn = None
def _get_word_check():
    global _word_check_fn
    if _word_check_fn is not None:
        return _word_check_fn
    try:
        from wordfreq import word_frequency
        _word_check_fn = lambda w: word_frequency(w, "en") > 0
    except ImportError:
        _word_check_fn = lambda w: bool(pronouncing.phones_for_word(w.lower()))
    return _word_check_fn
    

_sem_model: Optional[SentenceTransformer] = None


def _get_sem_model() -> SentenceTransformer:
    global _sem_model
    if _sem_model is None:
        log.info("Loading sentence-transformer model (first use)...")
        _sem_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _sem_model


def preload_models():
    log.info("Pre-loading sentence-transformer model...")
    model = _get_sem_model()
    model.encode(["warmup"], normalize_embeddings=True)
    log.info("Sentence-transformer model ready.")

def string_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

def phoneme_similarity(word_a: str, word_b: str) -> float:
    phones_a = pronouncing.phones_for_word(word_a.lower())
    phones_b = pronouncing.phones_for_word(word_b.lower())
    if not phones_a or not phones_b:
        return 0.0
    
    list_a = [p.rstrip("012") for p in phones_a[0].split()]
    list_b = [p.rstrip("012") for p in phones_b[0].split()]
    
    return SequenceMatcher(None, list_a, list_b).ratio()


def semantic_similarity(text_a: str, text_b: str) -> float:
    model = _get_sem_model()
    embs  = model.encode([text_a, text_b], normalize_embeddings=True)
    return float(np.dot(embs[0], embs[1]))

def is_prefix_attempt(word: str, target: str, min_ratio: float = 0.40) -> bool:
    w, t = word.lower().strip(), target.lower().strip()
    if not w or not t:
        return False
    return t.startswith(w) and len(w) >= min_ratio * len(t)

def is_real_word(word: str) -> bool:
    clean = word.strip(".,!?;:'-").lower()
    if len(clean) <= 2:
        return True
    try:
        return _get_word_check()(clean)
    except Exception:
        return True

def _best_word_match(words: list, target: str) -> tuple:
    best_word = words[0] if words else ""
    best_sim  = 0.0
    best_pho  = 0.0
    for w in words:
        w_clean = w.strip("?!.,[]() '")
        sim = string_similarity(w_clean, target)
        pho = phoneme_similarity(w_clean, target)
        pho_score = max(sim, pho) if sim >= 0.40 else sim
        if sim > best_sim:
            best_sim  = sim
            best_word = w_clean
        if pho_score > best_pho:
            best_pho = pho_score
    return best_word, best_sim, best_pho


DESCRIPTION_MARKERS = {"thing", "use", "used", "kind", "sort", 
                        "when", "where", "you", "it", "with", "its", "they", "has", "have", "is", "are", "was",
                        "for", "on", "in", "at", "to", "from", "of", "into", "out",
                        "like", "type", "part", "end", "top", "back", "side", "which", "that", "this", "there",}

FILLER_WORDS = {"um", "uh", "er", "hmm", "eh", "ah", "oh", "i", "don't", 
                "know", "what", "maybe", "think", "sure", "not", "uhh", "umm", "err", "an", "a"}

def _is_circumlocution(words: list, best_sim: float, target_word: str) -> bool:
    if len(words) < 4:
        return False
    
    content_words = [w for w in words if w not in FILLER_WORDS]
    if len(content_words) < 3:
        return False
    
    word_set = set(words)
    has_markers = len(word_set & DESCRIPTION_MARKERS) >= 2
    if not has_markers:
        return False
    
    sem_sim = semantic_similarity(" ".join(words), target_word)
    if sem_sim < SEMANTIC_LOW_THRESHOLD:
        return False
    
    return True


def detect_error_type(
    transcript:       str,
    target_word:      str,
    latency:     float = 0.0, 
    accepted_answers: list  = None,   # ← new
) -> ErrorType:

    t_clean = transcript.strip().lower()
    g_clean = target_word.strip().lower()
    words = [w.strip("?!.,[]() '") for w in re.split(r'[\s\-]+', t_clean)]
    words   = [w for w in words if w] 

    if accepted_answers:
        for ans in accepted_answers:
            ans_clean = ans.strip().lower()
            if ans_clean in words or string_similarity(t_clean, ans_clean) >= STRING_CORRECT_THRESHOLD:
                return ErrorType.CORRECT

    if not t_clean or not words:
        return ErrorType.SILENCE
    if latency >= RESPONSE_LATENCY_THRESHOLD and len(words) < 2:
        return ErrorType.SILENCE

    # correct 
    if g_clean in words:
        return ErrorType.CORRECT

    _, best_sim, best_pho = _best_word_match(words, g_clean)

    if best_sim >= 0.75 or best_pho >= 0.75:
        return ErrorType.CORRECT

    # circumlocution 
    if _is_circumlocution(words, best_sim, g_clean) and best_pho < 0.50:
        return ErrorType.CIRCUMLOCUTION

    # phonological 
    if best_pho >= 0.50:
        return ErrorType.PHONOLOGICAL_ERROR

    # semantic 
    sem_sim = semantic_similarity(t_clean, g_clean)

    best_word_sem = max(semantic_similarity(w, g_clean) for w in words) if words else 0.0

    if (SEMANTIC_LOW_THRESHOLD <= sem_sim < SEMANTIC_HIGH_THRESHOLD or
            SEMANTIC_LOW_THRESHOLD <= best_word_sem < SEMANTIC_HIGH_THRESHOLD):
        return ErrorType.SEMANTIC_ERROR

    # neologism 
    if words and not any(is_real_word(w) for w in words):
        return ErrorType.NEOLOGISM

    return ErrorType.PARTIAL_ATTEMPT

# state builder 

def build_user_state(
    transcript:       str,
    target_word:      str,
    latency:          float,
    attempt_number:   int,
    asr_confidence:   float = 0.0,
    accepted_answers: list = None,
    speech_detected: bool = False,

) -> UserState:
    if asr_confidence < -3.0 and asr_confidence != 0.0:
        return UserState(
            error_type        = ErrorType.UNINTELLIGIBLE,
            attempt_number    = attempt_number,
            transcript        = "[low confidence, could not decode]",
            latency           = latency,
        )
    
    if not transcript.strip() and speech_detected:
        return UserState(
            error_type = ErrorType.UNINTELLIGIBLE,
            attempt_number    = attempt_number,
            transcript = "[speech detected but could not decode]",
            latency           = latency,
    )

    if USE_CLASSIFIER:
            from classifier_detection import detect_error_type_clf
            error = detect_error_type_clf(
                transcript      = transcript,
                target_word     = target_word,
                latency         = latency,
                asr_confidence  = asr_confidence,
                speech_detected = speech_detected,
                model_path      = CLASSIFIER_MODEL_PATH,
            )
    else:
        error = detect_error_type(transcript, target_word, latency, accepted_answers)
    
    return UserState(
        error_type        = error,
        attempt_number    = attempt_number,
        transcript        = transcript,
        latency           = latency,
    )
