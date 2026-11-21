# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 6. Translate in progress: batches b001-b019 of 32 merged, b020-b032 to do (`batches.py todo`).
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
- **Next (phase 6):** translate b020-b032: `compact.py show bNNN > work/bNNN.jp`, write `work/bNNN.en` (same
  compact form), `compact.py expand work/bNNN.en bNNN`, `batches.py check bNNN`, `batches.py merge`. **Codex is
  out of quota until 2026-11-26** and Orca workers may not start subagents, so each worker translates itself:
  ~2-3 batches per worker before ~150k context (each batch ~20k tokens). After the batches: EXE rows without `en`
  (`script/exe.tsv`, 33 rows) and staff rows (`script/staff.tsv`, 97) and card titles (`script/sjis.tsv`, 8), then a read-only review pass (pairs.py)
  for Critical/Important, glossary NEW TERMs merged. Old notes: game-1 seeds cover 6,678 event + 852 EXE + 175
  staff rows; review the seeds against the
  measured limits: e.g. the confirm prompt row PSX.133E3C carries game 1's 6 leading spaces). Limits: dialogue
  40x3 (`wrap.py`), menus per `docs/windows.tsv`. **Glyph-soup rows (1,197, notes say so) get `-`**: `warp.py
  --event e573/e675` (`work/qa/p5/soup2`) and e420 (`work/qa/p5/soup`) play other scripts' dialogue, never the soup;
  as in game 1 their glyph table is unknown, re-extract in phase 7. `fitcheck.py` (game 1) is phase-7 work.
  Phase 7 also owes: repointing EXE strings (no in-place room), the save-menu rows (0x141C2C.., no u32 pointer) and
  the default angel name (0x141EE0, lui/addiu), the FIN.EXE pair hook for English credits.
- **Known gaps (debug tool):** e964 (id 549) stalls in MYH16's context; how the title menu normally reaches
  OMK.EXE is untraced (the exec warp covers it); endings above 26 not tried; stress saves come in phase 8.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
