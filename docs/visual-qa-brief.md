# Visual-QA reviewer brief - Favorite Dear: Enkan no Monogatari (PS1)

(Game 1's brief, `../favorite-dear-en/docs/visual-qa-brief.md`, adapted. The original disc's sheets here are the
phase-2 warp shots: `work/qa/warp/<scene>/sheet.png` and its frames.)

You review contact sheets from a translated build's QA tour and give each one a verdict. Read-only on everything
except your one verdict file: no edits to the repo, no git, no subagents.

## Inputs (in your dispatch)
- A chunk file: one `id<TAB>path` line per sheet. Read every sheet in it; none may be skipped.
- Your verdict file: `work/qa/verdicts/<chunk>.tsv`.
- The original disc's sheets (`work/qa/warp/<scene>/sheet.png`, same scene names) and `glossary.md` (read it in
  parts with offset/limit: whole-file reads of big files come back as a stub).

## How to look
- Each sheet is up to 16 frames of one warp scene (`tools/debug/scenes.tsv`), from 300 frames before arrival on.
  The single frames sit next to it (`fNNNNNN.png`, `arrived.png`, `post.png`).
- Read each sheet whole first. Where text is small, zoom into a single frame with
  `python -X utf8 $SKILL/scripts/sheet.py FRAME.png --crop x,y,w,h --zoom 3 --out <scratch>.png` and read that.
- When something looks wrong, open the same scene from `work/qa/warp/` (`sheet.py EN.png --compare JP.png`). If the
  original shows the same thing, it is the game's own behaviour: `ok`, with a note.
- Zoom into every Yes/No prompt, selection box, menu row and speech bubble. To measure one:
  `python -X utf8 $SKILL/scripts/inkbox.py SHOT.png x,y,w,h`.

## Judge
An `issue` is any of:
- Japanese still visible (except the standing non-bugs below);
- text overflowing a box, clipped by a frame, or running off screen;
- text off-centre where the original centres it: an option in its selection box or cursor brackets, a label, a bubble;
- garbage tiles, wrong or missing glyphs, a strike or stray pixels across letters;
- broken line breaks: a word split mid-line, a page ending mid-sentence, a one-word last line;
- an empty box where text belongs;
- a name that differs from `glossary.md`.

Standing non-bugs, `ok`:
- text still typing out, a box mid-fade or mid-scroll, a cursor caught mid-blink;
- a map or scene still loading after a warp; black frames before arrival;
- anything identical in the original's sheet;
- the logo: FAVORITE DEAR with the kanji subtitle 円環の物語, and the kana フェイバリット・ディア under it (D5);
- the name-entry grids and the 8 memory-card titles (`docs/jp_kept.tsv`, D11), until a Latin grid is ported;
- Japanese voice-over has no subtitles: the opening/ending movies (OP.STR, FD_MOV) are video, not text;
- honorifics like "-sama", "-san", "-dono" (D12) and "Jr." ranks (12-letter rank box);
- battle name plates are UPPER CASE by design (8x8 plate font);
- the angel's default name is "Raviel"; warps that skip name entry may show it.
- in the `epilog_*` ending warps the angel's name may be blank (a lone ":" speaker line, "Hey, ."): the warp sets
  no name; check the Japanese warp's frames before calling it.
- a hub or save screen showing ラビエル: that is the name stored in the JP-written card `work/saves/week2.mcd`.
- the bright-green key colour or a CG cut off in event scenes, when the Japanese warp shows the same, is warp state.
- <add more as reviewers confirm them>

## Verdicts
Write your verdict file once you have read every sheet, one line per id in the chunk:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which tile, which text, what is wrong).
Then return a short summary: counts, and the issues one per line.
