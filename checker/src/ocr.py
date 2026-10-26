import io
import time
from functools import lru_cache
from pathlib import Path

import numpy
from PIL import Image

from flag_image_generator import rnd_flag, gen_string_image, image_to_bitmap


class OcrEngine:
    def __init__(self) -> None:
        basepath = Path(__file__).parent.parent / "res" / "font-bitmaps"
        self._bitmaps = self._load_bitmaps(basepath)

    @classmethod
    @lru_cache(5)
    def _load_bitmaps(cls, p: Path) -> list[tuple[str, numpy.ndarray]]:
        chars = []
        for f in p.glob("char_*.bmp"):
            matrix = numpy.array(Image.open(f), dtype=numpy.int64)[:, :, 0]
            chars.append((f.stem[5:], matrix))
        chars.sort(key=lambda x: x[0])
        return chars

    def cut_chars(self, data: numpy.ndarray) -> list[numpy.ndarray]:
        return [data[:50, i:i + 25, :] for i in range(0, data.shape[1], 25)]

    def filter_char(self, data: numpy.ndarray) -> numpy.ndarray:
        background_color = data[0, 0, :]
        diff = numpy.abs(data.astype(numpy.int16) - background_color.astype(numpy.int16))
        mask = diff.sum(axis=2) > 6
        return mask * 255  # type: ignore

    def match_char(self, data: numpy.ndarray) -> str | None:
        best_value = 50000
        result = None
        for char, bitmap in self._bitmaps:
            diff = numpy.abs(data - bitmap).sum()
            if diff < best_value:
                best_value = diff
                result = char
        return result

    def match_all(self, data: numpy.ndarray) -> str:
        result = ""
        for c in self.cut_chars(data):
            m = self.match_char(self.filter_char(c))
            result += m if m is not None else "?"
        return result


class SpatialOcrEngine(OcrEngine):
    """
    OCR on a partial image (with every N-th row available).
    N = sampling. N = 1 is full OCR.
    """

    _sampled: dict[int, list[tuple[str, numpy.ndarray]]] = {}

    def __init__(self, sampling: int) -> None:
        super().__init__()
        self._sampling = sampling
        self._bitmaps = self._sample(self._bitmaps, sampling)

    @classmethod
    def _sample(cls, bitmaps: list[tuple[str, numpy.ndarray]], sampling: int) -> list[tuple[str, numpy.ndarray]]:
        if sampling not in cls._sampled:
            cls._sampled[sampling] = [(char, bitmap[::sampling, :]) for char, bitmap in bitmaps]
        return cls._sampled[sampling]


def eval_sampling() -> None:
    """
    sampling =  2 | Errors: 0 / 100 (0.000% error rate)
    sampling =  3 | Errors: 0 / 100 (0.000% error rate)
    sampling =  4 | Errors: 34 / 100 (34.000% error rate)
    sampling =  5 | Errors: 0 / 100 (0.000% error rate)
    sampling =  6 | Errors: 100 / 100 (100.000% error rate)
    sampling =  7 | Errors: 32 / 100 (32.000% error rate)
    sampling =  8 | Errors: 60 / 100 (60.000% error rate)
    sampling =  9 | Errors: 100 / 100 (100.000% error rate)
    sampling = 10 | Errors: 100 / 100 (100.000% error rate)
    :return:
    """

    for sampling in range(2, 11):
        ocr = SpatialOcrEngine(sampling) if sampling > 1 else OcrEngine()
        count = 100
        errors = 0
        for _ in range(count):
            flag = rnd_flag()
            img, dim = gen_string_image(flag)
            bmp = image_to_bitmap(img)
            matrix = numpy.array(Image.open(io.BytesIO(bmp)))
            if sampling > 1:
                matrix = matrix[::sampling, :]
            flag2 = ocr.match_all(matrix)
            if flag != flag2:
                errors += 1
        print(f"sampling = {sampling:2d} | Errors: {errors} / {count} ({errors / count * 100:.3f}% error rate)")


def main():
    sampling = 5

    # ocr = OcrEngine()
    ocr = SpatialOcrEngine(sampling) if sampling > 1 else OcrEngine()

    count = 1000
    errors = 0
    t = time.monotonic()
    for _ in range(count):
        flag = rnd_flag()
        img, dim = gen_string_image(flag)
        bmp = image_to_bitmap(img)
        matrix = numpy.array(Image.open(io.BytesIO(bmp)))
        if sampling > 1:
            matrix = matrix[::sampling, :]
        flag2 = ocr.match_all(matrix)
        if flag != flag2:
            errors += 1
    t = time.monotonic() - t
    print(f"Errors: {errors} / {count} ({errors / count * 100:.3f}% error rate)")
    print(f"OCR time: {t / count * 1000.0:.2f}ms per entry (generation + en/decoding + OCR)")


if __name__ == '__main__':
    # eval_sampling()
    main()
