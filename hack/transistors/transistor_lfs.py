import re
from itertools import chain

from fonduer.utils.data_model_utils import (
    get_aligned_ngrams,
    get_col_ngrams,
    get_head_ngrams,
    get_horz_ngrams,
    get_left_ngrams,
    get_neighbor_sentence_ngrams,
    get_page,
    get_page_vert_percentile,
    get_right_ngrams,
    get_row_ngrams,
    get_sentence_ngrams,
    get_tag,
    get_vert_ngrams,
    is_horz_aligned,
    is_vert_aligned,
    overlap,
    same_col,
    same_row,
    same_table,
)

from hack.transistors.transistor_spaces import expand_part_range

ABSTAIN = 0
FALSE = 1
TRUE = 2


def _filter_non_polarity(c):
    ret = set()
    for _ in c:
        if re.match(r"NPN|PNP", _):
            ret.add(_)
    return ret


def _filter_non_parts(c):
    ret = set()
    for _ in c:
        for __ in expand_part_range(_):
            if re.match("^([0-9]+[A-Z]+|[A-Z]+[0-9]+)[0-9A-Z]*$", __) and len(__) > 2:
                ret.add(__)

    return ret


# STORAGE TEMP LFS
def LF_storage_row(c):
    return TRUE if "storage" in get_row_ngrams(c[1]) else ABSTAIN


def LF_temperature_row(c):
    return TRUE if "temperature" in get_row_ngrams(c[1]) else ABSTAIN


def LF_operating_row(c):
    return FALSE if "operating" in get_row_ngrams(c[1]) else ABSTAIN


def LF_tstg_row(c):
    return (
        TRUE if overlap(["tstg", "stg", "ts"], list(get_row_ngrams(c[1]))) else ABSTAIN
    )


def LF_to_left(c):
    return TRUE if "to" in get_left_ngrams(c[1], window=2) else ABSTAIN


def LF_to_right(c):
    return TRUE if "to" in get_right_ngrams(c[1], window=2) else ABSTAIN


def LF_negative_number_left(c):
    return (
        TRUE
        if any(
            [re.match(r"-\s*\d+", ngram) for ngram in get_left_ngrams(c[1], window=4)]
        )
        else ABSTAIN
    )


def LF_positive_number_right(c):
    return (
        TRUE
        if any([re.match(r"\d+", ngram) for ngram in get_right_ngrams(c[1], window=4)])
        else ABSTAIN
    )


def LF_test_condition_aligned(c):
    return (
        FALSE
        if overlap(["test", "condition"], list(get_aligned_ngrams(c[1])))
        else ABSTAIN
    )


def LF_collector_aligned(c):
    return (
        FALSE
        if overlap(
            ["collector", "collector-current", "collector-base", "collector-emitter"],
            list(get_aligned_ngrams(c[1])),
        )
        else ABSTAIN
    )


def LF_current_aligned(c):
    return (
        FALSE
        if overlap(["current", "dc", "ic"], list(get_aligned_ngrams(c[1])))
        else ABSTAIN
    )


def LF_voltage_row_temp(c):
    return (
        FALSE
        if overlap(
            ["voltage", "cbo", "ceo", "ebo", "v"], list(get_aligned_ngrams(c[1]))
        )
        else ABSTAIN
    )


def LF_voltage_row_part(c):
    return (
        FALSE
        if overlap(
            ["voltage", "cbo", "ceo", "ebo", "v"], list(get_aligned_ngrams(c[1]))
        )
        else ABSTAIN
    )


def LF_typ_row(c):
    return FALSE if overlap(["typ", "typ."], list(get_row_ngrams(c[1]))) else ABSTAIN


def LF_complement_left_row(c):
    return (
        FALSE
        if (
            overlap(
                ["complement", "complementary"],
                chain.from_iterable(
                    [get_row_ngrams(c.part), get_left_ngrams(c.part, window=10)]
                ),
            )
        )
        else ABSTAIN
    )


def LF_too_many_numbers_row(c):
    num_numbers = list(get_row_ngrams(c[1], attrib="ner_tags")).count("number")
    return FALSE if num_numbers >= 3 else ABSTAIN


