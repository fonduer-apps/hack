import random

from hack.circular_connectors.transforms.transform import DauphinTransform
from hack.circular_connectors.transforms.utils import categorize_value


class Rotate(DauphinTransform):

    value_range = (0, 30)

    def __init__(self, name=None, prob=1.0, level=0):
        super().__init__(name, prob, level)

    def transform(self, pil_img, label, **kwargs):
        degree = categorize_value(self.level, self.value_range, "float")
        if random.random() > 0.5:
            degree = -degree
        return pil_img.rotate(degree), label
