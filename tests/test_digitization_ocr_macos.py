"""Tests for persistent macOS Vision OCR request reuse."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sys
import types

from digitization.ocr import OCRConfig
from digitization.ocr_macos import MacOSVisionOCR


class _Candidate:
    def __init__(self, text: str, confidence: float):
        self._text = text
        self._confidence = confidence

    def string(self):
        return self._text

    def confidence(self):
        return self._confidence


class _BBoxValue:
    def __init__(self, x=0.1, y=0.8, w=0.5, h=0.1):
        self.origin = types.SimpleNamespace(x=x, y=y)
        self.size = types.SimpleNamespace(width=w, height=h)


class _Observation:
    def __init__(self, text: str):
        self._candidate = _Candidate(text, 0.91)

    def topCandidates_(self, count):
        return [self._candidate]

    def boundingBox(self):
        return _BBoxValue()


def test_vision_request_is_initialized_once_and_reused(monkeypatch, tmp_path: Path):
    image_a = tmp_path / "a.png"
    image_b = tmp_path / "b.png"
    image_a.write_bytes(b"a")
    image_b.write_bytes(b"b")

    state = {"request_inits": 0, "perform_calls": 0}

    class FakeRequest:
        def __init__(self):
            self._results = []

        def setRecognitionLevel_(self, level):
            self.level = level

        def setRecognitionLanguages_(self, languages):
            self.languages = languages

        def results(self):
            return self._results

        @classmethod
        def alloc(cls):
            return cls()

        def init(self):
            state["request_inits"] += 1
            return self

    class FakeHandler:
        @classmethod
        def alloc(cls):
            return cls()

        def initWithData_options_(self, data, options):
            return self

        def performRequests_error_(self, requests, error):
            state["perform_calls"] += 1
            requests[0]._results = [_Observation(f"page-{state['perform_calls']}")]
            return True, None

    class FakeVision:
        VNRecognizeTextRequest = FakeRequest
        VNImageRequestHandler = FakeHandler

    class FakeNSData:
        @staticmethod
        def dataWithBytes_length_(data, length):
            return data

    @contextmanager
    def fake_pool():
        yield

    fake_objc = types.SimpleNamespace(autorelease_pool=fake_pool)
    fake_foundation = types.SimpleNamespace(NSData=FakeNSData)

    monkeypatch.setitem(sys.modules, "objc", fake_objc)
    monkeypatch.setitem(sys.modules, "Vision", FakeVision)
    monkeypatch.setitem(sys.modules, "Foundation", fake_foundation)

    ocr = MacOSVisionOCR(OCRConfig())

    assert ocr.ocr_image(image_a) == "page-1"
    assert ocr.ocr_image(image_b) == "page-2"
    assert state["request_inits"] == 1
    assert state["perform_calls"] == 2
    assert ocr._request is not None
