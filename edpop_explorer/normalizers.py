from iso639 import Lang
from iso639.exceptions import InvalidLanguageValue
from enum import Enum


class NormalizationResult(Enum):
    SUCCESS = 'success'
    NO_DATA = 'nodata'
    FAIL = 'fail'


def normalize_by_language_code(field) -> NormalizationResult:
    """Normalize using the iso639-lang package, which allows the name of the
    language in English as input, as well as one of the ISO-639 language
    codes."""
    if field.original_text is None:
        return NormalizationResult.NO_DATA
    try:
        language = Lang(field.original_text)
        field.language_code = language.pt3
        return NormalizationResult.SUCCESS
    except InvalidLanguageValue:
        return NormalizationResult.FAIL
