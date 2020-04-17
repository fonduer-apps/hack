from PIL import Image

from hack.circular_connectors.transforms.transform import DauphinTransform


class VerticalFlip(DauphinTransform):
    def __init__(self, name=None, prob=1.0, level=0):
        super().__init__(name, prob, level)

    def transform(self, pil_img, label, **kwargs):
        return pil_img.transpose(Image.FLIP_TOP_BOTTOM), label
