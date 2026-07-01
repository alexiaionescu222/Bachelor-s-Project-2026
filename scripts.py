STRINGS: dict[str, dict[str, str]] = {

    "intro_greeting": {
        "en": (
            "Hi! I am Alpha Mini. I am happy to see you today.  "
            "We are going to play a naming game together."
        ),
        "nl": (
            "Hallo! Ik ben Alpha Mini. Ik ben blij je vandaag te zien.  "
            "We gaan samen een benoemspel spelen."
        ),
    },
    "intro_explain": {
        "en": (
            "Here is how it works. "
            "I will show you a picture of an object. "
            "Your job is to say the name of the object you see out loud. "
        ),
        "nl": (
            "Zo werkt het. "
            "Ik laat je een afbeelding van een voorwerp zien. "
            "Jouw taak is om de naam van het voorwerp hardop te zeggen. "
        ),
    },
    "intro_spacebar": {
        "en": (
            "When you are done speaking, press the space bar on the keyboard. "
            "That tells me you have finished, and I will listen to what you said. "
            "So speak first... then press the space bar."
        ),
        "nl": (
            "Als je klaar bent met spreken, druk dan op de spatiebalk op het toetsenbord. "
            "Dat vertelt me dat je klaar bent, en dan luister ik naar wat je hebt gezegd. "
            "Spreek dus eerst... en druk dan op de spatiebalk."
        ),
    },
    "intro_ready_prompt": {
        "en": "Do you understand? Press the space bar if you are ready to start.",
        "nl": "Begrijp je het? Zeg ja als je klaar bent, of druk op de spatiebalk.",
    },
    "intro_lets_start": {
        "en": (
            "Wonderful! Let us start. Take your time with each picture. "
            "There are no wrong answers. Just do your best."
        ),
        "nl": (
            "Geweldig! Laten we beginnen. Neem de tijd voor elke afbeelding. "
            "Er zijn geen foute antwoorden. Doe gewoon je best."
        ),
    },
    "intro_explain_again": {
        "en": (
            "No problem. Let me explain again. "
            "I will show you a picture. "
            "You say the name of the object. "
            "Then press the space bar when you are done. "
            "For example, if you see a picture of a dog, you say... dog, and then press the space bar."
        ),
        "nl": (
            "Geen probleem. Ik leg het nog een keer uit. "
            "Ik laat je een afbeelding zien. "
            "Jij zegt de naam van het voorwerp. "
            "Druk daarna op de spatiebalk als je klaar bent. "
            "Als je bijvoorbeeld een afbeelding van een hond ziet, zeg je... hond, en dan druk je op de spatiebalk."
        ),
    },
    "intro_figure_it_out": {
        "en": "That is okay. We will figure it out together. Let us start!",
        "nl": "Dat is prima. We redden ons wel samen. Laten we beginnen!",
    },
    "intro_catch_again": {
        "en": "Sorry, I did not catch that. Please say yes if you are ready or press the space bar.",
        "nl": "Sorry, ik heb je niet goed verstaan. Zeg ja als je klaar bent, of druk op de spatiebalk.",
    },
    "intro_give_it_try": {
        "en": "Okay, let us give it a try!",
        "nl": "Oké, laten we het proberen!",
    },

    "look_at_picture": {
        "en": "Look at the picture. What is this?",
        "nl": "Kijk naar de afbeelding. Wat is dit?",
    },
    "session_end": {
        "en": (
            "Great work today! "
            "It was really nice spending time with you. "
            "See you next time!"
        ),
        "nl": (
            "Goed gedaan vandaag! "
            "Het was erg leuk om tijd met je door te brengen. "
            "Tot de volgende keer!"
        ),
    },

    "yes_words": {
        "en": {"yes", "yeah", "yep", "yup", "sure", "ok", "okay",
               "ready", "understand", "understood", "right", "correct", "go", "do"},
        "nl": {"ja", "jep", "jap", "oké", "ok", "goed", "klaar",
               "begrijp", "begrepen", "zeker", "prima", "doen", "start"},
    },
    "no_words": {
        "en": {"no", "nope", "not", "don't", "dont", "what", "huh",
               "again", "repeat", "sorry", "pardon"},
        "nl": {"nee", "nee", "niet", "wat", "hè", "opnieuw",
               "herhaal", "sorry", "pardon"},
    },
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    entry = STRINGS.get(key, {})
    value = entry.get(lang, entry.get("en", f"[missing: {key}]"))
    if kwargs and isinstance(value, str):
        value = value.format(**kwargs)
    return value
