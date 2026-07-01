from models import FeedbackType

FEEDBACK_SCRIPTS: dict[FeedbackType, list[str]] = {

    FeedbackType.CONFIRMATION: [
        "Yes, {word}! Well done.",
        "That's right, {word}! Great job.",
        "Exactly, {word}. Perfect.",
        "Yes! {word}. Wonderful.",
    ],

    FeedbackType.ELICITATION: [
        "Take your time. Can you try again?",
        "You are doing well. Give it another go.",
    ],

    FeedbackType.ELICITATION_CIRCUMLOCUTION: [
        "You're describing it well. Can you think of the name?",
        "Good description. What is the word for it?",
        "I can see you know what it is. Can you say the word?",
    ],

    FeedbackType.ELICITATION_SEMANTIC: [
        "That's related. Can you think of the exact word?",
        "You're in the right area. What is the specific word?",
        "Close! Can you find the exact name?",
    ],

    FeedbackType.ELICITATION_PHONOLOGICAL: [
        "You've got part of it. Try saying the full word.",
        "Almost! Can you say the whole word?",
        "Good start. Try once more from the beginning.",
    ],

    FeedbackType.CLARIFICATION: [
        "Sorry, I did not quite catch that. Could you say it again?",
        "Can you repeat that for me please?",
    ],

    FeedbackType.WAIT: [
        "Take all the time you need.",
        "No rush. I am listening.",
    ],
}


def build_pho_cue(target_word: str, shared_prefix: int, shared_suffix: int,
                  stem: str, ending: str, first_phone: str) -> str:
    if shared_prefix >= 2 and shared_prefix > shared_suffix:
        return f"Good start, you've got the beginning right. It starts with '{stem}...'."
    if shared_suffix >= 2 and shared_suffix > shared_prefix:
        return f"You've got the ending right. It finishes with '...{ending}'."
    if first_phone:
        return f"It starts with the sound {first_phone.lower()}..."
    return f"It starts with the letter {target_word[0].upper()}."

def build_sem_cue(hint: str | None) -> str:
    if hint:
        return f"Here is a hint. {hint}"
    return "Think about what you use it for, or what category it belongs to."


def build_exp_correction(target_word: str) -> str:
    return f"The word we are looking for is... {target_word}."
