import json
import logging
import os
from datetime import datetime
from collections import Counter

import time
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.threads import deferToThread

from autobahn.twisted.util import sleep

from models import ErrorType, FeedbackType, SessionState
from stt import listen_for_response, was_done_signalled, reset_done_signal
from tts import text_to_speech, play_behavior
from state_detection import build_user_state, detect_error_type
from feedback import select_feedback, resolve_text
from config import (
    MAX_ATTEMPTS_PER_ITEM,
    PAUSE_AFTER_PROMPT,
    PAUSE_BETWEEN_ATTEMPTS,
    PAUSE_END_SESSION,
    LANGUAGE,
)
from image_display import ImageDisplay
from scripts import t

log = logging.getLogger("session")

def load_tasks(path: str) -> list:
    with open(path) as f:
        tasks = json.load(f)
    log.info(f"Loaded {len(tasks)} task items from '{path}'")
    return tasks


def save_session_log(session: SessionState):
    timestamp  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_folder = "session_logs"
    os.makedirs(log_folder, exist_ok=True)
    path = os.path.join(log_folder, f"session_{timestamp}.json")
    trials = session.session_log
    
    feedback_dist = dict(Counter(t["feedback_given"] for t in trials if t["feedback_given"]))
    error_dist = dict(Counter(t["error_type"] for t in trials))

    session_duration = round(time.time() - session.session_start_time)

    output = {
        "summary": {
            "items_correct":        session.items_correct,
            "items_total":          session.items_total,
            "session_duration_s":   session_duration,
            "feedback_distribution":    feedback_dist,
            "error_type_distribution":  error_dist,
        },
        "trials": trials,
    }
    with open(path, "w") as f:
        json.dump(output, f, indent=2)
    log.info(f"Session log saved to '{path}'")
    


def _is_yes(transcript: str) -> bool:
    yes_words = t("yes_words", LANGUAGE)
    words = {w.strip(".,!?") for w in transcript.lower().split()}
    return bool(words & yes_words)


def _is_no(transcript: str) -> bool:
    no_words = t("no_words", LANGUAGE)
    words = {w.strip(".,!?") for w in transcript.lower().split()}
    return bool(words & no_words)

@inlineCallbacks
def introduction(session_wamp):
    yield play_behavior(session_wamp, "BlocklyWaveRightArm")

    yield text_to_speech(session_wamp,  t("intro_greeting", LANGUAGE))
    yield sleep(1.0)

    yield text_to_speech(session_wamp, t("intro_explain", LANGUAGE))
    yield sleep(1.0)

    yield text_to_speech(session_wamp, t("intro_spacebar", LANGUAGE))
    yield sleep(1.0)

    max_tries = 3
    for attempt in range(1, max_tries + 1):
        yield text_to_speech(session_wamp, t("intro_ready_prompt", LANGUAGE))
        yield sleep(0.5)
        reset_done_signal()

        transcript, latency, speech_detected = yield listen_for_response()        
        log.info(f"Introduction response: '{transcript}'")

        if _is_yes(transcript) or was_done_signalled():
            yield text_to_speech(session_wamp, t("intro_lets_start", LANGUAGE))
            yield sleep(0.8)
            returnValue(True)

        elif _is_no(transcript):
            if attempt < max_tries:
                yield text_to_speech(session_wamp, t("intro_explain_again", LANGUAGE))
                yield sleep(1.0)
            else:
                yield text_to_speech(session_wamp, t("intro_figure_it_out", LANGUAGE))
                yield sleep(0.8)
                returnValue(True)

        else:
            if attempt < max_tries:
                yield text_to_speech(session_wamp, t("intro_catch_again", LANGUAGE))
            else:
                yield text_to_speech(session_wamp, t("intro_give_it_try", LANGUAGE))
                yield sleep(0.8)
                returnValue(True)

    returnValue(True)


