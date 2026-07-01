import logging
import os

import joblib
import numpy as np

from models  import ErrorType
from features import extract_features

log = logging.getLogger("classifier_detector")

_model = None
_model_path = None


def load_classifier(path: str):
    global _model, _model_path

    if not os.path.exists(path):
        log.warning(
            f"Classifier model not found at '{path}'. "
            f"Falling back to rule-based detection. "
        )
        _model = None
        return

    _model = joblib.load(path)
    _model_path = path
    log.info("Classifier ready.")


def _get_model(path: str):
    global _model, _model_path
    if _model is None or _model_path != path:
        load_classifier(path)
    return _model

_LABEL_TO_ERROR: dict[str, ErrorType] = {e.value: e for e in ErrorType}


def detect_error_type_clf(
    transcript:      str,
    target_word:     str,
    latency:         float = 0.0,
    asr_confidence:  float = 0.0,
    speech_detected: bool  = False,
    model_path:      str   = "error_classifier.pkl",
) -> ErrorType:
    model = _get_model(model_path)

    if model is None:
        from state_detection import detect_error_type
        return detect_error_type(transcript, target_word, latency)

    try:
        feat = extract_features(transcript, target_word, latency, asr_confidence, speech_detected)
        X = feat["vector"].reshape(1, -1)
        label = model.predict(X)[0]
        result = _LABEL_TO_ERROR.get(label)

        if result is None:
            from state_detection import detect_error_type
            return detect_error_type(transcript, target_word, latency)

        log.debug(
            f"CLF → '{label}'  "
            f"(transcript='{transcript[:40]}', target='{target_word}')"
        )
        return result

    except Exception as exc:
        log.warning(f"Classifier prediction failed ({exc}), falling back to rules.")
        from state_detection import detect_error_type
        return detect_error_type(transcript, target_word, latency)


