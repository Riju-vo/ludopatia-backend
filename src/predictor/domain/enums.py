from enum import StrEnum


class MatchStatus(StrEnum):
    FINISHED = "finished"
    SCHEDULED = "scheduled"
    UNKNOWN = "unknown"


class MatchQuality(StrEnum):
    VERIFIED_STANDARD_TIME = "verified_standard_time"
    AMBIGUOUS_EXTRA_TIME = "ambiguous_extra_time"
    INVALID_SCORE = "invalid_score"
    OUT_OF_MODEL_SCOPE = "out_of_model_scope"
    UNKNOWN_REFERENCE = "unknown_reference"
