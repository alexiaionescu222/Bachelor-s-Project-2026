import logging
from twisted.internet.defer import inlineCallbacks
from alpha_mini_rug.speech_to_text import SpeechToText

log = logging.getLogger("tts")

@inlineCallbacks
def play_behavior(session, behavior_name: str):
    log.info(f"Behavior: '{behavior_name}'")
    yield session.call("rom.optional.behavior.play", name=behavior_name)


@inlineCallbacks
def text_to_speech(session, text: str):
    log.info(f"TTS = '{text}'")
    SpeechToText.do_speech_recognition = False
    yield session.call("rie.dialogue.say", text=text)
