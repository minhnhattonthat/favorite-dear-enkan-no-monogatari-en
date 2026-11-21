# Debug tool (phase 2): how the warp works here

A port of game 1's warp (`../favorite-dear-en/docs/re/debug.md`, read it for the mechanics); this file records what
differs and what was re-verified. Entry point: `python -X utf8 tools/debug/warp.py SCENE` (scenes in
`tools/debug/scenes.tsv`, `--list`), `--event NAME|eNNN` for any event script, `--battle NAME`, `--all` to rerun
everything, `--state` to also write `work/states/<scene>.sstate`, `--cue build/fd3_en.cue` for a built disc. Every
run boots cold and drives the game with `tools/debug/warp.lua`. Output: `work/qa/warp/<scene>/arrived.png` (the
proof), shots every 150 frames, `sheet.png`, `log.txt` (`WARP OK <scene> f<frame>`), a line in
`work/qa/warp/results.tsv`; exit 1 if a scene was not reached, its proof is blank, or a `mash` scene froze.

## Addresses (re-found 2026-11-21 with `tools/addrmap.py` / `tools/codefind.py`, verified by the warps below)

| What | Here | Game 1 |
|---|---|---|
| MODE flag (5 = week screen idle, 1 transitions, 2/3 dialogue, 4 event) | u16 0x80187448 | 0x8001A4A8 |
| PHASE flag (1 = week screen idle) | u16 0x801875F0 | 0x8001A654 |
| current hero | byte 0x8018DA05 | 0x80020991 |
| loaded-event table (10 x u16 id, u16 offset, ..) | 0x80148C6C | 0x8016C5B8 |
| script load buffer | 0x80148CBC | 0x8016C608 |
| `load_event(id)` | 0x800A161C | 0x800C82E8 |
| event id -> **u16 name hash** | 0x8014FCFC + 2*id | 9-byte names at 0x80173640 |
| name-hash list (index + 395 = GDATA entry) | 0x801040E4, 570 (count u16 0x8015D6D6, base u16 0x8015D6D4) | name list |
| stage table (battle_start idx -> event id) | 0x80150780 | 0x80174BD8 |
| battle table {key, event id} | 0x8015060C | 0x80174A84 |
| program path table (12-byte entries) | 0x80151A90 | 0x80175E98 |
| `exec(path)` | 0x80014910 (path strings 0x80011B80..) | 0x8003C7D4 |
| `game_clear(a0)` | 0x80012E48 | 0x8003ABB8 |
| `battle_start` / `start_event` | 0x800A9D34 / 0x800A197C | 0x800D08E4 / 0x800C8688 |
| EPILOG ending select | EPILOG.EXE 0x8001EF00 | 0x80020A20 |

## Events are found by name hash (verified: MYH16, SEND01, e931, e878 play their own text from a cold boot)

`load_event(id)` reads `hash = u16[0x8014FCFC + 2*id]`, finds it in the 570-entry list at 0x801040E4
(0x800139A0, searching from both ends) and loads GDATA entry `395 + index`. The hash (0x8001392C) of a name is
`sum(c_i * 11^i) mod 2^32`, folded `(s + (s >> 16)) & 0xFFFF`; `hash("MYH16") = 0x354E` = id 32's slot. No
names are stored: game 1's 462 names hash onto 443 list slots here (`tools/debug/evnames.py`), so game-1 ids and
names carry over (id 32 = MYH16 again). 127 slots have no game-1 name (16-bit hashes collide, so brute-forcing names
gives junk); ids 462-595 are new. warp.lua takes a game-1 name or `eNNN` (the GDATA entry) and writes that hash
into id 32's slot once PSX.EXE is loaded (slot == 0x354E), so the game's own loader fetches the target when the
week-1 hero search starts MYH16. Arrival = id 32 in the loaded-event table.

The opening, title flow, week-1 route (`tools/routes/week1.txt`) and save/hub menus are game 1's, frame for frame:
title menu by f3750, week-1 screen at f11279, MYH16 at f13642.

## Saves (verified 2026-11-21)

- `save_write` (week 1) and `save_write2` (week 2, kind `week2`: week 1 played through by circle presses, back to
  the week screen at f21399) save into a blank card with game 1's System -> Save route; the run folder's
  `memcard1.mcd` is the game-written card: `work/saves/week1.mcd`, `week2.mcd`. Product code `BISLPS-0328600`,
  title "フェイバリットディア　円環の物語　ゲームデータ１", 2 blocks per save.
- Layout = game 1's: c0/c1 12-bit sums at 0x200/0x202 (formula checked on both cards, `tests/test_debug.py`),
  angel name at 0x204 and 0x19AE, AP u16 0x199C, week u8 0x215, **second week copy 0x2838** (game 1 0x275C).
  Week 1 -> 2 diff: 0x210-0x21A header, 0x22C-0x321 table, AP 100 -> 150, 0x27FC-0x2800, 0x2838 week, ...
- `tools/debug/save.py set` (week, AP, name, poke) fixes both sums. `save_edit` loads week2.mcd edited to week 5,
  AP 999, name ミカエルアン to the week screen showing them; the same edit with `--bad-sum` (scene run by hand,
  not kept in the list) lists as TURN 5 but never reaches the week screen, so the sum is checked and right.

## Programs

All programs differ from game 1's. _LOADE.EXE (0x801C0000-0x801C6800) carries a path table that now starts with
`\OMK.EXE;1`. EPILOG.EXE reads scratchpad u16 0x14 (ending; 0xFF = use byte 0x1C, the hero) and u16 0x16 (1 = hero
+ **13**, game 1 + 12: a 13th hero). `exec` scenes: credits (FIN), ending_movie (FD_MOV), epilog/epilog_endN,
minigame (FD_BALL), omake (OMK).

- **OMK.EXE** (verified 2026-11-21): exec'd from the week screen it plays a picture intro (no text), then the Omake
  menu "Visual CG" / "Mini Event" (English lettering in the original) at ~6600 frames after arrival; scenes
  `omake`, `omake_cg` (circle: a CG viewer), `omake_mini` (down, circle: an event dialogue on a battle map).
  How the title reaches OMK normally is not traced (PS_MOV.EXE holds its path next to FD_BALL/PSX).
- **FIN.EXE crashes PCSX-Redux's dynarec** ~1800 frames in (the emulator process dies, 0xC0000374); with
  `--debugger` (interpreter) the whole staff roll plays. warp.py adds `--debugger` to every FIN scene.

## Results and gaps (2026-11-21, `warp.py --all`, original disc)

All 116 scenes reach their target (`work/qa/warp/results.tsv`; battle_t0301 needed a rerun once: its proof shot
fell on a black fade). Not in the list: e964 (id 549) stops on an empty box in MYH16's context (a conversation that
expects other state); check its text from the file. New-event coverage beyond the 12 sampled `ev_eNNN` scenes is
for the text-coverage pass (phase 8) via `--event eNNN`.

Limits are game 1's: the target runs in MYH16's context (week 1, guild room, Shelly/Florinda); scripts that expect
other state may show wrong portraits or stop. `NAME:HERO` sets the current hero; battles need it.
