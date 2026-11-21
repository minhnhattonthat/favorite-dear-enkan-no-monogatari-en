# Translator brief (event scripts)

Read in parts (offset/limit): context-mode trims whole-file Reads above ~4 KB.

1. Read `glossary.md` (rulings, style rules, name tables; game 1's, imported whole, plus "(FD:EnM)" names new here)
   and `docs/style-reference.md` (voices, stock lines), and `docs/synopsis.md` (who is who, the reveals, this
   game's additions: Juliana's arc). Game 1's English is the house style: a returning player reads both games.
2. Input `trans/batches/bNNN.tsv`: `id<TAB>jp<TAB>g1`. The JP has its soft line breaks removed: each `{n}` left is
   structural. Rows are in script-file order, so neighbours are context. `g1`, when set, is game 1's English for the
   game-1 row sharing most of this row's text (`tools/g1hint.py`): reuse its wording where the JP is the same and
   translate only what differs (this game re-uses game 1's scenes with additions).
   Rows whose JP already matched game 1 (verbatim, or with other code arguments/codes) are seeded and not batched
   (`tools/seed_g1.py`); glyph-soup rows are left out.
3. Output `trans/en/bNNN.tsv` (header `id<TAB>en`), one row per input id:
   - keep every control code (`{spk:..}`, `{e0:..}`, `{fb:..}`, `{n}`, `{wait}`, `{clear}`, `{end}`, `{name:..}`,
     `{f7:..}`...) in the same order; only the Japanese text between them changes. Do not add `{n}`:
     `tools/wrap.py` breaks lines at 40 letters and adds continuation pages itself.
   - plain ASCII plus … — ♥ ♪ é. No ASCII braces in text. Choices keep `　｛Option　｝` (see glossary).
   - `{name:0080}` is the angel (up to 10 letters), `{name:0180}`/`{name:0280}` heroes or items (runtime). No suffix
     glued to a name code except `'s`; never "a/an" right before one; keep them gender-neutral ("them").
   - `-` alone for a row that is data, not text (glyph soup, item-name lists run together, digit tables); add a
     line to glossary "Decisions from earlier batches" saying why.
4. Run `python -X utf8 tools/batches.py check bNNN` until it prints `bNNN: OK`, then
   `python -X utf8 tools/batches.py merge` (writes the wrapped `en` into `script/events/*.tsv`).
5. Quality bar (past mistakes in other projects): names exactly as in the glossary; jokes and character quirks kept
   (rough speech stays rough); no "1th"-style suffixes; no stock "GET!" phrasing; repeated variants of one message
   (rows that differ by one word) translated consistently.
6. Token saver: `python -X utf8 tools/compact.py show bNNN [--from N --to M]` prints the batch with the frequent
   code runs as one symbol each (¶ = `{n}{wait}{clear}{e0:E0FF}`, ¬ = `{n}{wait}{clear}`, § = `{e0:E0FF}`,
   Å = `{spk:E783}` (the angel), Ø = `{spk:0080}`, Ñ = `{name:0080}`) and the hint as a `#g1` line; write the
   English in the same form and `compact.py expand x.en bNNN` writes `trans/en/bNNN.tsv` exactly (lines starting
   `#` are ignored). Mind ¶ vs ¬ (the check catches a swap).
7. Report `NEW TERM: jp -> en`, `UNSURE: id - note`, `CUT: id - what was dropped`; terms go into glossary.md tables.
