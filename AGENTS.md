# Favorite Dear: Enkan no Monogatari (PS1, NEC Interchannel, 2001) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `<SKILL_DIR>/SKILL.md`; `$SKILL` = the directory holding its SKILL.md, printed by `python tools/skill.py`). Read it before ROM, text or QA work.
**Reference project: game 1, `../favorite-dear-en`.** This disc is an expanded re-release of it (same engine, layout and most data; `docs/re/README.md`): reuse its tools, notes, glossary, translations and graphics redraws, re-verifying each game-1 constant. Game 2, `../favorite-dear-junpaku-no-yogensha-en`, is a different engine (style/glossary only).

## Commands (run from repo root)
- Build:    `python -X utf8 tools/build.py` -> build/fd3_en.bin/.cue (needs tools/insert.py, phase 7); `--identity` -> build/fd3_en_identity.*, exit 1 unless byte-identical (checks `rom.sha1` first)
- Check:    `python -X utf8 tools/check.py`  (tests + lint; the pre-commit hook runs this; `git config core.hooksPath tools/hooks` once per clone)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py C:/abs/path/build/fd3_en.cue --out work/qa/smoke --route tools/routes/boot.txt --smoke` (the original: `rom/...cue`; title menu by ~f3900)
- Warp:     `python -X utf8 tools/debug/warp.py SCENE|--event NAME|eNNN|--battle NAME|--all [--state] [--cue ...]` (scenes: `tools/debug/scenes.tsv`, `--list`; saves: `tools/debug/save.py`; `docs/re/debug.md`). Never ask the user to play to a scene
- Recon:    `python -X utf8 tools/gdata.py list|events|text N|gaps`, `tools/evscript.py check`, `tools/scantext.py FILE [--regions]`, `tools/gfxmap.py`
- Release:  not written yet (`tools/release.py`: patch + verify; never publish without the user)
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)

## Paths
- Original disc: `rom/Favorite Dear - Enkan no Monogatari (Japan).bin/.cue` (gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Unpacked: `work/disc/tree/` + `work/disc/layout.xml` (dumpsxiso, command in `docs/re/disc.md`).
- Emulator: this repo's own PCSX-Redux in `tools/pcsx/` (nightly 32338.20261121.15 x64 via `$SKILL/scripts/fetch_emu.py pcsx`; gitignored); BIOS `tools/bios/scph5500.bin`. Savestates: `work/states/`.
- Disc tools (gitignored, copied from game 1's repo; GitHub releases): `tools/mkpsxiso/` (Lameguy64/mkpsxiso v2.30 win64), `tools/armips/` (Kingcom/armips v0.11.0), `tools/xdelta/` (jmacd/xdelta-gpl v3.1.0).
- Text: `script/` (TSV: events/eNNN.tsv, exe.tsv, staff.tsv, sjis.tsv; `tools/extract.py` regenerates jp, keeps en/notes; `g1:` notes = seeded from game 1). Tables: `tbl/jp.tbl` (font codes, `tools/mktbl.py`), `tbl/ev.tbl` (event printer codes). Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the agent types (translator, reviewer, visual-qa, playtester, graphics) shipped by the plugin as `translate-retro-game:<type>` (Claude Code), `.codex/agents/` (Codex) or `.opencode/agents/` (opencode), never general-purpose: their short tool list cuts each agent's start-up context from ~43k to ~9k tokens.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- From Git Bash give Python Windows paths (`C:/...`); emu.py needs an absolute path to the .cue.
- Two text sites: PSX.EXE and OMK.EXE carry the same 952 EXE strings and each its own GDATA directory: every EXE edit goes into both.
- Font bits are MSB-first here (game 1: LSB-first); NCODES is 0x6F0 (game 1: 0x66C). Never copy a game-1 address without re-finding it.

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
