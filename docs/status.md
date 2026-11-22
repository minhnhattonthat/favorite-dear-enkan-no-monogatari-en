# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **2026-11-23, v1.1 published (D13)** with the fixes below; tour gates waived for build fae395f2 (hotfix), README
  Thanks + README.txt Changes/Credits added.
- **2026-11-23, game 1's v1.1 player bugs checked here (released in v1.1; v1.0 has all three).** Same engine, so
  game 1's issues #1, #2, #4 were re-checked in game against the v1.0 image (`work/v10/v10.bin`, from the release
  xdelta, sha1 24d6d135) and fixed (D12; notes and repros in `docs/re/text.md` §Hero visit GIFT window, §Hero
  equipment, §Hero visit topic menu): (1) GIFT window header garbled, "Unus  le" / "Unusin use." -> `asm/gift.inc`
  + packed rows PSX.141F44/141F70; (2) hero status Equip box empty -> `asm/equip.inc` (caps4x7, `tests/test_equip.py`);
  (4) one visit-menu option 20 cells (e587.2918) -> fixed, `tools/menuopts.py` + test. Before/after:
  `work/qa/fix_g1/gift_old_vs_fix.png`, `equip_v10/` vs `equip/`. check ok (76 tests, lint 0), smoke ok, fitcheck ok on build
  fae395f2. New debug Lua: `tools/lua/scoutwin.lua`, `giveitems.lua`, `setequip.lua`. Next: player bug reports
  (`gh issue list --label bug`); a full re-tour before the next release (v1.1 waived it).

- **Phase:** 9. Release done 2026-11-22: all 8 story-pass chapters ok, `tools/release.py` exits 0 ->
  `release/Favorite_Dear_Enkan_no_Monogatari_EN_v1.0.zip` (xdelta + README.txt; patched disc sha1 24d6d135...,
  re-applied and verified; re-verified by worker 15: `release.py --force` exits 0, same image sha1 and
  byte-identical xdelta c90eecdc...). **Published 2026-11-22**: repo made public (description fixed to the game
  title), release v1.0 at https://github.com/minhnhattonthat/favorite-dear-enkan-no-monogatari-en/releases/tag/v1.0
  (tag on 60aa538; asset zip sha1 1c9dc050..., downloaded back and compared). Gotcha: `gh release create` right after
  `--visibility public` got a 404 on the asset upload and left a draft; `gh release upload` + `edit --draft=false` fixed it.
  Next: player bug reports (`gh issue list --label bug`).
  See "Phase 9" below. (Phase 8 done 2026-11-22: `textcover.py` exits 0, 11,256/11,424 shown, 168
  waived; see Next (2)). Phase 8 record: (phase 7 and its review fixes done 2026-11-22; phase 8: OMK
  repoint space verified by RAM dump, `docs/re/space.md`; graphics text ported; first tour + gate manifest; battle name plates English;
  hero skill names and name entry English; re-tour of the final code build; visual QA of all 293 sheets done:
  7 issues fixed; OMK Mini Event script translated and inserted, all 12 scenes read in game; tour3 on the final
  build; tour3 visual QA gate passes: 296/296 ok, 0 issues; inkbox, stress saves, rank width, e243 + tutorial
  Part 3 done; e203 unreached (likely unused); text coverage: textforce passes 1-8, 286 rows left, 270 of them
  choice menus; only textcover.py is left for phase 8).
