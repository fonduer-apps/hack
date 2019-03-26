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

ABSTAIN = 0
FALSE = 1
TRUE = 2


# Gain LFs
def pos_gain(c):
    return TRUE if "gain" in get_row_ngrams(c.gain) else ABSTAIN


def pos_gain_keywords(c):
    return (
        TRUE
        if overlap(["typ", "typ."], [_.lower() for _ in get_col_ngrams(c.gain) if _])
        else ABSTAIN
    )


def neg_gain_keywords_in_row(c):
    return (
        FALSE
        if overlap(
            ["small", "signal", "input", "noise", "f=", "f", "-3", "db", "dbm", "dbc", "voltage", "range"],
            [_.lower() for _ in get_row_ngrams(c.gain) if _],
        )
        else ABSTAIN
    )


def neg_gain_keywords_in_column(c):
    return (
        FALSE
        if overlap(
            ["condition", "conditions", "vgn", "f", "-3", "db", "dbc"],
            [_.lower() for _ in get_col_ngrams(c.gain) if _],
        )
        else ABSTAIN
    )


# Supply Current LFs
def pos_current(c):
    return TRUE if "current" in get_row_ngrams(c.supply_current) else ABSTAIN

def neg_current_keywords_in_column(c):
    return (
        FALSE
        if overlap(
            ["over", "temperature", "vgn", "f", "-3", "db", "dbc"],
            [_.lower() for _ in get_col_ngrams(c.gain) if _],
        )
        else ABSTAIN
    )


opamp_lfs = [
    pos_gain,
    pos_gain_keywords,
    pos_current,
    neg_gain_keywords_in_row,
    neg_gain_keywords_in_column,
]
