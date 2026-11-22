# Polish list

Minor review findings, fixed in one pass before release. Tick each `[x]` with `fixed` or `waived: reason`; the release
script refuses to run while any line is unticked.

- [x] e819.15B0 - "The hero's gone missing." / "the hero will come back": the JP box has no name; check in game what precedes it and whether "The hero" reads as redundant - fixed: second box "I think they'll come back after a while" (2026-11-22)
- [x] e833.1A54 - "Fearing Miraya, who attacks her land" -> "her own land" (自国を襲う) - fixed: "who attacks her own country"
- [x] e840.0532 - Ashe's そんな・・・ answering Milias's thanks is "But..."; "Oh, please..." reads better - fixed
- [x] e911.026E - "<name>:Um..." lacks the space after the colon the other lines have (JP lacks it too; check in game) - fixed 2026-11-22 (story pass): the waiver was wrong: the raw row is `{name}:{f7:0380}Um...` with no `{n}` ({f7} is a colour code, as in `Rush: {f7:E783}...`), so the text follows the label on the same line; all 87 such labels in 41 rows got the space (lint 0)
- [x] e958.32B2 - Ryudral's くすぐったい "it tickles" -> "you're making me squirm"; e963.32C0 "all tingly" -> "a little bashful" - fixed both
- [x] e746.0F58 - "if it isn't my Angel" -> "if it isn't the Angel" (JP plain 天使様) - fixed, also e746.10DA, e929.0F58, e929.10DA
- [x] e892.0268 - "since I left" drops 人間界から: "since I left the human world" (also e912.0268) - fixed as "Years have passed since I left Infos." (fits the line) in all 13 epilogue openers e889-e900, e912
- [x] FIN.278 - staff-roll name readings unverified (notes say so): 祐川 龍二 "Ryuji Sukegawa", FIN.322 真弓 貴 "Takashi Mayumi", FIN.329 樫原 修実 "Osami Kashihara", FIN.345 宮崎 暁 "Akira Miyazaki", FIN.346 大味 健一郎 "Kenichiro Omi", FIN.423 本多 柚々 "Yuyu Honda"; check a credits database (MobyGames, VGMdb) or keep with the flag - waived: kept with the flag (the most common readings; the row notes say unverified); a player correction can land as an issue
- [x] e747.0796 - line ends dangling (check the follow-on row in game; e767 has the same shape) - fixed: "I'm on a journey at the moment... You came all the way out here. Is your business urgent?"
- [x] e792.05DE - "You held me up..." is literal; smoother: "Sorry to keep you waiting..." - fixed as "...It was you who kept me going all this way..." (JP 君にささえられてここまでやってこれた; the suggested EN was wrong)
- [x] e800.032E - Beasia's casual register drifts neutral here; give her a rougher line like the rest of her arc - waived: re-read in full: "Yeah, of course...", "I finally get why", "tearing me up", "I'm going to lose it" already carry her オレ voice
- [x] e875.0498 - phrasing is a calque of the JP; reword idiomatically - fixed: これからもよろしく "Please take care of me from now on." -> "So please, keep me by your side."
- [x] e924.1A9C - 私でよければ聞きますよ is "I'll listen, if I can help", not the stock "if you'll have me" - fixed: "I'll hear you out, if it helps." (same length, choice-menu padding kept)
- [x] e924.31DA - "take my rest without holding back" stiff -> "rest up properly" - fixed: "Then I'll take you up on it and rest."
- [x] e947.0FCC - "Kane:Silence!" lacks the space after the colon (check JP/in game) - fixed with e911.026E
- [x] e468.11AE - "Girl:Everyone" lacks the space after the colon (check JP/in game) - fixed with e911.026E
- [x] e915.05FA - "stay on the surface" -> "stay on earth" (地上) - fixed
- [x] e923.07CA - "if it isn't the angel" -> "the Angel" (capitalised as an address) - fixed, also e923.0A58, e930.07CA, e930.0A58
- [x] hero status Name: "Juliana ・Andrang" shows a gap before the dot (odd-length given name: the pair glyph's empty right half, `work/qa/p8/skill/long`); same for any 7-letter given name (Griffin?): consider a name row with the dot packed in ("Juliana・") if the slot allows - waived: cosmetic half-cell gap from the pair-glyph font (game 1 ships the same for odd-length names); packing needs a name-row layout change for every hero, not worth the risk at release
