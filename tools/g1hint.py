"""g1hint.py: game 1's English for the game-1 row that shares most of a JP row's text (a translator hint).

    python -X utf8 tools/g1hint.py "<simplified jp>"     print the hint

Text pieces between control codes (4+ glyphs) are looked up among game 1's translated batch rows
(`tools/seed_g1.g1_reps`); the game-1 row covering the most of this row's text wins if it covers at least
MIN_COVER of it. The hint is game 1's simplified English (codes kept), for the translator to reuse wording where
the JP is the same and translate only what differs.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import seed_g1  # noqa: E402

MIN_COVER = 0.5


def frags(jp):
    return {f for f in re.split(r"\{[^}]*\}", jp) if len(f) >= 4}


class Hints:
    def __init__(self):
        self.reps = list(seed_g1.g1_reps().values())
        self.index = {}
        for i, (_, jp, _) in enumerate(self.reps):
            for f in frags(jp):
                self.index.setdefault(f, []).append(i)

    def get(self, jp):
        fs = frags(jp)
        total = sum(len(f) for f in fs)
        if not total:
            return ""
        score = {}
        for f in fs:
            for i in self.index.get(f, ()):
                score[i] = score.get(i, 0) + len(f)
        if not score:
            return ""
        best = max(score, key=lambda i: (score[i], -i))
        return self.reps[best][2] if score[best] / total >= MIN_COVER else ""


if __name__ == "__main__":
    print(Hints().get(sys.argv[1]) or "(no hint)")
