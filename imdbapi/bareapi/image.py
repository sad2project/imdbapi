from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple


def image_info_from_url(url: str):
    sz_start, sz_end = size_coordinates(url)
    size = ImageSize.from_url(url[sz_start: sz_end])
    id = url[sz_end + 1:]
    aspect_ratio = AspectRatio.from_url_or_id(url)
    return size, aspect_ratio, id


class ImageUrl:
    IMAGE_URL_FORMAT = 'https://imdb-api.com/Images/{size}/{id}'

    @staticmethod
    def _calc_fit_dimensions(original_ratio: 'AspectRatio', desired_w, desired_h) -> Tuple[int, int]:
        desired_ratio = desired_w / desired_h
        if original_ratio == desired_ratio:
            return desired_w, desired_h
        if desired_ratio > original_ratio:
            return desired_h * original_ratio, desired_h
        else:
            return desired_w, desired_w * (1 / original_ratio.as_float())

    @staticmethod
    def _calc_fill_dimensions(original_ratio: 'AspectRatio', desired_w, desired_h) -> Tuple[int, int]:
        desired_ratio = AspectRatio.from_dims(desired_w, desired_h)
        if original_ratio == desired_ratio:
            return desired_w, desired_h
        if desired_ratio > original_ratio:
            return desired_w, desired_w * (1 / original_ratio.as_float())
        else:
            return desired_h * original_ratio, desired_h

    @classmethod
    def to_fit(cls, id, width, height):
        realw, realh = cls._calc_fit_dimensions(AspectRatio.from_url_or_id(id), width, height)
        return cls.with_dims(id, realw, realh)

    @classmethod
    def to_fill(cls, id, width, height):
        realw, realh = cls._calc_fill_dimensions(AspectRatio.from_url_or_id(id), width, height)
        return cls.with_dims(id, realw, realh)

    @classmethod
    def with_dims(cls, id, width, height):
        return cls.with_size(id, ImageSize.with_dims(width, height))

    @classmethod
    def with_original_size(cls, id):
        return cls.with_size(id, ImageSize.original())

    @classmethod
    def with_size(cls, id, size: 'ImageSize'):
        return cls.IMAGE_URL_FORMAT.format(size=str(size), id=id)


class ImageSize(ABC):
    @staticmethod
    def from_url(url: str):
        start, end = size_coordinates(url)
        size = url[start:end]
        if size.lower() == 'original':
            return Original.value()
        else:
            return ImageSize.from_numXnum(size)

    @staticmethod
    def from_numXnum(desc: str):
        width, height = desc.lower().split('x')
        return Dimensions(width, height)

    @staticmethod
    def with_dims(width, height):
        return Dimensions(width, height)

    @staticmethod
    def original():
        return Original.value()

    @abstractmethod
    def aspect_ratio(self, original_a_r: 'AspectRatio'):
        ...


def size_coordinates(url: str) -> Tuple[int, int]:
    start = url.lower().find('images/') + 7
    return start, url.find('/', start)


@dataclass
class Dimensions(ImageSize):
    width: int
    height: int

    def aspect_ratio(self, original_a_r: 'AspectRatio'):
        return AspectRatio.from_dims(self.width, self.height)

    def __str__(self):
        return f'{self.width}x{self.height}'


class Original(ImageSize):
    __instance = None

    @classmethod
    def value(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def aspect_ratio(self, original_a_r: 'AspectRatio'):
        return original_a_r

    def __str__(self):
        return 'original'

    def __repr__(self):
        return 'Original.value()'

    def __eq__(self, other):
        return isinstance(other, Original)

    def __hash__(self):
        return 15


class AspectRatio:

    def __init__(self, large_version: int):
        if large_version <= 0 or large_version >= _conversion * 100:
            self._illegal_aspect_ratio(large_version / _conversion)
        self.ratio = large_version

    @classmethod
    def from_float(cls, float_version: float):
        return cls(int(float_version * _conversion))

    @classmethod
    def from_str(cls, str_version: str):
        if ':' in str_version:
            return cls._from_str_ratio(str_version)
        else:
            return cls._from_str_float(str_version)

    @classmethod
    def _from_str_float(cls, str_version: str):
        try:
            ratio = float(str_version)
        except ValueError:
            cls._illegal_aspect_ratio(str_version)
        else:
            return cls.from_float(ratio)

    @classmethod
    def _from_str_ratio(cls, str_version: str):
        try:
            width, height = str_version.split(':')
        except ValueError:
            cls._illegal_aspect_ratio(str_version)
        else:
            return cls.from_dims(width, height)

    @classmethod
    def from_dims(cls, width, height):
        return cls.from_float(width / height)

    @classmethod
    def from_url_or_id(cls, url: str):
        start = url.index('_Ratio') + 6
        return cls.from_str(url[start:-8])

    @classmethod
    def _illegal_aspect_ratio(cls, value):
        raise ValueError(f'{value} is an illegal aspect ratio')

    def as_float(self):
        return self.ratio / _conversion

    def __str__(self):
        return int_to_aspect_ratio(self.ratio)

    def __repr__(self):
        return f'AspectRatio({self.ratio})'

    def __eq__(self, other):
        return isinstance(other, AspectRatio) and self.ratio == other.ratio

    def __hash__(self):
        return hash(self.ratio)

    def __gt__(self, other: 'AspectRatio'):
        return self.ratio > other.ratio


_conversion = 10_000
def int_to_aspect_ratio(large_version: int) -> str:
    return f'{large_version // _conversion}.{large_version % _conversion}'
