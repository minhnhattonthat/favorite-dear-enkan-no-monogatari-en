"""wrap.py: event-script English, from translator paragraphs to the printer markup the `en` column holds.

Translators never see the JP line breaks. `simplify(jp)` drops every *soft* {n} (one between two pieces of text, a
{name} counting as text), so each box line group reads as one paragraph; every other {n} (after {spk}, before {wait},
around other codes) is *hard* and stays. The translator writes English in that simplified form, keeping every code
in order. `wrap(en)` then breaks each hard line into lines of at most 20 cells (two letters per cell, docs/re/text.md
§English; a run of k letters before a code takes ceil(k/2) cells; {name:0080} = the angel, 10 letters, other names
12) and a page of more than 3 text lines into continuation pages: `{n}{wait}{clear}` + the page's `{spk:X}{n}`.

    python -X utf8 tools/wrap.py "{spk:0001}{n}English text...{n}{wait}{clear}{end}"   prints the wrapped markup
"""
import re
import sys

CODE = re.compile(r"(\{[^}]*\})")
CELLS = 20
LINES = 3
NAME_CELLS = {"0080": 5}  # the angel's name is capped at 10 letters (docs/windows.tsv angel_name)
NAME_DEFAULT = 6
INLINE = ("name", "ins")  # codes that print text


def tokens(s):
    return [t for t in CODE.split(s) if t]


def is_code(t):
    return t.startswith("{") and t.endswith("}")


def kind(t):
    return t[1:-1].split(":")[0] if is_code(t) else None


def texty(t):
    return t is not None and (not is_code(t) or kind(t) in INLINE)


def simplify(jp):
    """JP markup without the soft line breaks (the translator's view)"""
    ts = tokens(jp)
    out = []
    for i, t in enumerate(ts):
        if t == "{n}" and i and i + 1 < len(ts) and texty(ts[i - 1]) and texty(ts[i + 1]):
            continue
        out.append(t)
    return "".join(out)


def codes(s):
    """the control codes of `s` other than {n}, in order (must match between JP and EN)"""
    return [t for t in tokens(s) if is_code(t) and t != "{n}"]


def cells(pieces):
    """cells taken by a line given as tokens"""
    n, run = 0, 0
    for t in pieces:
        if is_code(t):
            n += (run + 1) // 2
            run = 0
            if kind(t) == "name":
                n += NAME_CELLS.get(t[6:-1], NAME_DEFAULT)
            elif kind(t) == "ins":
                n += NAME_DEFAULT
        else:
            run += sum(2 if ord(c) >= 0x3000 else 1 for c in t)  # full-width glyphs (choice braces) take a cell
    return n + (run + 1) // 2


def _fix_odd(pieces):
    """a text run of odd length before a code gets a space partner from the encoder; if it already ends in a
    space, drop that space so the padding stands in for it (no half-cell double gap). Not before a code that prints
    text ({name}, {ins}): the name starts on the next cell, so the dropped space would leave none at all
    ("My name isRaviel"); there the space stays and the gap is one cell."""
    out = list(pieces)
    for i in range(len(out) - 1):
        if (not is_code(out[i]) and is_code(out[i + 1]) and kind(out[i + 1]) not in INLINE
                and len(out[i]) % 2 and out[i].endswith(" ")):
            out[i] = out[i][:-1]
    return out


def wrap_line(line):
    """one hard line (tokens) -> list of lines (token lists) of at most CELLS cells, broken at spaces"""
    words = []  # each word: list of tokens, ending at a space boundary
    cur = []
    for t in line:
        if is_code(t):
            cur.append(t)
            continue
        parts = re.split(r"( )", t)
        for p in parts:
            if p == " ":
                cur.append(" ")
                words.append(cur)
                cur = []
            elif p:
                cur.append(p)
    if cur:
        words.append(cur)
    groups, cur = [], []  # lines as lists of words
    for w in words:
        if cur and cells(_strip(_merge([t for x in cur + [w] for t in x]))) > CELLS:
            groups.append(cur)
            cur = [w]
        else:
            cur = cur + [w]
    if cur or not groups:
        groups.append(cur)
    _balance(groups)
    return [_strip(_merge([t for x in g for t in x])) for g in groups]


def _balance(groups):
    """no one-word last line: pull the previous line's last word down while it fits and leaves that line 2+ words
    (same line count, so pages don't change)"""
    if len(groups) < 2:
        return
    prev, last = groups[-2], groups[-1]
    texty_words = lambda g: sum(1 for w in g if has_text(w))  # noqa: E731
    while texty_words(last) < 2 and texty_words(prev) > 2:
        trial = [prev[-1]] + last
        if cells(_strip(_merge([t for x in trial for t in x]))) > CELLS:
            break
        last.insert(0, prev.pop())  # a code-only word moved: the loop pulls the next one too


def _merge(ts):
    out = []
    for t in ts:
        if out and not is_code(t) and not is_code(out[-1]):
            out[-1] += t
        else:
            out.append(t)
    return out


