from models import FeedbackType

FEEDBACK_SCRIPTS: dict[FeedbackType, list[str]] = {

    FeedbackType.CONFIRMATION: [
        "Ja, {word}! Goed gedaan.",
        "Precies, {word}! Heel goed.",
        "Exact, {word}. Perfect.",
        "Ja! {word}. Geweldig.",
    ],

    FeedbackType.ELICITATION: [
        "Neem de tijd. Kun je het nog een keer proberen?",
        "Je doet het goed. Probeer het nog eens.",
    ],

    FeedbackType.ELICITATION_CIRCUMLOCUTION: [
        "Je beschrijft het goed. Kun je aan de naam denken?",
        "Goede beschrijving. Wat is het woord ervoor?",
        "Ik zie dat je weet wat het is. Kun je het woord zeggen?",
    ],

    FeedbackType.ELICITATION_SEMANTIC: [
        "Dat is gerelateerd. Kun je aan het exacte woord denken?",
        "Je zit in de goede richting. Wat is het specifieke woord?",
        "Bijna! Kun je de exacte naam vinden?",
    ],

    FeedbackType.ELICITATION_PHONOLOGICAL: [
        "Je hebt een deel te pakken. Probeer het hele woord te zeggen.",
        "Bijna! Kun je het hele woord zeggen?",
        "Goede start. Probeer het nog een keer van het begin.",
    ],

    FeedbackType.CLARIFICATION: [
        "Sorry, ik heb je niet goed verstaan. Kun je het herhalen?",
        "Kun je dat alsjeblieft voor me herhalen?",
    ],

    FeedbackType.WAIT: [
        "Neem alle tijd die je nodig hebt.",
        "Geen haast. Ik luister.",
    ],
}


def build_pho_cue(target_word: str, syllable_info: str, shared_prefix: int,
                  shared_suffix: int, stem: str, ending: str, first_phone: str) -> str:
    if shared_prefix >= 2 and shared_prefix > shared_suffix:
        return f"Goed begin, je hebt het begin goed. Het begint met '{stem}...'. {syllable_info}"
    if shared_suffix >= 2 and shared_suffix > shared_prefix:
        return f"Je hebt het einde goed. Het eindigt met '...{ending}'. {syllable_info}"
    if first_phone:
        return f"Het begint met het geluid {first_phone.lower()}... {syllable_info}"
    return f"Het begint met de letter {target_word[0].upper()}."


def build_sem_cue(hint: str | None) -> str:
    if hint:
        return f"Hier is een aanwijzing. {hint}"
    return "Denk na over waarvoor je het gebruikt, of tot welke categorie het behoort."


def build_exp_correction(target_word: str) -> str:
    return f"Het woord dat we zoeken is... {target_word}."