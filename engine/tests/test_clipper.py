import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("clipper", Path(__file__).resolve().parents[1] / "clipper.py")
clipper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clipper)

class FakeWord:
    def __init__(self, start, end, word):
        self.start, self.end, self.word = start, end, word

class FakeSegment:
    def __init__(self, words):
        self.words = words

class EngineTests(unittest.TestCase):
    def test_candidate_boundaries(self):
        segments = [FakeSegment([
            FakeWord(0, 1, "Why"), FakeWord(1, 3, "is"), FakeWord(3, 7, "this?"),
            FakeWord(7, 10, "Because"), FakeWord(10, 14, "it"), FakeWord(14, 18, "matters.")
        ])]
        found = clipper.candidates(segments, min_sec=5, max_sec=20)
        self.assertTrue(found)
        self.assertTrue(any(c["start"] == 0 and c["end"] == 18 for c in found))

    def test_no_punctuation_transcript(self):
        words = [FakeWord(i, i + 1, "word") for i in range(70)]
        found = clipper.candidates([FakeSegment(words)], min_sec=15, max_sec=30)
        self.assertTrue(found, "Speech without punctuation should still yield clips")
        self.assertTrue(all(15 <= c["end"] - c["start"] <= 30 for c in found))

    def test_nonoverlap(self):
        items = [{"start":0,"end":20,"score":5}, {"start":10,"end":30,"score":4}, {"start":30,"end":50,"score":3}]
        result = clipper.choose(items, 3)
        self.assertEqual(len(result), 2)

    def test_srt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.srt"
            clipper.write_srt([{"start":10,"end":11,"word":"أهلاً"}, {"start":11,"end":12,"word":"بكم."}],10,path)
            contents = path.read_text(encoding="utf-8")
            self.assertIn("أهلاً بكم.", contents)
            self.assertIn("00:00:00,000 --> 00:00:02,000", contents)

if __name__ == "__main__":
    unittest.main()
