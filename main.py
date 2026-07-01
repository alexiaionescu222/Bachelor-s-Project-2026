import logging
from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.component import Component, run
from stt import load_whisper
from session import load_tasks, run_session, save_session_log
from config import WAMP_URL, WAMP_REALM, LANGUAGE, TASKS_FILES, CLASSIFIER_MODEL_PATH
from state_detection import preload_models
from classifier_detection import load_classifier


logging.basicConfig(  
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("main")

@inlineCallbacks
def main(session, details):
    log.info(f"WAMP session joined. Language: {LANGUAGE.upper()}")
    yield session.call("rie.dialogue.config.language", lang=LANGUAGE)
 
    tasks_path = TASKS_FILES.get(LANGUAGE, "tasks_en.json")
    try:
        tasks = load_tasks(tasks_path)
    except FileNotFoundError:
        log.error(f"Task file '{tasks_path}' not found.")           
        session.leave()           
        return

    session_state = yield run_session(session, tasks)
    save_session_log(session_state)
 
    session.leave()

wamp = Component(
    transports=[{
        "url":         WAMP_URL,
        "serializers": ["msgpack"],
        "max_retries": 0,
    }],
    realm=WAMP_REALM,
)
wamp.on_join(main)

if __name__ == "__main__":
    load_whisper()
    preload_models()    
    load_classifier(CLASSIFIER_MODEL_PATH)
    run([wamp])