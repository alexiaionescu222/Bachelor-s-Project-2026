import logging
import importlib
from typing import Optional

import pronouncing
from models import UserState, FeedbackType, ErrorType
from state_detection import string_similarity

log = logging.getLogger("feedback")

_LANG_MODULES = {
    "en": "feedback_en",
    "nl": "feedback_nl",
}

def _get_lang_module(lang: str):
    module_name = _LANG_MODULES.get(lang, "feedback_en")
    return importlib.import_module(module_name)

def _pho_cue_parts(target_word: str, transcript: str, lang: str = "en"):
    words = [w.strip(".,?!") for w in transcript.lower().split()]
    best_word = (
        max(words, key=lambda w: string_similarity(w, target_word.lower()), default="")
        if words else ""
    )
    phones = pronouncing.phones_for_word(target_word.lower())
    first_phone = phones[0].split()[0].rstrip("012") if phones else ""

    shared_prefix = shared_suffix = 0
    stem = ending = ""
    if best_word and target_word:
        t = target_word.lower()
        w = best_word.lower()
        for a, b in zip(w, t):
            if a == b: shared_prefix += 1
            else: break
        for a, b in zip(reversed(w), reversed(t)):
            if a == b: shared_suffix += 1
            else: break
        stem   = t[:shared_prefix]
        ending = t[-shared_suffix:] if shared_suffix else ""

    return shared_prefix, shared_suffix, stem, ending, first_phone


def select_feedback(
    state: UserState,
    target_word: str = "",
    prev_error: ErrorType = None,
) -> FeedbackType:
    err     = state.error_type
    attempt = state.attempt_number

    if err == ErrorType.CORRECT:
        return FeedbackType.CONFIRMATION

    if err == ErrorType.SILENCE:
        if attempt == 1:   return FeedbackType.WAIT
        elif attempt == 2: return FeedbackType.SEMANTIC_CUE
        else:              return FeedbackType.PHONOLOGICAL_CUE

    if err == ErrorType.UNINTELLIGIBLE:
        if attempt <= 2:   return FeedbackType.CLARIFICATION
        elif attempt == 3: return FeedbackType.SEMANTIC_CUE
        else:              return FeedbackType.EXPLICIT_CORRECTION

    if err == ErrorType.CIRCUMLOCUTION:
        if attempt <= 2:   return FeedbackType.ELICITATION_CIRCUMLOCUTION
        elif attempt == 3: return FeedbackType.PHONOLOGICAL_CUE
        else:              return FeedbackType.EXPLICIT_CORRECTION

    if err == ErrorType.PHONOLOGICAL_ERROR:
        if attempt == 1:   return FeedbackType.ELICITATION_PHONOLOGICAL
        elif attempt == 2: return FeedbackType.PHONOLOGICAL_CUE
        elif attempt == 3: return FeedbackType.SEMANTIC_CUE
        else:              return FeedbackType.EXPLICIT_CORRECTION

    if err == ErrorType.SEMANTIC_ERROR:
        if attempt == 1:   return FeedbackType.ELICITATION_SEMANTIC
        elif attempt == 2: return FeedbackType.SEMANTIC_CUE
        elif attempt == 3: return FeedbackType.PHONOLOGICAL_CUE
        else:              return FeedbackType.EXPLICIT_CORRECTION

    if err == ErrorType.NEOLOGISM:
        if attempt == 1:   return FeedbackType.CLARIFICATION
        elif attempt == 2: return FeedbackType.PHONOLOGICAL_CUE
        else:              return FeedbackType.EXPLICIT_CORRECTION

    if err == ErrorType.PARTIAL_ATTEMPT:
        if prev_error == ErrorType.CIRCUMLOCUTION:
            if attempt <= 2:   return FeedbackType.ELICITATION
            elif attempt == 3: return FeedbackType.PHONOLOGICAL_CUE
            else:              return FeedbackType.EXPLICIT_CORRECTION
        if attempt == 1:   return FeedbackType.ELICITATION
        elif attempt == 2: return FeedbackType.SEMANTIC_CUE
        elif attempt == 3: return FeedbackType.PHONOLOGICAL_CUE
        else:              return FeedbackType.EXPLICIT_CORRECTION


def resolve_text(
    feedback_type:  FeedbackType,
    target_word:    str,
    script_counter: dict,
    semantic_hints: Optional[dict] = None,
    transcript:     str = "",
    lang:           str = "en",
) -> str:
    m = _get_lang_module(lang)

    if feedback_type == FeedbackType.PHONOLOGICAL_CUE:
        parts = _pho_cue_parts(target_word, transcript, lang)
        return m.build_pho_cue(target_word, *parts)

    if feedback_type == FeedbackType.SEMANTIC_CUE:
        hint = semantic_hints.get(target_word.lower()) if semantic_hints else None
        return m.build_sem_cue(hint)

    if feedback_type == FeedbackType.EXPLICIT_CORRECTION:
        return m.build_exp_correction(target_word)

    scripts = m.FEEDBACK_SCRIPTS.get(feedback_type, [])
    if not scripts:
        import feedback_en
        scripts = feedback_en.FEEDBACK_SCRIPTS.get(feedback_type, ["..."])

    idx = script_counter.get(feedback_type, 0) % len(scripts)
    script_counter[feedback_type] = idx + 1
    return scripts[idx].replace("{word}", target_word.capitalize())
