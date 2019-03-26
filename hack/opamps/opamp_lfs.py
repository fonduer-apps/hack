from fonduer.utils.data_model_utils import (
    get_aligned_ngrams,
    get_col_ngrams,
    get_cell_ngrams,
    get_head_ngrams,
    get_horz_ngrams,
    get_left_ngrams,
    get_neighbor_sentence_ngrams,
    get_neighbor_cell_ngrams,
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


def neg_low_page_num(c):
    if get_page(c[0]) > 8:
        return FALSE

    return ABSTAIN


# Gain LFs
def pos_gain(c):
    row_ngrams = set(get_row_ngrams(c.gain, lower=True))
    if overlap(["gain", "bandwidth", "unity"], row_ngrams):
        return TRUE
    else:
        ABSTAIN


def pos_gain_keywords(c):
    return (
        TRUE
        if overlap(["typ", "typ."], get_col_ngrams(c.gain, lower=True))
        else ABSTAIN
    )


def neg_gain_keywords_in_cell(c):
    return (
        FALSE
        if overlap(
            ["g", "vo", "vpp", "f=", "f", "="], get_cell_ngrams(c.gain, lower=True)
        )
        else ABSTAIN
    )


def neg_gain_too_many_words_in_cell(c):
    cell_ngrams = list(get_cell_ngrams(c.gain))
    if len(cell_ngrams) >= 4:
        return FALSE
    else:
        ABSTAIN


def neg_gain_keywords_in_right_cell(c):
    right_ngrams = set(
        [
            x[0]
            for x in get_neighbor_cell_ngrams(
                c[0], n_max=1, dist=5, directions=True, lower=False
            )
            if x[-1] == "RIGHT"
        ]
    )
    if not overlap(["kHz", "MHz", "GHz"], right_ngrams):
        return FALSE

    return ABSTAIN


def neg_gain_keywords_in_row(c):
    return (
        FALSE
        if overlap(
            [
                "small",
                "full",
                "flat",
                "current",
                "thd",
                "signal",
                "flatness",
                "input",
                "noise",
                "f=",
                "f",
                "-3",
                "power",
                "db",
                "dbm",
                "output",
                "impedence",
                "delay",
                "capacitance",
                "range",
                "ratio",
                "dbc",
                "temperature",
                "common",
                "voltage",
                "range",
            ],
            get_row_ngrams(c.gain, lower=True),
        )
        else ABSTAIN
    )


def neg_gain_keywords_in_column(c):
    return (
        FALSE
        if overlap(
            [
                "max",
                "min",
                "test",
                "condition",
                "conditions",
                "vgn",
                "f",
                "-3",
                "db",
                "dbc",
            ],
            get_col_ngrams(c.gain, lower=True),
        )
        else ABSTAIN
    )


# Supply Current LFs
def pos_current(c):
    row_ngrams = list(get_row_ngrams(c.supply_current))
    keywords = ["supply", "quiescent", "iq", "is", "idd"]
    return TRUE if overlap(keywords, row_ngrams) else ABSTAIN


def pos_current_units(c):
    row_ngrams = list(get_row_ngrams(c.supply_current))
    current_units = ["ma", "μa", "ua", "µa", "\uf06da"]
    return TRUE if overlap(current_units, row_ngrams) else ABSTAIN


def pos_current_typ(c):
    return (
        TRUE
        if overlap(["typ", "typ."], get_col_ngrams(c.supply_current, lower=True))
        else ABSTAIN
    )


def neg_current_keywords_in_column(c):
    return (
        FALSE
        if overlap(
            ["over", "temperature", "vgn", "f", "-3", "db", "dbc", "min", "max"],
            get_col_ngrams(c.supply_current, lower=True),
        )
        else ABSTAIN
    )


def neg_current_keywords_in_vert(c):
    return (
        FALSE
        if overlap(
            ["over", "temperature", "vgn", "f", "-3", "db", "dbc", "min", "max"],
            get_vert_ngrams(c.supply_current, lower=True),
        )
        else ABSTAIN
    )


def neg_current_keywords_in_row(c):
    return (
        FALSE
        if overlap(
            ["output", "drive", "voltage", "io"],
            get_row_ngrams(c.supply_current, lower=True),
        )
        else ABSTAIN
    )


gain_lfs = [
    pos_gain,
    pos_gain_keywords,
    neg_gain_keywords_in_row,
    neg_gain_keywords_in_column,
    neg_gain_keywords_in_cell,
    neg_gain_keywords_in_right_cell,
    neg_gain_too_many_words_in_cell,
    neg_low_page_num,
]

current_lfs = [
    pos_current,
    pos_current_units,
    pos_current_typ,
    neg_current_keywords_in_row,
    neg_current_keywords_in_vert,
    neg_current_keywords_in_column,
    neg_low_page_num,
]