def LF_temp_on_high_page_num(c):
    return FALSE if c[1].context.get_attrib_tokens("page")[0] > 2 else ABSTAIN


def LF_not_temp_relevant(c):
    return (
        FALSE
        if not overlap(
            ["storage", "temperature", "tstg", "stg", "ts"],
            list(get_aligned_ngrams(c[1])),
        )
        else ABSTAIN
    )


def LF_other_minus_signs_in_row(c):
    return FALSE if "-" in get_row_ngrams(c[1]) else ABSTAIN


stg_temp_lfs = [
    LF_collector_aligned,
    #  LF_complement_left_row,
    LF_current_aligned,
    LF_not_temp_relevant,
    LF_operating_row,
    LF_storage_row,
    LF_temp_on_high_page_num,
    LF_temperature_row,
    #  LF_test_condition_aligned,
    #  LF_too_many_numbers_row,
    LF_tstg_row,
    #  LF_typ_row,
    LF_voltage_row_part,
    LF_voltage_row_temp,
]

stg_temp_max_lfs = stg_temp_lfs + [LF_to_left, LF_negative_number_left]
stg_temp_min_lfs = stg_temp_lfs + [
    LF_to_right,
    LF_positive_number_right,
    LF_other_minus_signs_in_row,
]


# Polarity LFS
def LF_polarity_part_tabular_aligned(c):
    return TRUE if same_row(c) or same_col(c) else ABSTAIN


def LF_polarity_part_viz_aligned(c):
    return TRUE if is_horz_aligned(c) or is_vert_aligned(c) else ABSTAIN


def LF_polarity_part_in_top_third(c):
    return (
        TRUE
        if (
            get_page(c.part) == 1
            and get_page(c[1])
            and get_page_vert_percentile(c.part) > 0.33
            and get_page_vert_percentile(c[1]) > 0.33
        )
        else ABSTAIN
    )


def LF_polarity_description(c):
    aligned_ngrams = set(get_aligned_ngrams(c[1]))
    return TRUE if overlap(["description", "polarity"], aligned_ngrams) else ABSTAIN


def LF_polarity_transistor_type(c):
    return (
        TRUE
        if overlap(
            [
                "silicon",
                "power",
                "darlington",
                "epitaxial",
                "low noise",
                "ampl/switch",
                "switch",
                "surface",
                "mount",
            ],
            chain.from_iterable(
                [get_sentence_ngrams(c[1]), get_neighbor_sentence_ngrams(c[1])]
            ),
        )
        else ABSTAIN
    )


def LF_polarity_right_of_part(c):
    right_ngrams = set(get_right_ngrams(c.part, lower=False))
    return (
        TRUE
        if (
            (c[1].context.get_span() == "NPN" and "NPN" in right_ngrams)
            or (c[1].context.get_span() == "PNP" and "PNP" in right_ngrams)
        )
        else ABSTAIN
    )


def LF_polarity_in_header_tag(c):
    return TRUE if get_tag(c[1]).startswith("h") else ABSTAIN


def LF_polarity_complement(c):
    return (
        FALSE
        if overlap(
            ["complement", "complementary"],
            chain.from_iterable(
                [get_sentence_ngrams(c[1]), get_neighbor_sentence_ngrams(c[1])]
            ),
        )
        else ABSTAIN
    )


def LF_cheating_with_another_polarity(c):
    return (
        FALSE
        if (
            (
                c[1].context.get_span() == "NPN"
                and "PNP" in get_horz_ngrams(c.part, lower=False)
            )
            or (
                c[1].context.get_span() == "PNP"
                and "NPN" in get_horz_ngrams(c.part, lower=False)
            )
        )
        else ABSTAIN
    )


def LF_both_present(c):
    sentence_ngrams = set(get_sentence_ngrams(c[1]))
    return FALSE if ("npn" in sentence_ngrams and "pnp" in sentence_ngrams) else ABSTAIN