def _strip(ts):
    """drop trailing spaces of the line (they never print)"""
    ts = list(ts)
    while ts and not is_code(ts[-1]) and ts[-1].endswith(" "):
        ts[-1] = ts[-1].rstrip(" ")
        if not ts[-1]:
            ts.pop()
    return ts


def has_text(ts):
    return any(texty(t) for t in ts)


def wrap(en, max_lines=LINES):
    """simplified English markup -> printer markup. max_lines: lines a page may hold before it continues on a new
    page (pages the JP already scrolls past 3 lines pass a larger value)."""
    pages = re.split(r"(\{clear\})", en)
    out = []
    for page in pages:
        if page == "{clear}":
            out.append(page)
            continue
        out.append(_wrap_page(page, max_lines))
    return "".join(out)


def _wrap_page(page, max_lines):
    ts = tokens(page)
    spk = next((t for t in ts if kind(t) == "spk"), None)
    # hard lines: split at {n}; keep code-only lines as they are
    hard, cur = [], []
    for t in ts:
        if t == "{n}":
            hard.append(cur)
            cur = []
        else:
            cur.append(t)
    hard.append(cur)
    lines, breaks = [], set()  # breaks: indexes of lines that must start a continuation page
    count = 0
    for h in hard:
        if has_text(h):
            # leading/trailing codes stay attached to the first/last wrapped line
            ws = wrap_line(h)
            room = max_lines - count
            if 0 < room < len(ws):
                cut = _page_cut(h, room, len(ws) - room, max_lines)
                if cut:
                    first, rest = cut
                    for w in (wrap_line(first) if first else []):
                        lines.append(_fix_odd(w))
                    breaks.add(len(lines))
                    count = max_lines
                    ws = wrap_line(rest)
            for w in ws:
                if count == max_lines:
                    count = 0
                count += 1
                lines.append(_fix_odd(w))
        else:
            lines.append(h)
    # continuation pages
    # lines are joined by {n}, so a continuation reads 'prev{n}{wait}{clear}{spk:X}{n}next' as the JP pages do
    res, count = [], 0
    for i, ln in enumerate(lines):
        s = "".join(ln)
        if has_text(ln):
            if count == max_lines or i in breaks:
                s = "{wait}{clear}" + (spk + "{n}" if spk else "") + s
                count = 0
            count += 1
        res.append(s)
    return "{n}".join(res)


CLAUSE_END = re.compile(r"[.!?,;:][\"')]?(?= )")


def _page_cut(h, room, overflow, max_lines):
    """a hard line too long for the `room` lines left on its page: split it at the last sentence/clause end whose
    first part fits that room, so the continuation page starts a clause instead of a stray 'shows up.' (phase 8).
    None when no end fits or the split would need more continuation pages than the greedy break."""
    pages = lambda n: -(-n // max_lines)  # noqa: E731
    words = lambda ts: len("".join(t for t in ts if not is_code(t)).split())  # noqa: E731
    # in order of preference: a sentence end ('.!?') whose first part fills the room ("eventually. / Everything,
    # just like before." beats "Everything, / just like before."), then the latest end; both leaving the next page
    # 4+ words ("..., / wasn't he?", "chaos, / destruction and death..." are no better than the greedy break)
    full = late = short = None
    for i, t in enumerate(h):
        if is_code(t):
            continue
        for m in CLAUSE_END.finditer(t):
            first = h[:i] + [t[:m.end()]]
            rest = [x for x in [t[m.end() + 1:]] + h[i + 1:] if x]
            if not has_text(first) or not has_text(rest):
                continue
            n = len(wrap_line(first))
            if n <= room and pages(len(wrap_line(rest))) <= pages(overflow):
                if words(rest) < 4:
                    short = (first, rest)
                    continue
                late = (first, rest)
                if n == room and m.group(0)[0] in ".!?":
                    full = late
    if full or late:
        return full or late
    if pages(len(wrap_line(h))) <= pages(overflow):
        return [], h  # no clause end fits: the whole line opens the next page ("...like to / hear today?")
    ws = wrap_line(h)
    if room >= 2 and words(ws[room]) <= 3 and len(ws) == room + 1:
        # one sentence over a page plus a stray line: give the next page two lines ("...held down / inside her.")
        join = lambda ls: [t for ln in ls for t in ln + [" "]][:-1]  # noqa: E731
        return join(ws[:room - 1]), join(ws[room - 1:])
    return short


def page_lines(jp):
    """max text lines of any page of the JP (pages past 3 lines scroll in the original)"""
    best = 0
    for page in jp.split("{clear}"):
        best = max(best, sum(1 for ln in page.split("{n}") if has_text(tokens(ln))))
    return best


def wrap_for(jp, en):
    return wrap(en, max(LINES, page_lines(jp)))


def lines_report(markup):
    """[(cells, text)] per line, for checks"""
    out = []
    for page in markup.split("{clear}"):
        for ln in page.split("{n}"):
            ts = tokens(ln)
            if has_text(ts):
                out.append((cells(ts), ln))
    return out


if __name__ == "__main__":
    print(wrap(sys.argv[1]))