- **Done:**
  - Step 0: template filled, `tools/skill.py`, PCSX-Redux in `tools/pcsx/` (fetch_emu), BIOS + mkpsxiso/armips/xdelta
    copied from game 1's repo, guard hook in `.claude/settings.json` (canary `sed -i` blocked), pre-commit hook
    (`core.hooksPath tools/hooks`, CHECK = `tools/check.py`; a failing test was rejected), `rom.sha1` +
    `tests/test_rom.py`, original disc smoke-boots to the title menu (`work/qa/smoke_orig`, scripted Start works).
    Not checked: keyboard input in the PCSX-Redux window (headless runs only).
  - Phase 1: **this game is an expanded re-release of game 1 (`../favorite-dear-en`)**. Same engine and layout,
    most data byte-identical, 56% of event characters are verbatim game-1 `jp` rows. Recorded in `docs/re/`:
    encoding (`tbl/jp.tbl`; font MSB-first at PSX.EXE 0xFA6C0; NCODES 0x6F0), GDATA/SDATA u16 directories, 568
    event scripts (game 1's grammar), EXE strings (952, also in OMK.EXE), credits in DATA/FIN.EXE, load buffer,
    graphics-text survey.
  - Phase 2: `tools/debug/` (warp.py/warp.lua/scenes.tsv, save.py, mcd.py, evnames.py), `docs/re/debug.md`,
    `tests/test_debug.py`, `tools/addrmap.py`. All 116 scenes reach their target from a cold boot on the original
    disc (`work/qa/warp/<scene>/arrived.png`, `results.tsv`): title/load/option menus, new game + name entry,
    week 1/2, world map, 30 game-1 events + 12 new ones (`--event eNNN`), hub + ability/map/system/save menus,
    7 battles + 12 T-battles, credits + full staff roll (FIN needs interpreter mode, automatic), epilog + endings
    1-26, ending movie, FD_BALL minigame, OMK Omake menu / Visual CG / Mini Event, edited save. Events are
    loaded by u16 name hash here (game 1: names); new events have no names, so GDATA entry eNNN is the handle.
    Game-written cards `work/saves/week1.mcd`, `week2.mcd` (gitignored; `save_write`/`save_write2` scenes
    regenerate them); save.py layout re-verified (second week copy at 0x2838), bad-sum save rejected.
  - Phase 3: `tools/build.py` (game 1's, adapted) -> `build/fd3_en_identity.bin/.cue` is byte-identical to the
    original (sha1 = `rom.sha1`, ~3 s, nothing to explain); `tests/test_build.py` (identity, one-byte edit changes
    one sector, unknown path refused; in the default check). The identity build smoke-boots
    (`work/qa/smoke_identity`) and `warp.py week1 --cue build/fd3_en_identity.cue --root work/qa/warp_identity`
    arrives (week-1 party screen). `build.py` without `--identity` exits until `tools/insert.py` exists (phase 7).
  - Phase 4: `tools/extract.py` (game 1's, adapted) -> `script/events/eNNN.tsv` (561 files, 12,617 rows, id
    `eNNN.<byte offset>`, NNN = GDATA entry; e902/e932 alias e520/e739), `script/exe.tsv` (885 rows: 2 regions,
    5 lui/addiu-addressed strings, 2 name-entry grids; OMK.EXE copies at fixed deltas, `extract.omk_delta`, same
    rows), `script/staff.tsv` (272 rows, FIN.EXE Shift-JIS lines), `script/sjis.tsv` (8 card titles).
    `tests/test_extract.py` (9 tests, in check): every row re-encodes to the original bytes (PSX and OMK), scripts
    tile end to end, EXE regions hold only rows/codes-only strings/3 pointer tables, staff roll rebuilds. Seeded
    from game 1's identical `jp` rows: 6,678 event + 852 EXE + 175 staff rows have game 1's `en` (`g1:<id>` in
    notes); 1,197 rows match game-1 glyph-soup rows game 1 never translated (notes say so). EXE text map and
    the sweep (`tools/strsweep.py`) in `docs/re/text.md`.
  - Phase 5 so far: game 1's pair glyphs ported (`tools/en.py`, `tools/font_en.py` MSB-first, `fonts/en6x12.txt`,
    `asm/pair.inc`/`pair_data.inc`/`font.asm`/`epilog.asm`), `tools/insert.py` (modes en/marker/ruler/torture;
    events rebuilt + relocated to GDATA's end with all six u16 directories repointed; EXE strings in place in PSX
    and OMK; FIN staff roll markers in place), `build.py --mode`, `tests/test_insert.py` (6 tests, in check).
    Hook space: PSX 0x80192A6C / OMK 0x8019122C, proven unwritten by `tools/debug/freewatch.lua` (`space.md`).
    `build/fd3_en_marker.cue` smoke-boots (`work/qa/p5/smoke_marker`) and warps: ids render clean
    ("[e835.1F2A]The quick..."; title, week1, ev_kaiwa1). Ruler build: 14 scenes arrive (`work/qa/p5/ruler/`);
    measured dialogue 40, battle 40, endings 40 (EPILOG hook works) in `docs/windows.tsv`; credits show [Fn].
  - Phase 5 finished (2026-11-22): `build.py --mode marker --qa ID=text` (single EXE-string override: text at
    0x80193800, every u32 pointer repointed, PSX and OMK; `tests/test_insert.py::test_qa_override`). **Width gate
    done: all 13 variants in `docs/windows.tsv` measured** (`work/qa/p5/qa1/`): hub help 40, location 11, ability
    list 12 (engine copies 6 cells of a name), week tags/ACTION 10, save menu 12 (bar), confirm prompt 22 (prints
    the JP glyph count, nothing hidden: drop game 1's leading spaces), Yes/No 5/6 after 3/4 hidden letters (keep
    game 1's padding), angel name 10, credits 14 cells = 28 letters with a FIN pair hook. Torture build
    (`--mode torture`: each script's first row + `insert.TORTURE_ROWS`) renders every glyph in the dialogue and
    battle boxes (`work/qa/p5/torture/z_dialogue.png`, `z_battle.png`). **0x801956D0 is not free** (a card load
    overwrites it, DMA invisible to freewatch; `docs/re/space.md`). `tools/wrap.py` + `tests/test_wrap.py` ported
    from game 1 (20 pair cells x 3 lines, test ties it to `windows.tsv`). The hub's ラビエル is the name stored in
    the JP-written save card (`work/saves/week2.mcd`), not a missing string (default name = row PSX.141EE0).
    EPILOG hook blob at 0x80170000: byte-identical to the built file in RAM dumps at f12000/16000/20000 of endings
    1, 12 and 26 (`work/qa/p5/epi/`, ruler build), whose boxes draw the markers.
  - Phase 6 so far (2026-11-22): game 1's `batches.py` (eNNN files, soup/seeded families skipped, `g1` hint
    column), `compact.py` (prints `#g1` hint lines), `honorifics.py`, `pairs.py`, `docs/translator-brief.md`,
    `docs/style-reference.md`, `docs/synopsis.md` (game 1's; extend with this game's additions) ported. Game 1's
    glossary imported whole into `glossary.md`, new names added "(FD:EnM)" (decisions D10). `tools/seed_g1.py`
    seeded 2,003 more event rows from game 1's translator output (1,122 differ only in code args, 881 only in
    codes around the same text; notes `g1~:`). `tools/g1hint.py`: nearest game-1 English as the batch hint.
    `batches.py split` -> 32 batches / 1,433 families (trans/batches, ~3,500 JP glyphs each). b001-b002 translated
    by the controller (Sievas/Ryudral/Ashe/Nasadia Q&A rows, Juliana scouting reports), checked OK, merged.
    b003-b006 (2026-11-22, one worker): boss-fight scenes (e469-e508), per-hero "go again" lines (e516-e572;
    fb:01..0D = the hero index in e533/e570 rows), Reiv/Griffin/Felimi/Dian/Yaruru/Fiana/Beasia Q&A (e581-e587).
    The angel's stock questions reuse b001-b002 wording (`grep` trans/en/b00N.tsv). Rows with per-line `{f7:0180}`
    (e478, e504, e507) get bare `{n}` from wrap.py: fine, the colour code persists across `{n}` (as e835 shows).
    b007-b013 (2026-11-22, one worker): Beasia/Tia Q&A (e587-e588), Sievas/Reiv/Griffin/Felimi/Yaruru/Fiana/Ashe
    story scenes (e589-e671, most with a `#g1` hint), Reiv ceremony + Griffin/Lydia thanks (e736-e739), hero-visit
    greetings e746 (CB10.. Yaruru, 6303.. Ryudral, 1E04.. Fiana, BB04.. Ashe). Hinted rows: start from the hint, then
    fix what this game changed. The hints often carry game 1's code args (`{e0:..}`, `{fb:..}`) and lack this game's
    added `{f7:0080}Name: ` prefixes; `batches.py check` catches both. Game 1's stock "He's gone..." spoken by a hero
    about the angel is gendered: e591.0DD6 uses "Gone, just like that...".
    From b014 on almost no row has a hint (b014, b023-b032: none): full translation, ~2 batches per worker.
    b014-b019 (2026-11-22, one worker): hero-visit greetings e746/e747 (fb 79-7D/83-84 Yaruru, 8C-91 Ryudral,
    A1-A5 Fiana, B5-B9 Ashe; e747 fb 15-20 Sievas, 29-34 Reiv, 3D-48 Griffin, 51-55 Felimi, 65-69 Dian),
    love-confession scenes e791-e802 (choices in glossary), fairy missing-hero reports e817-e821 (Juliana),
    Lily/chicks e829, mission reports e833-e835. Report rows carry `{f7:0180}` per line: keep each JP line, <=40
    letters, and keep every `{name:..}` on the same line as in the JP (`batches.py check` fails otherwise); reuse
    game 1's report wording (`grep "Peace level up" ../favorite-dear-en/script`: "rogue dragon Macula Dragon",
    "Knight in Black", "hero candidate", "One hope for saving Infos is lost!"). Mission-title runs (e817.2F1C,
    e833.10C4, e834.17DA) are `-` (glossary).
    b020-b023 (2026-11-22, one worker): last e835 reports (Reiv/Tia/Juliana loss, time-ran-out endings, the demo's
    "This version ends here" e835.20EE and e914.19DA "TGS version" rows translated plainly), Milias/Ashe e840,
    hero rematch lines vs Apollyon/Iuvart/Rasuel/Gaap e859-e862 (no hints; voices by pronoun), ending speeches
    e865-e875/e909 (hints use ¬ where this game has §..¶: always follow the JP codes), Reiv-rescue offers e904,
    Yaruru/Rush e906, Juliana battle lines e910, epilogues e892 (Felimi, hint) and e911/e912 (Juliana, new),
    Juliana scouting e913-e914, confession e915, tavern scene e916 (thugs "Man 1:"/"Man 2:"/"Men:").
    b024-b025 (2026-11-22, one worker): Juliana's story e916-e922 (Andrang castle, Kane and Velk, the shoulder
    scar), hero-visit greetings while travelling/at night/eating/resting/training e923 (fb C9-CD rough male
    voice, DC-E1 天使サマ -> "my dear angel", F1-F5 and 04-09 polite).
    b026-b032 (2026-11-22, one worker): Juliana's call/gift/request scenes e924, talk topics e925 (travel, night,
    meals, rest), mission accept/refuse e927 and e935-e939, Beasia's bear cave e933 (two angel-gender variants),
    Juliana's brother arc e934/e945-e952 (**Velk is Rasuel in disguise**, e949), fairy reports e940-e944, every
    hero's rest/training topics e953-e963. Speaker labels and other rulings: glossary "Juliana's arc". New term
    ジル "Gil" (Griffin's teacher). `batches.py todo`: 0 left.
    EXE rows: 29 of 33 filled (Juliana/Andrang name rows, mission titles, gift items, save messages, weapons, 男/女
    "Male"/"Female" in 4-byte slots). Kept Japanese as in game 1 (glossary "EXE/staff/card leftovers"): packed
    label rows PSX.141F44/141F70, name-entry grids, the 8 memory-card titles in `script/sjis.tsv`. Staff roll: all
    97 rows filled (game 1's layout; 6 readings flagged "name reading unverified" in notes).
- **Review pass (2026-11-22, one worker):** `tools/pairs.py` was printing an empty JP column (read the batch's last
  column, the `g1` hint) - fixed, pairs now 507 KB for 32 batches. b014-b020 read in full: verdicts in
  `docs/review.tsv` (committed; one row per batch, `ok`/`fixed`), Minors in `docs/polish.md`. Fixes: game 1's
  "Sir... Felimi?"/"Lady... Nasadia?" -> "-dono" (D1), "the daughter of Omron" -> "a girl from Omron". Quality of
  b014-b020 is good; ~7 batches (~110 KB of pairs) fit in one worker's context.
  **Review finished (2026-11-22, second worker):** b021-b032 and b001-b013 read in full (all 32 batches now have a
  row in `docs/review.tsv`, every one `ok` or `fixed`). One fix: e606.068A "Griffin... sir." -> "Griffin...-sama."
  (D1). No meaning errors or voice breaks found. Minors in `docs/polish.md` (stiff "If I'll do, I'll go" for
  私でよければ across ~16 rows; heroes call their fairy "it", fairies are female; a few small wording notes).
  The review was a single read-only pass by the controller (Codex out of quota until 2026-11-26), not an
  independent reviewer; phase 9's per-chapter story pass is the second read.
  **Independent re-read (2026-11-22, third worker, after the phase 6 review file's fixes in 875365b):** all 32
  batches read again in a fresh read-only pass (verdicts `work/qa/review/verdicts/r2_b*.tsv`, all ok/fixed). Fixes:
  e833/e834 "calamity" wording back to game 1's, e618 "Come, this way", e650 "rebel army", e746 "No way!". New
  Minors appended to `docs/polish.md`.
- **Phase 7 (2026-11-22, done):** `python -X utf8 tools/build.py` builds the English disc (8 files edited);
  `tools/lint.py` (in check.py: every event/EXE/staff row's codes, 20-cell lines, page heights, EXE slots from
  `docs/windows.tsv`, 28-letter credits) 0 findings on 12,573 rows; `tools/fitcheck.py` romdiff ok on all 8 files;
  `--identity` still byte-identical; 53 tests. Work: grown EXE strings (47: place names, fairy commands, items,
  ranks, mission titles; last PSX.136460) repointed to 0x80193200-0x80193800 in PSX.EXE and OMK.EXE (`insert.REPOINT`); 平和度/男/女 are fixed 8-byte copies, so "Peace",
  "M", "F" in place; English credits via `asm/fin.asm` (game 1's FIN hook re-found: docs/re/text.md §Credits),
  name lines indented one cell less to fit the block; shots `work/qa/p7/credits/credits_roll` read clean. The
  English build passes smoke (`work/qa/p7/smoke`) and `warp.py hub_system` shows "Save / Load" (`work/qa/p7/warp`).
  Glyph-soup rows (1,197) stay with an empty `en` (insert keeps the JP bytes; a `-` would be inserted literally).
- **Phase 7 review fixes (2026-11-22, `../.harness/reviews/...-phase7.md`):** (1) the op-0xDE list rows e396.1558
  (gift items + greeting), e817.2F1C, e833.10C4, e834.17DA (mission titles) translated line for line (glossary
  "op-0xDE lists"); report lines reworded so a 21-letter title fits. (2) D11 decided: label rows PSX.141F44/141F70 are
  pool strings indexed from 0x801516E0 (draw 0x800D67D0), translated field by field in place; grids and card titles
  kept, listed in new `docs/jp_kept.tsv`. (3) `tools/lint.py` fails an empty `en` whose JP has text unless it is
  codes-only, an event glyph-soup row (by note) or keep-listed; a `-` fails. (4) list-string caps (places 14, items
  16, ranks 12, missions 16) linted by address range as "unmeasured" (docs/windows.tsv rows); lines using a list-fed
  name slot measured with the list's longest entry (`lint.LIST_ROWS`). (5) `tests/test_enbuild.py` (in check, ~45 s):
  builds `en` in memory, fitcheck ranges, insert's write log (`insert.put`/`log_diff` -> `romdiff.check`: every
  changed byte has a write, no overlap, original bytes match), six directories agree / kinds kept / no overlap,
  no branch into a hook. (6) PSX.133E3C "Is this okay?" without game 1's spaces. New `tools/setrow.py` (set `en`
  cells from a patch TSV through extract's writer). Build sha1 06900d99bb69a9d85d31f359dbf3b2eff22f036d, smoke ok
  (`work/qa/p7r/smoke`), fitcheck ok, 59 tests + lint 0 findings.
- **Phase 8 worker 1 (2026-11-22):** graphics text ported from game 1: `tools/gfx.py` (u16 sector directory at
  0x170244, MSB-first font), `tools/labelfont.py`, `fonts/label14.txt`/`narrow3x7.txt`, `gfx/*.tsv` (e008 e009
  e012-e015 e142 e143 e145 e203 e243 + e207 mirror, tutorial charts s40193/s40269/s40345 = game 1's s40127/..,
  TTL_OPT/TTL_OPT2/TTL_INFO). Changed images e143 (MIA/KIA stamps) and e145 (save panels) take game 1's specs
  cleanly (`work/gfx/en/e143.png`, `e145.png`). insert.py applies them (en mode, logged), fitcheck allows each slot
  and the PSS files, `tests/test_gfx.py`; lint now fails glossary Avoid spellings (0 hits). Build 11 files edited,
  fitcheck ok, 70 tests. **First tour** of the English build (sha1 163192ec..., before this commit's docs only):
  `warp.py --all --cue build/fd3_en.cue --root work/qa/p8/tour`, all 116 reached; battle_t0301 "blank" and
  ev_e945 "stuck" are warp timing (the original run shows the same end frame / was flaky too). `tools/qa_sheets.py`
  (game 1's) made full-size sheets; gate: `qa_gate.py init work/qa/p8/manifest.tsv work/qa/p8/tour --glob
  "qa_sheet*.png" --build build/fd3_en.bin` = 298 sheets, chunks of 25 in `work/qa/p8/chunks/` (11 chunks),
  brief `docs/visual-qa-brief.md` (game 1's, adapted; JP reference = `work/qa/warp/<scene>/`). Verdicts so far
  (`work/qa/p8/verdicts/w1_graphics.tsv`, 5 sheets): seen English in game: e008 hub buttons, e142 fairy panel,
  e145 "New Data", TTL_OPT card notice, e015 page buttons. One issue: the name-entry grid is still the kana page.
  Name-entry port lead (codefind/addrmap mapping of every game-1 name.inc site): `docs/re/text.md` §Name entry.
- **Phase 8 worker 2 (2026-11-22):** battle name plates English: game 1's `asm/btname.inc` ported
  (`asm/btname.asm`, PSX.EXE only, en mode; routine 0x8001A680 replaced in place, every address re-found by
  `codefind`, docs/re/graphics.md e204-e206 row), `tools/btname.py`, `trans/btname.tsv` (273 rows: game 1's 272 +
  H13 Juliana), `fonts/caps4x7.txt`, `tests/test_btname.py`; fitcheck allows the asm's diff; test_enbuild's
  branch-into-hook test skips the replaced routine's own dead branches (`REPLACED`). Seen in game:
  `work/qa/p8/bt/battle_forest` f015300 BANDIT / CHIEF / DIAN, LV digits intact. Build sha1 8550312e..., check 72
  tests + lint 0, fitcheck ok. Visual QA of chunk 000 started and stopped: every battle sheet showed the kana
  plates, so battle verdicts wait for the re-tour; one reading kept: e727.181E "(None: I've been captured!)" is
  game 1's wording of the game's own stub line for a captured hero (ok). Hero-skill port lead (addresses, and the
  renderer changed here): `docs/re/text.md` §Hero skills.
- **Phase 8 worker 3 (2026-11-22):** code ports finished. Hero skill names: game 1's `asm/skill.inc` ported
  (`asm/skill.asm`, PSX.EXE only; the renderer's branches changed, hook = hero branch exit 0x800EA1CC; docs/re/text.md
  §Hero skills); seen with `hub_ability4` + `tools/debug/herosel.lua` (forces a hero; LONG=1 = longest names:
  Double Boomerang fits), `work/qa/p8/skill/`. Name entry: game 1's `asm/name.inc` ported (`asm/name.asm`, every
  site re-found by aligning the disassembly; code at `insert.NAME_SPACE` 0x80193600, REPOINT now ends there; §Name
  entry); `newgame_grid` shows the Latin page + "Raviel", `newgame_name10` commits Raviwwwwww and the intro prints
  it (`work/qa/p8/name/`). Check 72 tests + lint 0, fitcheck ok, smoke ok. Re-tour: `work/qa/p8/tour2` (see Next).
  **Re-tour done** on build sha1 29bce9e6... (`warp.py --all --root work/qa/p8/tour2`): 114 ok; battle_t0201
  "blank" (its final frame is a box mid-print, the same shot as the JP run) and ev_e945 "stuck" (end frame identical
  to the JP run's, as in the first tour): warp timing, not bugs. `qa_sheets.py work/qa/p8/tour2` + `qa_gate.py init
  work/qa/p8/manifest2.tsv work/qa/p8/tour2 --glob "qa_sheet*.png" --build build/fd3_en.bin` = 293 sheets;
  `todo ... work/qa/p8/verdicts2 --size 25 --out-dir work/qa/p8/chunks2` = 12 chunks (000-011). The old
  `tour`/`manifest.tsv`/`verdicts`/`chunks` are superseded (keep only as history).
- **Phase 8 worker 4 (2026-11-22):** visual QA of chunks2 000 and 001 (50 sheets: battles, credits, credits_roll,
  ending_movie, epilog, epilog_end10-12) in one read-only pass by the worker itself (no subagents allowed by the
  dispatch; Codex out of quota): all `ok`, verdicts in `work/qa/p8/verdicts2/chunk_34990ab3ae05_00{0,1}.tsv`
  (gitignored, like all of `work/`). Checked against the JP warp: the epilog/credits_roll garbled background is
  warp state (same in JP); the ending save prompts touching the "Fin." logo match the JP layout (f014550); the wide
  font's "(" reads like "<" in sheets but is the paren glyph. Gate: 243 of 293 sheets still without a verdict.
- **Phase 8 worker 5 (2026-11-22):** visual QA of chunks2 002-005 (100 sheets: epilog_end1-26 except end7-11,
  which are in chunk 006) in one read-only pass by the worker itself: all `ok`, verdicts in
  `work/qa/p8/verdicts2/chunk_34990ab3ae05_00{2..5}.tsv`. Every hero's epilogue narration reads cleanly (names per
  glossary, no clipping); e890.0268's double gap before "He seems to be living straight down" is the JP script's own
  double blank. Gate (`$SKILL/scripts/qa_gate.py check ...`; the gate script lives in the skill, not `tools/`):
  143 of 293 sheets still without a verdict, 0 not ok.
- **Phase 8 worker 6 (2026-11-22):** visual QA of chunks2 006-011 (143 sheets) in one read-only pass: **all 293
  sheets now have a verdict; 8 `issue`**, 7 of them fixed in this commit, 1 open:
  (a) the scout confirm after picking a hero showed "s okay?": that box prints PSX.133E3C from byte 6 (letters
  7-22; JP shows only よろしいですか？), the name-entry box from byte 0. Game 1's 6 leading spaces restored (`'      Is
  this okay?'`, centred in both boxes: `work/qa/p8/fix1/ev_bos_clr` f014330, `newgame_name10` f007650); the phase 5
  windows.tsv note corrected. (b) the angel's visit/talk menu lists each `{fb:XX80}{spk:E783}` question's first page
  as an option, indenting only its first line: 2-line questions spilled onto a third line (ev_scqa01) and a 39-letter
  one touched the frame (ev_sqa01). All 519 such rows (~70 distinct questions) rewritten to one line <= 38 letters
  (wording kept close; game 1 had the same 2-line forms), new lint rule `lint.QUESTION` + test, windows.tsv
  `question_menu`; seen fixed in `work/qa/p8/q/ev_sqa01` f013760. (c) **open: the Omake "Mini Event" dialogue is
  Japanese.** OMK.EXE carries its own mini-event script at file 0x13B708-0x13EB86 (RAM 0x8014AF08.., OMK's copy
  of the script load buffer; pc 0 = `0x28` goto, no file header: the argument table must come from elsewhere,
  GDATA grammar with the battle-map printer codes FFF1/FFFA speaker, FFF0 newline, FFF3/FFF2 page). Parsing it
  with a GDATA argtab (entries 416/515/725/780/815 agree; 395's does not) gives 38 segments but mis-reads op runs
  as text in places, so the true argtab (from OMK's VM) is needed. ~9 short scenes (Sievas/Fiana at the Kvaal
  church painting, Juliana's castle, Yaruru's carving, Beasia, a princess, Dian found out as a girl, ...); no row in
  `script/` has this text. New confirmed non-bugs in `docs/visual-qa-brief.md`. Build sha1 bf85c679..., check 73
  tests + lint 0, fitcheck ok. The gate is STALE (tour2 ran on 29bce9e6).
  **(c) done 2026-11-22 (56b8944):** OMK's own argument table found (file 0x13B4C4, 234 entries; `docs/re/text.md`
  §OMK mini events); `script/omk.tsv` (38 rows) extracted and translated; `insert.omk_mini_edit` rebuilds the script
  in place (0x32D4 of 0x347E bytes); lint covers omk.tsv; fitcheck allows the slot; test
  `test_omk_mini_events_fit_in_place`. Seen in game: `work/qa/p8/omk2/omake_mini/post.png` ("You... Weren't you at
  the church / in Kvaal?"). Build sha1 7bef143f..., check 74 tests + lint 0 (12,617 rows), fitcheck ok.
  warp.lua: with a POST route, mash waits for it to finish; warp.py `--frames` also overrides a named scene's length.
  **Interrupted:** the full re-tour into `work/qa/p8/tour2` and a read-through of every Mini Event page were both
  stopped by the host (system low on memory), part-way. tour2 is now a mix of old and new shots: re-run it whole.
- **Phase 8 worker 7 (2026-11-22, build 7bef143f unchanged):** (a) **Mini Event read in full:** mashing the menu
  replays scene 1 only (the EXE passes the scene number; the script reads it with `007E 8002` and switches on it at
  pc 0x16 and 0x40, 12 cases). New warp.lua `MINI=N` rewrites both switches to scene N
  (`warp.py omake_mini --name mini_N --frames 22000 --var 'AFTER="mash"' --var MASH_EVERY=150 --var MINI=N`). All 12
  scenes run (`work/qa/p8/mini/mini_1..12`, reading sheets `read_N.png`), read by me in a read-only pass: English
  throughout, no clipping, no Japanese (3-line pages fit; scene 3 ends on a wide-font CG box, as designed). (b)
  Graphics seen: e012/e013 status backgrounds (Angel/Fairy pages, `work/qa/p8/gfxcheck/hub_all.png`), tutorial
  charts Part 1 and Part 2 (`setumei_z.png`, from tour2 ev_setumei f013800/f016500). (c) **Text coverage ported**
  (game 1's design, `docs/re/debug.md` §Text coverage): `tools/lua/textlog.lua`, `tools/textcover_map.py`
  (strings/convert/report), `tools/cover_sweep.py` (freeze/run, resumable). Frozen: `work/qa/cover_build` (11,424
  rows; 164 rows in 12 entries no event id loads, waived in `waive.tsv`). (d) `tools/qa_carry.py`: carries verdicts
  to re-tour sheets with the same sha1. (e) tour3: `warp.py --all -j 2 --lua tools/lua/textlog.lua --root
  work/qa/p8/tour3`: 115 ok + battle_t0301 "blank" (the known warp-timing end frame, as in tours 1 and 2); log
  `work/qa/p8/tour3_run.txt`. `qa_sheets.py` -> 296 sheets; `qa_gate.py init work/qa/p8/manifest3.tsv
  work/qa/p8/tour3 --glob "qa_sheet*.png" --build build/fd3_en.bin`; qa_carry from manifest2/verdicts2 carried only
  14 (frame timing differs run to run, so sheets rarely match pixel for pixel); `todo ... work/qa/p8/verdicts3
  --size 25 --out-dir work/qa/p8/chunks3` = **12 chunks (chunk_5454ac7a3215_000..011), 282 sheets to judge**.
  Coverage from tour3's own logs: 97 / 11,424 rows (`textcover_map.py convert work/qa/p8/tour3/*`).
- **Phase 9 (2026-11-22, worker 11; build 104693c3, smoke ok, fitcheck ok, check 74 tests + lint 0):**
  - DONE: `tools/release.py` (game 1's, adapted: build, check, fitcheck, smoke, jpcheck, `qa_gate check` on every
    `work/qa/**/manifest.tsv` + GATES p8/manifest3 and manifest_stress, textcover over the log.txt of work/qa/cover,
    force, force_pilot (strings + waive from work/qa/cover_build), polish, README placeholders, debug off, xdelta -B,
    re-apply, zip `release/Favorite_Dear_Enkan_no_Monogatari_EN_v1.0.zip`). Each gate tried alone: visual + stress
    + textcover pass. `tools/jpcheck.py`: rows 0 unintended, PSX.EXE/OMK.EXE text spans 0 runs (1,354 JP rows sit in
    unloaded entries). README filled (Redump SLPS-03286, size/CRC/MD5/SHA-1). Retired (renamed `.retired`):
    p8/manifest.tsv, p8/manifest2.tsv (superseded tours), review/manifest.tsv (phase 6 per-batch review, superseded
    by the story pass; its pairs changed because pairs.py now reads EN from script/).
  - DONE polish pass: all 19 lines of `docs/polish.md` ticked (13 fixed, 6 waived with reasons); new
    `tools/showrow.py` (flattened JP/EN of ids), `tools/subrow.py` (exact-once substring edits -> setrow.py).
  - Story pass: `tools/pairs.py --chapters` (EN from script/, + ch08 = OMK Mini Events) -> 8 files in
    `work/qa/story/chapters`; brief `work/qa/story/brief.md`; `tools/story_review.py chNN` runs codex, but **codex is
    out of quota until 2026-11-26** (re-checked 2026-11-22 worker 12), so chapters are read by the worker itself in a
    read-only pass. Done: ch08 ok, ch07 ok (2 Minors fixed directly); worker 12: ch04 ok, ch05 ok, ch06 ok, ch02 fixed
    (e606.068A: a speaker-only "Idavel:" box merged back; **speaker-label colon spacing**: 87 labels in 41 rows read
    `Ellen:Why` because `{f7:xxxx}` is a colour code, not a line break; all got the space (lint 0; the polish
    waivers for e911/e947/e468 were wrong and are now "fixed")); worker 13: ch01 ok (2 Minors fixed: e581.59A8,
    e591.0DD6; check 74 + lint 0; `qa_gate check` on the story manifest: only ch03 lacks a verdict); worker 14: ch03
    ok (1 Minor fixed: e800.032E Beasia's confession roughened, "What're you gonna do", "figures", "gonna lose
    it"); story gate 8/8 ok. Notes for later chapter edits: `tools/subrow.py` breaks on rows
    holding `"` (csv QUOTE_NONE): for those, write the `id/en/notes` patch yourself and run setrow.py. For each: fix Critical/Important (and cheap Minors) with subrow.py, then `pairs.py --chapters`,
    `qa_gate.py init work/qa/story/manifest.tsv work/qa/story/chapters --glob "*.txt"`, and only THEN write
    `work/qa/story/verdicts/chNN.tsv` (`chNN<TAB>ok|fixed<TAB>note`) and `touch` the other verdict files whose
    chapters changed only by your fixes (a verdict must be newer than its chapter's last change).
  - DONE (worker 14): rebuilt (sha1 24d6d135, 11 files edited, fitcheck ok, smoke ok); p8/manifest3 and
    manifest_stress waived for 24d6d135 (git diff since 6cf7aa8 touches no insert/asm/tbl/gfx file, only QA tools,
    README and script text); `python -X utf8 tools/release.py` exits 0: build, check, fitcheck, smoke, jpcheck,
    3 qa_gates, textcover (775 logs), polish, README, debug off, xdelta 1,589,106 bytes, re-apply ok. Any later
    text edit changes the build sha1: re-waive both p8 gates (and re-verdict the touched chapter) before re-running
    release.py. Never `gh release create`.
  - Phase-7 review leftovers (non-blocking, not release gates): pool label rows PSX.141F44/141F70 on screen, e396
    gift advice and e833/e834 long titles in game, lint extras (listed below).
- **Phase 8 notes (QA in the emulator, done):** (1) DONE 2026-11-22: tour3 visual QA, `qa_gate.py check
  work/qa/p8/manifest3.tsv work/qa/p8/verdicts3` exits 0 (296 ok, 0 issues). 101 sheets carried by pixel identity
  (`carried_*.tsv`: whole sheet, every tile, or every frame same as an ok tour2/tour3 tile), 19 ending-movie video
  sheets (`movie3.tsv`), the rest read (`read3.tsv`). Checked against JP: "Is this okay?" is left-aligned in JP too
  (x=188 vs 190, so no centring needed); the angel-menu question drawn indented over the hero's reply (ev_scqa01)
  is JP's layout. (2) Text coverage: DONE 2026-11-22 (worker 10). Pass 4 `--choices` finished (22 rows left);
  `--hero 1` (no PRINTPATCH: with it SS0105 showed 0/5) cleared SS0105 10/10, SS01042, SS0805, SS0202, SMEN12, e924;
  SS0905 (e649.0BBE) needed a KEYPATCH fix: its message opens `FFE0 103F FFFB 8064`, and `keyed_target` in
  `tools/lua/textforce.lua` now also accepts an `FFE0 x` prefix before the key; SS0102 (e590.200E) sits behind a
  random roll (`0027`, `%100`, `002F ... 0x19`), shown with `--only e590 --mash 13`. Only SS0507's 4 proven-dead rows are
  left. Gate: `textcover_map.py strings --out work/qa/cover_build/strings.tsv --waive work/qa/cover_build/waive.tsv`
  (strings.tsv byte-identical to the frozen one), then the log.txt files of work/qa/cover, force, force_pilot copied
  into one dir and `textcover.py DIR work/qa/cover_build/strings.tsv --waive work/qa/cover_build/waive.tsv`:
  11256/11424 shown, 168 waived, 0 failing, exit 0 (logs `work/qa/force_p4.log`..`force_p17`, `force_m*.log`).
  Older notes: **2026-11-22 worker 9:** pass 1 finished
  (6,081 -> 266 non-choice rows), pass 2 (same command, log `work/qa/force_p2.log`) -> 70. **warp.lua fix**
  (243cc7f): `--battle` now waits until its own id is in the id table (e945-e951 = ids 550-556 load after slot 32,
  so `id_of` saw junk and raised "no event id loads e945"); pass 2 then showed e945-e951. TM12ALL 34/34 with
  `--only e789 --hero 1` (p6), TM02ALL 12/12 with `--hero 1` (p6-p8, three runs), TM0312A 3/3 with `--hero 3
  --keypatch --var STARTPATCH=1` **without PRINTPATCH** (p7; PRINTPATCH finds sites, so STARTPATCH never fires).
  SS0507 (e623) proven dead as in game 1 (`docs/text_unshown_proven.tsv`, merged by `textcover_map.py strings
  --waive`; re-run that before the gate). Pass 3 (same options, -j 1, `force_p3.log`) and pass 4 (`--choices`, no
  RECHOICE, -j 2, `force_p4.log`, 25 files done) were **killed by the host for low memory** (other projects' agents
  share it; 5 emulators at once was too many). **Left now: 286 rows in 70 files, 270 of them choice-menu rows**
  (SMENxx 10 each, SLOVExx 1 each, SSxxyy, e915-e934; `textforce.py left --also work/qa/cover --also
  work/qa/force_pilot`). Next: resume `--pass 4 --choices` (same command as above, at most -j 2 total), then a
  normal pass for the 16 non-choice rows (SS0105 10 rows: 0/8 in pass 2, PRINTPATCH 0 sites: look at its code),
  then `textcover_map.py strings --waive` + `textcover.py` across `work/qa`. **2026-11-22 worker 8:** the plain sweep was stopped at 79
  entries (186/11,424 rows: ~2 per entry); game 1's forcing driver is ported (`tools/textforce.py`,
  `tools/lua/textforce.lua`, `docs/re/debug.md` §Text coverage; pilot e481 10/10). Pass 1 over all 518 entries:
  `python -X utf8 tools/textforce.py run --also work/qa/cover --also work/qa/force_pilot -j 2 --keypatch --var
  SKIPKEY=1 --var ADOPT=1 --var PRINTPATCH=1 --var RECHOICE=1 --var NOBATTLE=1 --var MASH_ROTATE=3` (log
  `work/qa/force_p1.log`; resumable with `--pass 1`; `textforce.py left --also work/qa/cover --also
  work/qa/force_pilot` counts what is left). **Pass 1 was stopped by the host (system low on memory) after 292
  of 517 files (last e716)**: 6,081 of 11,260 loaded rows still unshown (was 11,153), in 291 files. Nearly every
  file run shows all its wanted rows in one go (KAIWA1 300/300, T01SEN 22/22 in pilot pass `force_pilot/p2`;
  SQA01 102/102); partial so far: T0204 13/14, T1104 12/13. Forced pages draw clean English
  (`force_pilot/p2/ev_e747/f028500.png`). **Resume:** the same command with `--pass 1` (it skips finished runs);
  check free memory first, and drop to `-j 1` if the host is short. Then later passes for the leftovers
  (`--choices` for the 339 choice-menu rows, ENTRYGO/STARTPATCH cases as in game 1), proofs for dead rows in
  `docs/text_unshown_proven.tsv`, and `textcover.py` across `work/qa` must exit 0. Older notes on the sweep: (frozen build 7bef143f in `work/qa/cover_build`, log
  `work/qa/cover_sweep.log`, resumed 2026-11-22 07:15 at -j 2 by worker task_e70ac39af3f8; 76/518 entries done at
  08:38, ~1 entry/min when nothing else runs; that worker handed back at its context limit with the sweep still
  running in its terminal. **Before resuming, check it is not still running** (`tasklist | grep -i pcsx`, and whether
  the log's last line or the newest `work/qa/cover/ev_*` dir is minutes old); if dead, re-run `python -X utf8
  tools/cover_sweep.py run -j 2` in the background (resumable; at most 2 emulators besides one for other work)), then `textcover.py work/qa/cover
  work/qa/cover_build/strings.tsv --waive work/qa/cover_build/waive.tsv` (add `work/qa/p8/tour3` as a second log dir
  if textcover.py takes several). Then port game 1's forcing driver (`docs/re/debug.md` §Text coverage). Speed-up idea:
  a savestate just before MYH16 loads (f~12100) + `emu.py --state-in` would skip ~12k frames per run. (3) DONE
  2026-11-22 graphics: e243/e207 stamps (POISON, battle_t0901), tutorial chart Part 3 (`warp.py ev_setumei --frames
  26000 --var MASH_ROTATE=2`, `work/qa/p8/gfxcheck/part3_fade_x40.png`); e203 is English as an image but **not reached
  and likely unused** (the opening's "2. See the overall flow." plays e830's charts; new `tools/lua/tuthook.lua
  --var FLOW=1` picks it; details in `docs/re/graphics.md`). (4) DONE 2026-11-22 stress saves: scenes stress_w10_*
  (WWWWWWWWWW, AP 999: week, hub, ability list, angel page, save panel), stress_i_* (Ivy, AP 1), stress_name1_week
  (I); `work/qa/p8/stress`, gate `qa_gate.py check work/qa/p8/manifest_stress.tsv work/qa/p8/verdicts_stress` exits
  0. Heroes in the party: still only `herosel.lua` (LONG=1 longest names, `work/qa/p8/skill/`); no game-written
  hero save. (5) DONE 2026-11-22 inkbox: every centred box measured against the JP shot of the same scene and frame,
  all at JP's offset or the nearest half-cell step (`docs/inkbox.tsv`). (6) DONE list widths: rank measured in game
  (12, `work/qa/p8/rank/z_rank.png`); place/item/mission caps are the JP strings' own width, confirmed as a model by
  rank (`docs/windows.tsv`). Smoke on build 7bef143f ok 2026-11-22 (`work/qa/p8/smoke_final`). Left for phase 8:
  the sweep + textcover.py, the forcing-driver port (game 1's `tools/textforce.py` 303 lines + `tools/lua/textforce.lua`
  402 lines; re-find every address), and from the phase 7 review: see the pool label rows PSX.141F44/141F70 on screen (gift menu, status);
  see e396's gift advice and e833/e834 reports with a long title in game (they need story flags: `warp.py --event
  e396` lands in the scene but its mash route takes another branch, `work/qa/p7r/warp/ev_e396`); whether any glyph-soup row is ever drawn (`textcover.py`); lint extras (leading/trailing blank parity
  with an exception list, stub last lines, glossary "Avoid" spellings). Watch: PSX.133E3C "Is this okay?" now has
  no leading spaces (check centring in game); the repointed place names on the map and hub; the credits' long names (FIN.009 "Kazuhiko Watanabe").
- **Known gaps (debug tool):** e964 (id 549) stalls in MYH16's context; how the title menu normally reaches
  OMK.EXE is untraced (the exec warp covers it); endings above 26 not tried; stress saves come in phase 8.
- **Open bugs:** none.
- **Waiting on the user:** (not blocking) whether and when to publish `release/Favorite_Dear_Enkan_no_Monogatari_EN_v1.0.zip`
  as a GitHub release; agents never run `gh release create`.