def LF_part_miss_match_part(c):
    if not c[1].context.sentence.is_tabular():
        return ABSTAIN
    ngrams_part = set(list(get_row_ngrams(c[1], n_max=1, lower=False)))
    ngrams_part = _filter_non_parts(ngrams_part)
    return (
        ABSTAIN
        if len(ngrams_part) == 0
        or any(
            [
                c.part.context.get_span().lower().startswith(_.lower())
                for _ in ngrams_part
            ]
        )
        else FALSE
    )


def LF_part_miss_match_polarity(c):
    ngrams_part = set(list(get_row_ngrams(c.part, n_max=1, lower=False)))
    ngrams_part = _filter_non_polarity(ngrams_part)
    return (
        ABSTAIN
        if len(ngrams_part) == 0
        or any(
            [c[1].context.get_span().lower().startswith(_.lower()) for _ in ngrams_part]
        )
        else FALSE
    )


polarity_lfs = [
    # LF_polarity_description,
    LF_polarity_transistor_type,
    LF_polarity_part_tabular_aligned,
    LF_polarity_part_viz_aligned,
    LF_polarity_right_of_part,
    # LF_both_in_top_third,
    LF_polarity_in_header_tag,
    LF_polarity_complement,
    LF_both_present,
]


# ce_v_max lfs
def LF_aligned_or_global(c):
    return (
        TRUE
        if (same_row(c) or is_horz_aligned(c) or not c.part.sentence.is_tabular())
        else FALSE
    )


def LF_same_table_must_align(c):
    return (
        FALSE
        if (same_table(c) and not (is_horz_aligned(c) or is_vert_aligned(c)))
        else ABSTAIN
    )


def LF_voltage_not_in_table(c):
    return FALSE if not c[1].context.sentence.is_tabular() else ABSTAIN


def LF_low_table_num(c):
    return (
        FALSE
        if (c[1].context.sentence.is_tabular() and c[1].parent.table.position > 2)
        else ABSTAIN
    )


_BAD_VOLT_KEYWORDS = set(["continuous", "cut-off", "gain", "breakdown"])


def LF_bad_keywords_in_row(c):
    return FALSE if overlap(_BAD_VOLT_KEYWORDS, get_row_ngrams(c[1])) else ABSTAIN


def LF_equals_in_row(c):
    return FALSE if overlap("=", get_row_ngrams(c[1])) else ABSTAIN


def LF_current_in_row(c):
    return FALSE if overlap(["i", "ic", "mA"], get_row_ngrams(c[1])) else ABSTAIN


def LF_V_aligned(c):
    return TRUE if overlap("V", get_aligned_ngrams(c, lower=False)) else ABSTAIN


def LF_too_many_numbers_horz(c):
    num_numbers = list(get_horz_ngrams(c[1], attrib="ner_tags")).count("number")
    return FALSE if num_numbers > 3 else ABSTAIN


voltage_lfs = [
    # LF_aligned_or_global,
    # LF_same_table_must_align,
    # LF_low_table_num,
    LF_voltage_not_in_table,
    LF_bad_keywords_in_row,
    # LF_equals_in_row,
    LF_current_in_row,
    # LF_V_aligned,
    # LF_too_many_numbers_horz
]
_CE_KEYWORDS = set(["collector emitter", "collector-emitter", "collector - emitter"])


def LF_ce_keywords_in_row(c):
    return TRUE if overlap(_CE_KEYWORDS, get_row_ngrams(c[1], n_max=3)) else ABSTAIN


def LF_ce_keywords_horz(c):
    return TRUE if overlap(_CE_KEYWORDS, get_horz_ngrams(c[1])) else ABSTAIN


_CE_ABBREVS = set(["ceo", "vceo"])  # 'value', 'rating'


def LF_ce_abbrevs_in_row(c):
    return TRUE if overlap(_CE_ABBREVS, get_row_ngrams(c[1])) else ABSTAIN


def LF_ce_abbrevs_horz(c):
    return TRUE if overlap(_CE_ABBREVS, get_horz_ngrams(c[1])) else ABSTAIN


def LF_head_ends_with_ceo(c):
    return (
        TRUE
        if any(ngram.endswith("ceo") for ngram in get_head_ngrams(c[1]))
        else ABSTAIN
    )


