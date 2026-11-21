# Graphics text survey (phase 1)

How (2026-11-21): game 1 (`../favorite-dear-en/docs/re/graphics.md`) already surveyed every image of the shared engine
and redrew each Japanese-lettered one (its `gfx/*.tsv` specs, `tools/gfx.py`). This disc reuses most of game 1's
GDATA byte for byte, so the survey is: (1) look up each of game 1's lettered sources here by content
(`python -X utf8 tools/gfxmap.py`), (2) render and look at every image whose bytes are new in this game
(`tools/gfxmap.py` second list; `tools/tim.py dump work/gfx/new --only N,..`; scan TIMs to work/gfx/scan_new/), (3) the
changed/new root files (`disc.md`). Sheets live in work/gfx/ (gitignored, regenerate with those commands).

Phase 8 (2026-11-22): every "reuse/re-apply game 1" row below is now built: `tools/gfx.py` + `gfx/*.tsv` (game 1's
specs; sector images renamed s40193/s40269/s40345). Seen English in game so far: e008, e142, e145, e015 buttons,
TTL_OPT (`work/qa/p8/verdicts/`).

Japanese drawn as graphics (each row must be English in a zoomed cold-boot shot by phase 8, except where noted):

| Source here | Game 1 source | Same bytes? | Japanese in it | Plan |
|---|---|---|---|---|
| GDATA e008 | e008 | same | command buttons 予定 訪問 能力 地図 スカウト システム 戻る 任務 会話 贈る | reuse game 1's redraw (gfx/e008.tsv) |
| GDATA e009 | e009 | same | status labels 信頼度 正義感 ストレス ... | reuse game 1 (it found e009 unused on screen; recheck) |
| GDATA e012-e014 | e012-e014 | same | status-screen backgrounds (fairy/angel/hero) | reuse game 1's redraw |
| GDATA e015 | e015 | same | name entry カタカナ ひらがな 英字 | reuse game 1's redraw |
| GDATA e142 | e142 | same | fairy panel ストレス 発見 索敵 移動中 待機中 行方不明 | reuse game 1's redraw |
| GDATA e143 | e143 | **changed** (new hero sprites) | status icons 失 死 (bottom row, same lettering) | re-apply game 1's e143 spec on the new image |
| GDATA e144 | e144 | same | フェイバリット・ディア kana on a patterned background | as game 1 decided (logo) |
| GDATA e145 | e145 | **changed** | save/load: この「Data」はこわれています 新規作成 空き容量がたりません 「Data」がありません | re-apply game 1's e145 spec (wording: 空き容量 here) |
| GDATA e203 | e203 | same | game-flow chart 全体のながれ | reuse game 1's redraw |
| GDATA e207 (+e243) | e207, e243 | same | battle status ポイズン チャーム スリープ コンフュ パライズ | reuse game 1's redraw (both copies) |
| GDATA e204-e206 | e204-e206 | same | 8x8 battle font (kana, Latin, digits) | game 1 drew battle names in code (`asm/btname.inc`) |
| GDATA sectors 40193, 40269, 40345 (no entry; in e382's span) | sectors 40127, 40203, 40279 | same | tutorial charts ゲームの流れ 其の一/二/三 | reuse game 1's redraw |
| GDATA e380 (sector 15294) and e383 | sectors 15228, 41039, 41115 | same | GAME OVER logo with ゲーム・オーバー kana | game 1 left it (no game-over screen reachable); same here unless the debug tool reaches one |
| PSX.EXE string 平和度 (text engine) | PSX.EXE 0x1747B4 | moved | map box "X: Y: 平和度" | text, not graphics: phase 4 extraction |
| TITLE/TTL_LOG0.PSS (uncompressed), NOWLOAD.TIM | (new) | new | **logo**: FAVORITE DEAR with the kanji subtitle 円環の物語 | **stays Japanese** (D5: no official English logo exists) |
| TITLE.PSS | TITLE.PSS | same | フェイバリット・ディア kana under the English logo | logo: stays (D5) |
| TITLE/TTL_OPT.PSS | same | same | memory-card notice | reuse game 1's redraw |
| TITLE/TTL_OPT2.PSS, TTL_INFO.PSS | same | same | Slime Ball instructions | reuse game 1's redraw |

Already English: title menu TITLE/TTL_COM.PSS (now uncompressed: Press Start Button / New Game / Load Game / Option /
Omake / Visual CG / Mini Event), STS_OPT2.PSS, OPM1.PSS, NOWLOAD.PSS "Now Loading...", EPI_OBJ.PSS, NEC logos.

New in this game, looked at, **no lettering**: GDATA e384 (15 new 640x240 event pictures, sectors 41333-42397) and
e385 (7 new 512x240 portraits, 42743-43139), e386-e387 (portraits), DATA/14.TIM (credits picture).

Open (look at with the debug tool's warps, phases 2/8): GDATA e151 (LZSS, changed) and e388-e394 (small non-TIM
entries, new); TITLE/TTL_LOG1.PSS (did not decode); graphics inside OMK.EXE's modes (Omake, Visual CG, Mini Event:
new menus, likely font-drawn text or new images); GOVER/FD_BALL/EPILOG/PS_MOV/FIN EXE-embedded graphics (game 1 left
these open too); FMVs are byte-identical to game 1's (game 1: no burned-in text in OP/DEMO/ENDING samples).
