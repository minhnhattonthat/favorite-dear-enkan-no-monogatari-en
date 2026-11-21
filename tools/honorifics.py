"""honorifics.py: apply ruling D1/D12 (personal name + honorific -> "Name-san") to trans/en, reviewed row by row.

    python -X utf8 tools/honorifics.py propose OUT.tsv   rows whose EN lacks a ruled honorific: proposed EN + context
    python -X utf8 tools/honorifics.py apply OUT.tsv     write the `new` column of reviewed rows into trans/en/bNNN.tsv

`propose` only writes a proposal file. Rows it can't place (the name is missing from the English, or the same name
appears both with and without an honorific in the JP) get `new` = `?` and are fixed by hand. Every proposed row is
read before `apply`; delete or hand-edit lines in the proposal file as needed (columns: batch, id, how, old, new).
The same rule is linted by `batches.check_row` (`missing()` below).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import batches as B  # noqa: E402

HON = {"さん": "san", "くん": "kun", "君": "kun", "ちゃん": "chan", "様": "sama", "さま": "sama", "殿": "dono",
       "どの": "dono"}
# English titles that stood in for the honorific before D12; dropped in front of the name
TITLES = r"(?:(?:Lord|Lady|Sir|Master|Mister|Mr\.|Mrs\.|Miss|Ms\.|Dame|Madam|Mistress|Boss|Dr\.)\s+)"
_PAT = None


def names():
    """{jp katakana name: en} from the glossary's katakana rows (nicknames such as ナーサ have their own rows)"""
    out = {}
    for jp, en, _ in B.glossary():
        if re.fullmatch(f"[{B.KATA}]+", jp):
            out[jp] = en.split(" (")[0]
    return out


def pairs(jp, nm):
    """[(jp name or code, en name or code, en suffix)] for each name+honorific in the JP text"""
    text = re.sub(r"\{(?!name:)[^}]*\}", "", jp)
    hon = "|".join(sorted(HON, key=len, reverse=True))
    out = []
    for m in re.finditer(rf"(\{{name:\w+\}}|[{B.KATA}]+)({hon})", text):
        who, h = m.groups()
        if who.startswith("{"):
            out.append((who, who, HON[h]))
        elif who in nm:
            out.append((who, nm[who], HON[h]))
    return out


def missing(jp, en, nm):
    """lint: ruled `Name-suffix` forms absent from the English (one message per pair)"""
    errs = []
    for who, e, suf in dict.fromkeys(pairs(jp, nm)):
        if f"{e}-{suf}" not in en:
            errs.append(f"honorific {who} -> {e}-{suf} missing (D12)")
    return errs


def propose_row(jp, en, nm):
    """(how, new) for one row"""
    new, how = en, "auto"
    for who, e, suf in dict.fromkeys(pairs(jp, nm)):
        if f"{e}-{suf}" in new:
            continue
        text = re.sub(r"\{[^}]*\}", "", jp) if not who.startswith("{") else jp
        bare = len(re.findall(re.escape(who), text)) - len(re.findall(re.escape(who) + "(?:" + "|".join(HON) + ")", text))
        if bare > 0:
            # the JP also uses the bare name: convert only the English forms that carry a title ("Lord Sievas",
            # "Sir Reiv Vincelras"), where the translator rendered the honorific
            rx = re.compile(TITLES + re.escape(e) + r"((?: [A-Z][a-z]+)?)(?![\w-])")
            if not rx.search(new):
                return "mixed", "?"
            new = rx.sub(lambda m: f"{e}{m.group(1)}-{suf}", new)
            how = "titled"
            continue
        rx = re.compile(TITLES + "?" + re.escape(e) + r"(?![\w-])")
        if not rx.search(new):
            return "absent", "?"
        new = rx.sub(lambda m: f"{e}-{suf}", new)
    return how, new


def propose(outp):
    nm = names()
    lines = ["batch\tid\thow\told\tnew"]
    for p in sorted(B.BATCHES.glob("b*.tsv")):
        ep = B.OUT / p.name
        en = {r["id"]: r["en"] for r in B.read_tsv(ep)}
        for r in B.read_tsv(p):
            e = en.get(r["id"], "")
            if e == B.SKIP or not missing(r["jp"], e, nm):
                continue
            how, new = propose_row(r["jp"], e, nm)
            lines.append("\t".join([p.stem, r["id"], how, e, new]))
    Path(outp).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(lines) - 1} rows -> {outp}")


def apply(inp):
    rows = B.read_tsv(Path(inp))
    by = {}
    for r in rows:
        if r["new"] in ("?", ""):
            sys.exit(f"{r['id']}: unresolved `?` row; fix or delete it first")
        by.setdefault(r["batch"], {})[r["id"]] = r
    for b, fix in by.items():
        p = B.OUT / f"{b}.tsv"
        out = B.read_tsv(p)
        for r in out:
            f = fix.get(r["id"])
            if f:
                if r["en"] != f["old"]:
                    sys.exit(f"{b} {r['id']}: trans/en changed since propose")
                r["en"] = f["new"]
        B.write_tsv(p, out, ["id", "en"])
    print(f"applied {len(rows)} rows in {len(by)} batches")


def main(argv):
    if len(argv) != 2 or argv[0] not in ("propose", "apply"):
        print(__doc__)
        return 2
    (propose if argv[0] == "propose" else apply)(argv[1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