_NON_CEV_KEYWORDS = set(
    [
        "collector-base",
        "collector - base",
        "collector base",
        "vcbo",
        "cbo",
        "vces",
        "emitter-base",
        "emitter - base",
        "emitter base",
        "vebo",
        "ebo",
        "breakdown voltage",
        "emitter breakdown",
        "emitter breakdown voltage",
        "current",
    ]
)


def LF_non_ce_voltages_in_row(c):
    return (
        FALSE if overlap(_NON_CEV_KEYWORDS, get_row_ngrams(c[1], n_max=3)) else ABSTAIN
    )


def LF_first_two_pages(c):
    return TRUE if get_page(c) in [1, 2] else FALSE


def LF_part_ce_keywords_in_rows(c):
    return (
        TRUE
        if overlap(_CE_KEYWORDS.union(_CE_ABBREVS), get_row_ngrams(c[1], n_max=3))
        and overlap(
            set([c.part.context.get_span().lower()]), get_row_ngrams(c[1], n_max=3)
        )
        else ABSTAIN
    )


def LF_part_ce_keywords_in_rows_cols_prefix(c):
    ngrams = set(list(get_row_ngrams(c[1], n_max=3)))
    ngrams = ngrams.union(set(list(get_col_ngrams(c[1], n_max=3))))
    ngrams_part = _filter_non_parts(ngrams)
    return (
        TRUE
        if overlap(_CE_KEYWORDS.union(_CE_ABBREVS), ngrams)
        and any([c.part.context.get_span().lower().startswith(_) for _ in ngrams_part])
        else FALSE
    )


def LF_part_ce_keywords_in_rows_cols_prefix_1(c):
    ngrams = set(list(get_horz_ngrams(c[1])))
    ngrams = ngrams.union(set(list(get_vert_ngrams(c[1]))))
    ngrams_part = _filter_non_parts(ngrams)
    return (
        TRUE
        if overlap(_CE_KEYWORDS.union(_CE_ABBREVS), ngrams)
        and any([c.part.context.get_span().lower().startswith(_) for _ in ngrams_part])
        else ABSTAIN
    )


def LF_part_ce_keywords_horz(c):
    return (
        TRUE
        if overlap(_CE_KEYWORDS.union(_CE_ABBREVS), get_horz_ngrams(c[1]))
        and overlap(set([c.part.context.get_span().lower()]), get_horz_ngrams(c[1]))
        else ABSTAIN
    )


def LF_part_ce_keywords_horz_prefix(c):
    return (
        TRUE
        if overlap(_CE_KEYWORDS.union(_CE_ABBREVS), get_horz_ngrams(c[1]))
        and any(
            [
                c.part.context.get_span().lower().startswith(_)
                for _ in get_horz_ngrams(c[1])
            ]
        )
        and not overlap(_NON_CEV_KEYWORDS, get_horz_ngrams(c[1]))
        else ABSTAIN
    )


def LF_part_ce_keywords_in_row_prefix(c):
    ngrams_part = _filter_non_parts(get_row_ngrams(c[1], n_max=3))

    return (
        TRUE
        if overlap(_CE_KEYWORDS.union(_CE_ABBREVS), get_row_ngrams(c[1], n_max=3))
        and any([c.part.context.get_span().lower().startswith(_) for _ in ngrams_part])
        and not overlap(_NON_CEV_KEYWORDS, get_row_ngrams(c[1], n_max=3))
        and not LF_current_in_row(c)
        else ABSTAIN
    )


def LF_part_ce_keywords_in_row_prefix_same_table(c):
    ngrams_part = _filter_non_parts(get_row_ngrams(c[1], n_max=3))

    return (
        TRUE
        if same_table(c)
        and is_horz_aligned(c)
        and overlap(_CE_KEYWORDS.union(_CE_ABBREVS), get_row_ngrams(c[1], n_max=3))
        and overlap(_CE_KEYWORDS.union(_CE_ABBREVS), get_row_ngrams(c.part, n_max=3))
        and any([c.part.context.get_span().lower().startswith(_) for _ in ngrams_part])
        and not overlap(_NON_CEV_KEYWORDS, get_row_ngrams(c.part, n_max=3))
        and not overlap(_NON_CEV_KEYWORDS, get_row_ngrams(c[1], n_max=3))
        and not LF_current_in_row(c)
        else ABSTAIN
    )


