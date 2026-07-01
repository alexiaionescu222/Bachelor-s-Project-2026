# Bachelor-s-Thesis-2026

A real-time speech therapy assistant running on the Alpha Mini social robot. The robot presents pictures of common objects to a patient with aphasia and prompts them to name the object aloud. It automatically classifies the patient's response, selects clinically appropriate feedback, and escalates support across attempts if the patient does not self-correct.

**CONTENTS**

main.py              --> Run this for a live session with the robot
config.py            --> All settings (thresholds, language, model paths)
tasks_en.json        --> Naming task items in English
tasks_nl.json        --> Naming task items in Dutch
error_classifier.pkl --> Trained Random Forest model
session_logs/        --> Session output files

**REQUIREMENTS**

- Python 3.10 or higher is required.
- Install all dependencies: 
    pip install -r requirements.txt

**RUNNING A SESSION**
- add the WAMP realm in config.py
- run main.py
- The robot will introduce itself, display stimulus images on the laptop screen, and run through all items in tasks.json. Session logs are saved automatically to session_logs/

**LANGUAGE**
To switch between English and Dutch, change LANGUAGE in config.py:
    LANGUAGE = "en"   # English
    LANGUAGE = "nl"   # Dutch

**CLASSIFIER**
- The system uses a trained Random Forest classifier to detect error types. The trained model file error_classifier.pkl must exist in the project folder.
- If it is missing, run:
    py train_classifier.py
- This trains the classifier on dataset.json and saves error_classifier.pkl.
- The system will also fall back to the rule-based engine automatically if the file is missing.


**SESSION LOGS**
After every session, a JSON file is saved to session_logs/ with a timestamp filename. Each log contains:
- Every attempt: transcript, latency, ASR confidence, error type, feedback given
- Summary statistics: accuracy, mean attempts to correct, feedback distribution, error distribution
- Cue effectiveness: which feedback types led to a correct response on the next attempt