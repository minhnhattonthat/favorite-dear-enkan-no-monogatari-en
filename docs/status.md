# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool next (phase 1 recon done 2026-11-21, 1st worker; no build yet).
- **Done:**
  - Step 0: template filled, `tools/skill.py`, PCSX-Redux in `tools/pcsx/` (fetch_emu), BIOS + mkpsxiso/armips/xdelta
    copied from game 1's repo, guard hook in `.claude/settings.json` (canary `sed -i` blocked), pre-commit hook
    (`core.hooksPath tools/hooks`, CHECK = `tools/check.py`; a failing test was rejected), `rom.sha1` +
    `tests/test_rom.py`, original disc smoke-boots to the title menu (`work/qa/smoke_orig`, scripted Start works).
    Not checked: keyboard input in the PCSX-Redux window (headless runs only).
  - Phase 1: **this game is an expanded re-release of game 1 (`../favorite-dear-en`)**. Same engine and layout,
    most data byte-identical, 56% of event characters are verbatim game-1 `jp` rows. Recorded in `docs/re/`:
    encoding (`tbl/jp.tbl` from game 1's table + font match; font MSB-first at PSX.EXE 0xFA6C0; NCODES 0x6F0), the
    GDATA/SDATA u16 directories (PSX.EXE 0x170244 / 0x1700E4), 568 event scripts that all parse with game 1's
    grammar (13,261 segments), EXE strings (952, the same in OMK.EXE), credits in DATA/FIN.EXE (Shift-JIS), the load
    buffer (RAM 0x80148CBC, ~0x7000 B vs largest script 0x6C78), the graphics-text survey (game 1's lettered
    images mapped here, e143/e145 changed, new pictures have no text, logo stays per D5).
- **Next (phase 2, debug tool):** port game 1's `tools/debug/` (`warp.py`, `warp.lua`, `scenes.tsv`, `save.py`,
  `docs/re/debug.md` there): re-find its RAM addresses here (event-name table, event swap, New Game route) with
  `tools/retools.py` + `codefind`-style instruction matching (scratch script in the session: match game-1 code with
  immediates masked; promote to `tools/` when used again). Add scenes for the new modes in OMK.EXE (Omake, Visual
  CG, Mini Event). Then phase 3 identity build (game 1's `tools/build.py` approach: mkpsxiso on the dumpsxiso layout).
- **Open bugs:** none (no build).
- **Waiting on the user:** nothing.
