from dataclasses import dataclass, field
from enum import Enum
import time

class ErrorType(str, Enum):
    SILENCE = "SILENCE"
    UNINTELLIGIBLE = "UNINTELLIGIBLE"
    CORRECT = "CORRECT"
    PHONOLOGICAL_ERROR = "PHONOLOGICAL_ERROR"
    SEMANTIC_ERROR = "SEMANTIC_ERROR"
    CIRCUMLOCUTION = "CIRCUMLOCUTION"
    NEOLOGISM = "NEOLOGISM"
    PARTIAL_ATTEMPT = "PARTIAL_ATTEMPT"


class FeedbackType(str, Enum):
    CONFIRMATION = "CON"
    ELICITATION = "ELI"
    ELICITATION_CIRCUMLOCUTION = "ELI_CIR"
    ELICITATION_SEMANTIC = "ELI_SEM"
    ELICITATION_PHONOLOGICAL = "ELI_PHO"
    PHONOLOGICAL_CUE = "PHO"
    SEMANTIC_CUE = "SEM"
    EXPLICIT_CORRECTION = "EXP"
    CLARIFICATION = "CLR"
    WAIT = "WAIT"

@dataclass
class UserState:
    error_type: ErrorType
    attempt_number: int
    transcript: str = ""
    latency: float = 0.0
    asr_confidence: float = 0.0


@dataclass
class SessionState:
    current_item: str = ""
    target_word: str = ""
    attempt_number: int = 0
    items_correct: int = 0
    items_total: int = 0
    session_log: list  = field(default_factory=list)
    session_start_time: float = field(default_factory=time.time)
