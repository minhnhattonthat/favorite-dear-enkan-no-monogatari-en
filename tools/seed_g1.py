"""seed_g1.py: carry game 1's English over to event rows whose JP is game 1's with different control codes.

    python -X utf8 tools/seed_g1.py [--dry]     fill `en` of untranslated rows, print counts

Phase 4 seeded rows whose JP is byte-identical to a game-1 row (`g1:<id>` notes). This tool takes the next two
steps, both from game 1's translator output (`../favorite-dear-en/trans/en/bNNN.tsv`, simplified form, verified to
rewrap to game 1's `en` exactly):
  1. family: the JP equals a game-1 batch row once code arguments are blanked (tools/batches.family_key): game 1's
     English with this row's code arguments (batches.with_args). Note `g1~:<id> (code args differ)`.
  2. segments: the JP's text segments (text between control codes other than {n} and inline {name}/{ins}) are the
     same list, in the same order, as a game-1 row's: each segment takes the English of the game-1 segment at the
     same position, inside this row's own codes. Note `g1~:<id> (codes differ, text same)`.
Every result must pass batches.check_row (codes, font, glossary, honorifics, wrap) or it is left for translators.
Glyph-soup rows (notes say so) are never touched.
"""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import batches as B  # noqa: E402
import wrap  # noqa: E402

G1 = B.ROOT.parent / "favorite-dear-en"
csv.field_size_limit(10 ** 8)


def g1_reps():
    """{family_key: (g1 id, simplified jp, simplified en)} from game 1's batches and translator output"""
    out = {}
    for p in sorted((G1 / "trans" / "en").glob("b*.tsv")):
        jp = {r["id"]: r["jp"] for r in B.read_tsv(G1 / "trans" / "batches" / p.name)}
        for r in B.read_tsv(p):
            if r["en"] and r["en"] != B.SKIP and r["id"] in jp:
                out.setdefault(B.family_key(jp[r["id"]]), (r["id"], jp[r["id"]], r["en"]))
    return out


def is_seg_code(t):
    return wrap.is_code(t) and t != "{n}" and wrap.kind(t) not in wrap.INLINE


def segments(s):
    """split simplified markup at structural codes: [(codes_before, segment_tokens)] + trailing codes"""
    segs, cur = [], []
    for t in wrap.tokens(s):
        if is_seg_code(t):
            segs.append(cur)
            segs.append(t)
            cur = []
        else:
            cur.append(t)
    segs.append(cur)
    return segs  # alternating: [seg, code, seg, code, ..., seg]


def seg_text(seg):
    return "".join(t for t in seg if t != "{n}")


def core(seg):
    """(leading {n}s, middle tokens, trailing {n}s)"""
    a, b = 0, len(seg)
    while a < b and seg[a] == "{n}":
        a += 1
    while b > a and seg[b - 1] == "{n}":
        b -= 1
    return seg[:a], seg[a:b], seg[b:]


def text_key(s):
    return tuple(x for x in (seg_text(g) for g in segments(s)[::2]) if x)


def transplant(jp, g1_jp, g1_en):
    """this row's codes with game 1's English per text segment, or None"""
    sa, sb, se = segments(jp), segments(g1_jp), segments(g1_en)
    if len(sb) != len(se):
        return None
    tb = [i for i in range(0, len(sb), 2) if seg_text(sb[i])]
    ta = [i for i in range(0, len(sa), 2) if seg_text(sa[i])]
    if [seg_text(sa[i]) for i in ta] != [seg_text(sb[i]) for i in tb]:
        return None
    # English of game-1 segments that had no JP text (translator moved text there) would be lost
    if any(seg_text(se[i]) for i in range(0, len(sb), 2) if i not in tb):
        return None
    out = list(sa)
    for ia, ib in zip(ta, tb):
        lead, _, trail = core(sa[ia])
        _, mid, _ = core(se[ib])
        out[ia] = lead + mid + trail
    return "".join(t if isinstance(t, str) else "".join(t) for t in out)


def main(argv):
    dry = "--dry" in argv
    reps = g1_reps()
    by_text = {}
    for k, (gid, gjp, gen) in reps.items():
        by_text.setdefault(text_key(gjp), (gid, gjp, gen))
    terms = B.glossary()
    n_fam = n_seg = n_fail = 0
    for p in B.event_files():
        rows = B.read_tsv(p)
        cols = list(rows[0].keys())
        dirty = False
        for r in rows:
            if r["en"] or "soup" in r["notes"] or not B.glyphs(r["jp"]):
                continue
            sj = wrap.simplify(r["jp"])
            en = note = None
            k = B.family_key(r["jp"])
            if k in reps:
                gid, gjp, gen = reps[k]
                en, note = B.with_args(gen, gjp, r["jp"]), f"g1~:{gid} (code args differ)"
            else:
                hit = by_text.get(text_key(sj))
                if hit:
                    en = transplant(sj, hit[1], hit[2])
                    note = f"g1~:{hit[0]} (codes differ, text same)"
            if en is None:
                continue
            errs = B.check_row(r["id"], sj, en, terms)
            if errs:
                n_fail += 1
                if n_fail <= 5:
                    print("\n".join(errs[:2]))
                continue
            if note.endswith("args differ)"):
                n_fam += 1
            else:
                n_seg += 1
            r["en"] = B.to_printer(wrap.wrap_for(r["jp"], en))
            r["notes"] = "; ".join(x for x in (r["notes"], note) if x)
            dirty = True
        if dirty and not dry:
            B.write_tsv(p, rows, cols)
    print(f"seeded: {n_fam} by family, {n_seg} by segments; {n_fail} candidates failed the row check")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