@inlineCallbacks
def run_session(session_wamp, tasks: list):
    state = SessionState()
    counter = {}  
    display = ImageDisplay()

    yield introduction(session_wamp)

    for task in tasks:
        target = task["target_word"]
        label = task.get("display_label", f"Show picture: {target}")
        sem_hints = {target.lower(): task["semantic_hint"]} if "semantic_hint" in task else None
        accepted_answers = task.get("accepted_answers", [target])

        state.current_item = task.get("id", target)
        state.target_word = target
        state.attempt_number = 0
        state.items_total += 1
        log.info(f"Item '{target}' | {label}")

        display.show(task.get("image_key", target))
        yield play_behavior(session_wamp, "BlocklyLeftArmSide")

        yield text_to_speech(session_wamp, t("look_at_picture", LANGUAGE))
        yield sleep(PAUSE_AFTER_PROMPT)

        prev_error = None
        consecutive_unintel = 0 
        attempt = 0 

        while attempt < MAX_ATTEMPTS_PER_ITEM:
            attempt += 1
            state.attempt_number = attempt
            reset_done_signal() 
            transcript, latency, speech_detected = yield listen_for_response()

            user_state = build_user_state(
                transcript = transcript,
                target_word = target,
                latency = latency,
                attempt_number = attempt,
                accepted_answers = accepted_answers,
                speech_detected = speech_detected
            )

            rb_error = detect_error_type(transcript, target, latency).value

            log.info(
                f"Attempt {attempt} | "
                f"error={user_state.error_type.value} | "
                f"latency={latency:.1f}s"
            )

            trial = {
                "item":           target,
                "attempt":        attempt,
                "timestamp":      round(time.time(), 3),
                "transcript":     transcript,
                "latency":        round(latency, 2),
                "asr_confidence": round(user_state.asr_confidence, 3),
                "error_type":     user_state.error_type.value,
                "error_type_rb":  rb_error,
                "feedback_given": None,
            }

            if user_state.error_type == ErrorType.UNINTELLIGIBLE:
                consecutive_unintel += 1
                trial["feedback_given"] = FeedbackType.CLARIFICATION.value
                state.session_log.append(trial)

                if consecutive_unintel >= 2:
                    log.info("2 consecutive unintelligible responses")
                    speech = resolve_text(
                        FeedbackType.EXPLICIT_CORRECTION, target, counter, sem_hints, "", LANGUAGE
                    )
                    yield text_to_speech(session_wamp, speech)
                    break

                yield play_behavior(session_wamp, "BlocklyShrug")
                speech = resolve_text(FeedbackType.CLARIFICATION, target, counter, sem_hints, "", LANGUAGE)
                yield text_to_speech(session_wamp, speech)
                yield sleep(PAUSE_BETWEEN_ATTEMPTS)
                reset_done_signal()
                attempt -= 1 
                continue
            
            consecutive_unintel = 0

            if user_state.error_type == ErrorType.CORRECT:
                state.items_correct += 1
                fb = FeedbackType.CONFIRMATION
                trial["feedback_given"] = fb.value
                state.session_log.append(trial)
                speech = yield deferToThread(resolve_text, fb, target, counter, sem_hints, user_state.transcript, LANGUAGE)
                yield play_behavior(session_wamp, "BlocklyApplause")
                yield text_to_speech(session_wamp, speech)

                break

            if attempt == MAX_ATTEMPTS_PER_ITEM:
                log.info("Max attempts reached.")
                fb = FeedbackType.EXPLICIT_CORRECTION
                trial["feedback_given"] = fb.value
                state.session_log.append(trial)
                speech = yield deferToThread(resolve_text, fb, target, counter, sem_hints, user_state.transcript, LANGUAGE)
                yield text_to_speech(session_wamp, speech)
                break

            fb = select_feedback(user_state, target_word=target, prev_error=prev_error)
            speech = yield deferToThread(resolve_text, fb, target, counter, sem_hints, user_state.transcript, LANGUAGE)
            trial["feedback_given"] = fb.value
            state.session_log.append(trial)

            if fb == FeedbackType.CLARIFICATION:
                yield play_behavior(session_wamp, "BlocklyShrug")

            yield text_to_speech(session_wamp, speech)
            yield sleep(PAUSE_BETWEEN_ATTEMPTS)

            prev_error = user_state.error_type

    display.close()

    yield text_to_speech(session_wamp, t("session_end", LANGUAGE))
    yield play_behavior(session_wamp, "BlocklyWaveRightArm")
    yield sleep(PAUSE_END_SESSION)

    returnValue(state)