def LF_part_ce_keywords_in_col_prefix_same_table(c):
    return (
        TRUE
        if same_table(c)
        and is_vert_aligned(c)
        and overlap(_CE_KEYWORDS.union(_CE_ABBREVS), get_row_ngrams(c[1], n_max=3))
        and not overlap(_NON_CEV_KEYWORDS, get_row_ngrams(c[1], n_max=3))
        and not LF_current_in_row(c)
        else FALSE
    )


def LF_ce_keywords_not_part_in_row_col_prefix(c):
    ngrams_part = set(list(get_col_ngrams(c[1], n_max=3)))
    ngrams_part = _filter_non_parts(
        ngrams_part.union(set(list(get_row_ngrams(c[1], n_max=3))))
    )

    return (
        TRUE
        if not same_table(c)
        and overlap(_CE_KEYWORDS.union(_CE_ABBREVS), get_row_ngrams(c[1], n_max=3))
        and len(ngrams_part) == 0
        and not overlap(_NON_CEV_KEYWORDS, get_row_ngrams(c.part, n_max=3))
        and not overlap(_NON_CEV_KEYWORDS, get_row_ngrams(c[1], n_max=3))
        and not LF_current_in_row(c)
        else FALSE
    )


def LF_part_miss_match(c):
    ngrams_part = set(list(get_vert_ngrams(c[1], n_max=1)))
    ngrams_part = _filter_non_parts(
        ngrams_part.union(set(list(get_horz_ngrams(c[1], n_max=1))))
    )
    return (
        ABSTAIN
        if len(ngrams_part) == 0
        or any(
            [
                c.part.context.get_span().lower().startswith(_.lower())
                for _ in ngrams_part
            ]
        )
        else FALSE
    )


def LF_not_valid_value(c):
    return (
        FALSE
        if not overlap(_CE_KEYWORDS.union(_CE_ABBREVS), get_row_ngrams(c[1], n_max=3))
        else ABSTAIN
    )


def LF_ce_keywords_no_part_in_rows(c):
    for _ in get_row_ngrams(c[1], n_max=3):
        if re.match("^([0-9]+[a-zA-Z]+|[a-zA-Z]+[0-9]+)[0-9a-zA-Z]*$", _):
            return ABSTAIN
    return (
        TRUE
        if overlap(_CE_KEYWORDS.union(_CE_ABBREVS), get_row_ngrams(c[1], n_max=3))
        else ABSTAIN
    )


def LF_ce_keywords_no_part_horz(c):
    for _ in get_horz_ngrams(c[1]):
        if re.match("^([0-9]+[a-zA-Z]+|[a-zA-Z]+[0-9]+)[0-9a-zA-Z]*$", _):
            return ABSTAIN
    return (
        TRUE
        if overlap(_CE_KEYWORDS.union(_CE_ABBREVS), get_horz_ngrams(c[1]))
        else ABSTAIN
    )


ce_v_max_lfs = voltage_lfs + [
    # LF_ce_keywords_in_row,
    # LF_ce_keywords_horz,
    # LF_ce_abbrevs_in_row,
    # LF_ce_abbrevs_horz,
    # LF_head_ends_with_ceo,
    LF_non_ce_voltages_in_row,
    # LF_first_two_pages
    # LF_part_ce_keywords_in_rows_cols_prefix,
    LF_part_ce_keywords_in_row_prefix_same_table,
    LF_part_ce_keywords_in_col_prefix_same_table,
    LF_part_miss_match
    # LF_part_ce_keywords_in_row_prefix,
    # LF_ce_keywords_not_part_in_row_col_prefix,
    # LF_part_ce_keywords_horz_prefix
    # LF_not_valid_value
    # LF_ce_keywords_no_part_in_rows,
    # LF_ce_keywords_no_part_horz
]
