import torchvision.transforms as transforms

from hack.circular_connectors.transforms.transform import DauphinTransform


class Normalize(DauphinTransform):
    def __init__(self, mean, std, name=None, prob=1.0, level=0):
        self.mean = mean
        self.std = std
        self.transform_func = transforms.Normalize(mean, std)

        super().__init__(name, prob, level)

    def transform(self, pil_img, label, **kwargs):
        return self.transform_func(pil_img), label
