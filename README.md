# Favorite Dear: Enkan no Monogatari English translation

Unofficial English fan translation of **Favorite Dear: Enkan no Monogatari** (PlayStation, NEC Interchannel, 2001;
the expanded re-release of Favorite Dear): the source text and tools that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## How it differs from Favorite Dear (1998)

Enkan no Monogatari is the original Favorite Dear re-released with more content, on the same engine. The premise, the
twelve heroes and most scenes are the original's (about half of the event text is word for word the same), so this
translation builds on the [Favorite Dear translation](https://github.com/minhnhattonthat/favorite-dear-en). New here:

- **A thirteenth hero, Juliana Andrang**: a noble searching for her missing older brother, Kane, with her own story
  arc, missions, confession, battle lines and epilogues.
- **More scenes for the original heroes**: visits and greetings, talk and training topics, extra love confessions,
  Q&A scenes, boss-fight and rematch lines, more mission reports and endings, plus smaller new episodes (Beasia's
  bear cave, Griffin's home village, Reiv's rescue from Barba Island and others).
- **Changes to the story's villains**: the fallen angel Rasuel plays a new role, with new rematches against the
  fallen angels.
- **An Omake (bonus) mode** with **Visual CG** (an event-picture gallery) and **Mini Event** (12 short extra scenes).
- **A new title screen** with the Enkan no Monogatari (円環の物語) subtitle and the extra menu entries.

The opening, demo and ending movies are the same as the original's.

For modders: the Omake mode is a second copy of the main program (`OMK.EXE`), so every program string exists twice;
the font encoding, the data directory format and all addresses differ from the 1998 disc. Details in
[`docs/re/disc.md`](docs/re/disc.md) and [`docs/re/text.md`](docs/re/text.md); the story summary is
[`docs/synopsis.md`](docs/synopsis.md) (contains spoilers).

## Translation status

| Part | Status |
|---|---|
| Dialogue and story, battle text, endings, Juliana's arc | Translated |
| Menus, items, places, skills, system messages | Translated |
| Omake menu (Visual CG, Mini Event scenes) | Translated |
| Graphics with text (menus, labels, tutorial charts, battle plates) | Translated |
| Title logo | Kept as released (FAVORITE DEAR with the Japanese subtitle; no official English logo exists) |
| Name entry | English letter page by default; the kana pages are kept |
| Staff credits | Translated (names romanized) |
| Voice acting, songs | Left in Japanese (audio) |
| Memory-card titles (console memory-card manager) | Left in Japanese |

Base disc: `Favorite Dear - Enkan no Monogatari (Japan).bin` (Redump, SLPS-03286), 639219504 bytes, CRC32 8C4F696F,
MD5 18d564e3ce5f5b9b006ead6be11a290c, SHA-1 605d9dd7d6d6bf985d64f307540b431459797d35. Tested in PCSX-Redux; start
from a cold boot, not a savestate made with the Japanese game.

Known issues: see [Issues](../../issues).

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.codex/agents/`, `.opencode/agents/` | Subagent types (translator, reviewer, visual QA, playtester, graphics) for Codex and opencode; Claude Code gets them from the plugin. |

## Build your own patched disc

Needs Python 3.12+ and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/favorite-dear-enkan-no-monogatari-en
cd favorite-dear-enkan-no-monogatari-en
# copy your dump to: rom/Favorite Dear - Enkan no Monogatari (Japan).bin and .cue
#   (639219504 bytes, SHA-1 605d9dd7d6d6bf985d64f307540b431459797d35; the build refuses any other dump, see rom.sha1)
python -X utf8 tools/build.py                          # -> build/fd3_en.bin/.cue
python -X utf8 tools/check.py                          # tests + text lint
```

## Thanks

v1.1 and v1.2 fix bugs that players found in the [Favorite Dear translation](https://github.com/minhnhattonthat/favorite-dear-en)
(same engine): thanks to ahassmoto-boop and Centurionzo12 for reporting them.

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is NEC Interchannel's and is included only
so the translation can be checked against it. Favorite Dear: Enkan no Monogatari is (c) NEC Interchannel; this project
is not affiliated with them. Do not share patched disc images.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
