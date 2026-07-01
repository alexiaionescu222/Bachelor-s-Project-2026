WAMP_URL   = "ws://wamp.robotsindeklas.nl"
WAMP_REALM = "rie.6a2961c48a2cba4f82b87e90"

LANGUAGE = "en" # en or nl
WHISPER_LANGUAGE = "en"

# whisper
WHISPER_MODEL_SIZE = "small" #small or medium are better but slower
AUDIO_SAMPLE_RATE = 16000 

# max recording duration per attempt
MAX_RECORD_SECONDS = 15

# silence detection for stopping the recording
SILENCE_THRESHOLD  = 0.005 # maybe play with this (smaller = better)
SILENCE_DURATION   = 15.0 # maybe even higher    
SILENCE_CHUNK_SIZE = 1024  


# Seconds before a response is classified as no response
RESPONSE_LATENCY_THRESHOLD = 15.0 

# similarity thresholds
STRING_CORRECT_THRESHOLD  = 0.85   # character-level match
SEMANTIC_LOW_THRESHOLD    = 0.50   # embedding cosine similarity lower bound
SEMANTIC_HIGH_THRESHOLD   = 0.90   # upper bound (above this overlaps with string match)

MAX_ATTEMPTS_PER_ITEM = 4 

PAUSE_AFTER_PROMPT     = 0.2
PAUSE_BETWEEN_ATTEMPTS = 1.0
PAUSE_END_SESSION      = 1.0

DONE_KEY = " "   # spacebar

USE_CLASSIFIER = True
CLASSIFIER_MODEL_PATH = "error_classifier.pkl"

TASKS_FILES = {
    "en": "tasks_en.json",
    "nl": "tasks_nl.json",
}