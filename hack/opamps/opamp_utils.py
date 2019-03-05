import codecs
import csv
import logging
import os
import pdb
from collections import namedtuple

from fonduer.utils.data_model_utils import get_row_ngrams
from quantiphy import Quantity

try:
    from IPython import get_ipython

    if "IPKernelApp" not in get_ipython().config:
        raise ImportError("console")
except (AttributeError, ImportError):
    from tqdm import tqdm
else:
    from tqdm import tqdm_notebook as tqdm


logger = logging.getLogger(__name__)

Score = namedtuple("Score", ["f1", "prec", "rec", "TP", "FP", "FN"])


def get_gold_set(docs=None):

    dirname = os.path.dirname(__file__)
    gold_set = set()
    temp_dict = {}
    for filename in [
        os.path.join(dirname, "data/dev/dev_gold.csv"),
        os.path.join(dirname, "data/test/test_gold.csv"),
    ]:
        with codecs.open(filename, encoding="utf-8") as csvfile:
            gold_reader = csv.reader(csvfile)
            for row in gold_reader:
                (doc, part, attr, val) = row
                if doc not in temp_dict:
                    temp_dict[doc] = {"typ_gbp": set(), "typ_supply_current": set()}
                if docs is None or doc.upper() in docs:
                    if attr in ["typ_gbp", "typ_supply_current"]:
                        # Allow the double of a +/- value to be valid also.
                        if val.startswith("±"):
                            (value, unit) = val.split(" ")
                            temp_dict[doc][attr].add(
                                f"{str(2 * float(value[1:]))} {unit}"
                            )
                            temp_dict[doc][attr].add(val[1:])
                        else:
                            temp_dict[doc][attr].add(val)

    # Iterate over the now-populated temp_dict to generate all tuples.
    # We use Quantities to make normalization easier during scoring.

    # NOTE: We are making the perhaps too broad assumptiion that all pairs of
    # true supply currents and GBP in a datasheet are valid.
    for doc, values in temp_dict.items():
        for gain in values["typ_gbp"]:
            for current in values["typ_supply_current"]:
                gold_set.add(
                    (doc.upper(), Quantity(gain), Quantity(current.replace("u", "μ")))
                )

    return gold_set


def entity_confusion_matrix(pred, gold):
    if not isinstance(pred, set):
        pred = set(pred)
    if not isinstance(gold, set):
        gold = set(gold)

    TP = pred.intersection(gold)
    FP = pred.difference(gold)
    FN = gold.difference(pred)
    return (TP, FP, FN)


def cand_to_entity(c):
    doc = c[0].context.sentence.document.name.upper()
    gain = c[0].context.get_span()
    current = c[1].context.get_span()

    gain_ngrams = set(get_row_ngrams(c[0], lower=False))
    # Get a set of the hertz units
    gain_ngrams = set([_ for _ in gain_ngrams if _ in ["kHz", "MHz", "GHz"]])
    if len(gain_ngrams) > 1:
        logger.debug(f"gain_ngrams: {gain_ngrams}")
        return
    elif len(gain_ngrams) == 0:
        return

    current_ngrams = set(get_row_ngrams(c[1], lower=False))
    # Get a set of the current units
    current_ngrams = set([_ for _ in current_ngrams if _ and _.endswith("A")])

    if len(current_ngrams) > 1:
        logger.debug(f"current_ngrams: {current_ngrams}")
        return

    if len(current_ngrams) == 0:
        return

    # Convert to the appropriate quantities for scoring
    gain_unit = gain_ngrams.pop()

    # Needed to handle Adobe's poor conversion of unicode mu
    current_unit = current_ngrams.pop().replace("\uf06d", "μ")

    # Allow the double of a +/- value to be valid also.
    try:
        if current.startswith("±"):
            result = (
                doc,
                Quantity(f"{gain} {gain_unit}"),
                Quantity(f"{str(2 * float(current[1:]))} {current_unit}"),
            )
            yield result

            result = (
                doc,
                Quantity(f"{gain} {gain_unit}"),
                Quantity(f"{current[1:]} {current_unit}"),
            )
            yield result
        else:
            result = (
                doc,
                Quantity(f"{gain} {gain_unit}"),
                Quantity(f"{current} {current_unit}"),
            )
            yield result
    except Exception:
        logger.debug(f"{gain} {gain_unit} or {current} {current_unit} is not valid.")
        return


def entity_level_scores(candidates, corpus=None):
    """Checks entity-level recall of candidates compared to gold."""
    docs = [(doc.name).upper() for doc in corpus] if corpus else None
    gold_set = get_gold_set(docs=docs)
    if len(gold_set) == 0:
        logger.error("Gold set is empty.")
        return

    # Turn CandidateSet into set of tuples
    entities = set()
    for c in tqdm(candidates):
        for entity in cand_to_entity(c):
            entities.add(entity)

    (TP_set, FP_set, FN_set) = entity_confusion_matrix(entities, gold_set)
    TP = len(TP_set)
    FP = len(FP_set)
    FN = len(FN_set)

    prec = TP / (TP + FP) if TP + FP > 0 else float("nan")
    rec = TP / (TP + FN) if TP + FN > 0 else float("nan")
    f1 = 2 * (prec * rec) / (prec + rec) if prec + rec > 0 else float("nan")
    return Score(
        f1, prec, rec, sorted(list(TP_set)), sorted(list(FP_set)), sorted(list(FN_set))
    )


def entity_to_candidates(entity, candidate_subset):
    matches = []
    for c in candidate_subset:
        for c_entity in cand_to_entity(c):
            if c_entity == entity:
                matches.append(c)
    return matches
