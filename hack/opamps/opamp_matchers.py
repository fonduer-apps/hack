import logging

from fonduer.candidates.matchers import Intersect, LambdaFunctionMatcher, RegexMatchSpan
from fonduer.utils.data_model_utils import (
    get_page,
    get_row_ngrams,
    get_sentence_ngrams,
    overlap,
)

logger = logging.getLogger(__name__)


def _first_page_or_table(attr):
    """Must be in the first page, or in a table."""
    return get_page(attr) or attr.sentence.is_tabular()


def get_gain_matcher():
    def hertz_units(attr):
        keywords = [
            "gain bandwidth",
            "unity gain",
            "mhz",
            "khz",
            "gbp",
            "gbw",
            "unity bandwidth",
            "bandwidth product",
        ]
        related_ngrams = set(
            [_.lower() for _ in get_sentence_ngrams(attr, n_max=2) if _]
        )
        related_ngrams.update([_.lower() for _ in get_row_ngrams(attr, n_max=2) if _])

        if overlap(keywords, related_ngrams):
            return True

        return False

    # match 3-digit integers, or two-digit floats up with 2 points of precision
    gain_rgx = RegexMatchSpan(
        rgx=r"^(?:\d{1,2}\.\d{1,2}|\d{1,3})$", longest_match_only=False
    )

    hertz_lambda = LambdaFunctionMatcher(func=hertz_units)
    location_lambda = LambdaFunctionMatcher(func=_first_page_or_table)

    return Intersect(gain_rgx, hertz_lambda, location_lambda)


def get_supply_current_matcher():
    def current_units(attr):
        keywords = ["ma", "μa", "a", "supply current", "quiescent", "is"]
        related_ngrams = set(
            [_.lower() for _ in get_sentence_ngrams(attr, n_max=2) if _]
        )
        related_ngrams.update([_.lower() for _ in get_row_ngrams(attr, n_max=2) if _])

        if overlap(keywords, related_ngrams):
            return True

        return False

    # match 4-digit integers, or two-digit floats up with 2 points of precision
    current_rgx = RegexMatchSpan(
        rgx=r"^(?:\d{1,2}\.\d{1,2}|\d{1,4})$", longest_match_only=False
    )

    current_lambda = LambdaFunctionMatcher(func=current_units)
    location_lambda = LambdaFunctionMatcher(func=_first_page_or_table)

    return Intersect(current_rgx, current_lambda, location_lambda)
