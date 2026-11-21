# Glossary - Favorite Dear: Enkan no Monogatari

Binding for every translator and reviewer. Translators propose additions in reports; only the controller edits this
file. `tools/batches.py check` enforces the tables: a row whose JP holds a term (whole katakana run) must contain the
EN form (first word group before " ("), and never a spelling from the Avoid column.

Imported whole from game 1 (`../favorite-dear-en/glossary.md`, phase 6, 2026-11-22): this game re-uses game 1's
cast, places, items and voices, and a returning player reads both, so every game-1 spelling and rule is kept (D2,
D9). Terms new in this game are added to the tables below, marked "(FD:EnM)" in notes.

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics (D1, as game 1's D12): kept, hyphenated, on personal names: さん "-san", くん/君 "-kun", ちゃん
  "-chan", 様/さま "-sama", 殿/どの "-dono" ("Sievas-sama", "{name:0180}-sama", "Griffin-dono", "Nana-chan").
  The English title they replaced goes ("Lord Sievas" -> "Sievas-sama"). Titles that are words stay English:
  王子 Prince, 王女/姫 Princess, 卿 Lord ("Lord Busik"), 騎士 knight; address nouns stay English: 天使様/天使さん
  "Angel", 勇者様 "the hero", お父様 "Father". Common nouns + さん in a childlike voice: "Mister" ("the Mister Orcs",
  "Kind Mister Human"). Linted by `batches.py check` (`tools/honorifics.py`). Name order: Western.
- Romanisation source (D2): game 1's spellings below win; for new names, game 2's glossary
  (`../favorite-dear-junpaku-no-yogensha-en/glossary.md`), else as game 1 did (its D10): Western-style spellings of the katakana names, demon and
  angel names in their standard English forms (Apollyon, Gabriel, Belphegor).
- Credits: English.
- Register: warm fantasy drama, natural modern English, no archaisms except for the higher angels (formal, measured).
  Sound effects and interjections: English equivalents (うふふ "Hehe", ククク "Heh heh heh", えっ "Huh?").
- Abbreviations: full names and terms everywhere, prefer engine changes over shortening.

## Style rules
- Punctuation: 「」 -> "...", 『』 -> '...', ・・・ / ・・・・・・ -> "..." (one ellipsis, never more than "......"),
  ！？ -> "?!", （...） inner monologue -> (...). Plain ASCII plus … — ♥ ♪ é only.
- Choice lines keep the full-width layout: `　｛Go to them　｝` (full-width space, ｛ ｝, the option inside; pad both
  options of one choice to the same width with full-width spaces after the text).
- The player is the angel `{name:0080}`: keep every line about the angel gender-neutral (no he/she).
  天使様 -> "Angel" (capitalised as an address), voiced by the speaker ("Hey, Angel!").
- Common terms (not lint-enforced): 天使 angel; 勇者 hero (the angel's chosen champion); 妖精 fairy; 堕天使 fallen
  angel; 天界 the Heavens; 地上 the surface / the world below (set against Heaven, "stay on earth" / "come down to earth", no article);
  魔人 fiend (lower case mid-sentence); 魔物/怪物/モンスター monster; 災い calamity;
  魂 soul; 相性 compatibility (between heroes); 経験 experience; ボーナスＡＰ Bonus AP; 行方不明 missing;
  平和度 peace level ("Peace level down 10 points!"); 地獄の騎士 Knight of Hell (Regal's title; b058 "Knights of
  Hell"); 翼を持つ者 winged ones; 逆臣 traitor (逆臣ステレンス "the traitor Sterens").
- Voices: docs/style-reference.md.

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| レイヴ | Reiv | | hero, Reiv Vincelras, knight of the Voras order | Rave |
| ヴィンセルラス | Vincelras | | Reiv's family name | |
| シーヴァス | Sievas | | hero, Sievas Volkgang | |
| フォルクガング | Volkgang | | | |
| アーシェ | Ashe | | hero, Ashe Bradarik | |
| ブレイダリク | Bradarik | | | |
| ティア | Tia | | hero, Tia Tangeri | |
| ターンゲリ | Tangeri | | | |
| ビーシア | Beasia | | hero, Beasia Gray | |
| フィアナ | Fiana | | hero, Fiana Ecliya | |
| エクリーヤ | Ecliya | | | |
| ヤルル | Yaruru | | hero, Yaruru Willing | |
| ルドック | Ludock | | Ludock Willing | |
| ウィリング | Willing | | family name | |
| リュドラル | Ryudral | | hero, Ryudral Algrane; human raised among monsters, friend of the dragon chief Aul | |
| アルグレーン | Algrane | | | |
| フェリミ | Felimi | | hero, Felimi MacDill | |
| マクディル | MacDill | | | |
| ディアン | Dian | | hero, Dian Alvis | |
| アルヴィース | Alvis | | | |
| ナーサディア | Nasadia | | | |
| ナーサ | Nasa | | Nasadia's nickname (ナーサさん "Nasa-san") | |
| ナナ | Nana | | a child at Ellen's church (ナナちゃん "Nana-chan") | |
| グリフィン | Griffin | | | |
| ラスエル | Rasuel | | fallen angel; (FD:EnM) posed as Velk to corrupt Kane (e949) | |
| エレン | Ellen | | | |
| ミリアス | Milias | | | |
| アウル | Aul | | chief of the dragon clan (竜族の長) | Owl |
| シルフェ | Sylphe | | fairy | |
| シェリー | Shelly | | fairy | |
| フロリンダ | Florinda | | fairy | |
| ローザ | Rosa | | fairy (formal, composed) | |
| フロリン | Florin | | Florinda's name for herself | |
| ミライヤ | Miraya | | | |
| ガブリエル | Gabriel | | archangel | |
| ミカエル | Michael | | archangel; lends the angel his golden sword (黄金の剣) against Apollyon | |
| レミエル | Remiel | | angel who keeps wandering souls; レミエル様 "Remiel-sama" (D12) | Lady Remiel, Lord Remiel |
| ラミエル | Remiel | | JP typo for レミエル (3B0A soul-lost lines) | |
| リリィ | Lily | | | |
| アポルオン | Apollyon | | | |
| イウヴァート | Iuvart | | fallen angel | |
| アドラメレク | Adramelech | | | |
| ガープ | Gaap | | | |
| 勇者の発見 | Find Hero | | menu command (PSX.157A34) the fairies ask for when a hero goes missing | |
| トロメア | Ptolomea | | place of the fallen angels' exile (Dante); with ジュデッカ Judecca, リンボ Limbo | |
| ジュデッカ | Judecca | | | |
| リンボ | Limbo | | | |
| レライエ | Leraje | | | |
| ベルフェゴール | Belphegor | | | |
| ドラッケン | Drakken | | mountain bandit / monster preying on merchants in Hebron | |
| キメラ | Chimera | | monster in the Duminas marshes | |
| ケルピー | Kelpie | | water monster posing as a girl (Sievas event) | |
| マキュラ | Macula | | rogue dragon, マキュラドラゴン "Macula Dragon"; dealt with Iuvart | |
| ボルンガ | Borunga | | gentle Duminas monster (Ryudral event) | |
| トリシア | Tricia | | village chief's daughter below the Dragon's Den (Ryudral event) | |
| シエラ | Sierra | | witch serving Apollyon (Dian event) | |
| リーガル | Regal | | Reiv's old friend, the Knight in Black (黒衣の騎士) | |
| イダヴェル | Idavel | | (Griffin event) | |
| ビュシーク | Busik | | undead monster empowered by Apollyon | |
| バルバロッサ | Barbarossa | | bandit (Felimi event) | |
| ライザ | Liza | | Dian's lost love | |
| ジャックハウンド | Jackhound | | Rush's true name (sacred beast) | |
| ブロッケン | Brocken | | monster (Yaruru event) | |
| ゼビア | Zebia | | slaver bandit boss (Fiana event) | |
| バルト | Balt | | Apollyon's servant (Fiana event) | |
| ラッシュ | Rush | | Yaruru's sacred beast ("he") | |
| グレイ | Gray | | Beasia's family and her dojo ("the Gray-style dojo", グレイ流道場) | |
| ウォルフラム | Wolfram | | General Wolfram, Fangam royalist commander (Ashe event) | |
| ステレンス | Sterens | | usurper king of Fangam, empowered by Apollyon (Ashe event); "Sterens-sama" to his soldiers (D12) | |
| バーンズ | Barnes | | guardian beast of the fairy world, servant of Iuvart (Tia event); broken speech ("Me... beat you") | |
| ティタニア | Titania | | fairy queen (ティタニア様 "Titania-sama", D12) | |
| フェリス | Felice | | noblewoman Sievas jilts at a soiree (Sievas event) | |
| ユリアナ | Juliana | | (FD:EnM) new hero, Juliana Andrang, a Kanoa noble's daughter who travels | Yuliana |
| アンドラング | Andrang | | (FD:EnM) Juliana's family ("the Andrang family", アンドラング家; castle in Lumia) | |
| ケイン | Kane | | (FD:EnM) Juliana's older brother | Cain |
| ヴェルク | Velk | | (FD:EnM) name a fallen angel used to get close to Kane | |
| リディア | Lydia | | (FD:EnM) a hero's younger sister (e739) | |
| ビーストドラゴン | Beast Dragon | | (FD:EnM) dragon fought with Rush/Jackhound (e485) | |
| アウルドラゴン | Aul Dragon | | (FD:EnM) | |
| インキュバス | Incubus | | (FD:EnM) demon | |
| ジル | Gil | | (FD:EnM) Beowulf's former boss, Griffin's teacher (e954) | |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| インフォス | Infos | | the world the angel protects | |
| ヴォーラス | Voras | | Voras Knights (ヴォーラス騎士団) | |
| ラダール | Radal | | Lake Radal | |
| ヘブロン | Hebron | | Kingdom of Hebron (ヘブロン王国); capital Voras | |
| ヨースト | Joost | | town in Hebron (Sievas) | |
| キンバルト | Kimbalt | | Kingdom of Kimbalt | |
| エルバレー | Elvalley | | the Elvalley Road (エルバレー街道) in Kimbalt (Griffin mission) | |
| アンシェ | Anshe | | town in the Esparda Empire attacked by a demon; not アーシェ (Ashe) | |
| ニーセン | Niesen | | town in Kimbalt (Griffin) | |
| カノーア | Kanoa | | the Kanoa Nation (カノーア国) | |
| フェデコ | Fedeco | | town in Kanoa (Felimi) | |
| エスパルダ | Esparda | | the Esparda Empire (エスパルダ皇国) | |
| ブルン | Brun | | town in Esparda (Dian) | |
| クヴァール | Kvaal | | region/nation (Yaruru, Fiana, Tia) | |
| ガルフ | Garf | | town in Kvaal (Yaruru) | |
| デュミナス | Duminas | | the Duminas Empire (デュミナス帝国) | |
| ラルース | Larousse | | town in Duminas (Ryudral) | |
| タンブール | Tambour | | town in Kvaal (Fiana) | |
| ファンガム | Fangam | | Kingdom of Fangam (Ashe's home) | |
| グルーチ | Gruche | | capital of Fangam | |
| ノバ | Nova | | town in Kimbalt (Beasia) | |
| トラスト | Trust | | town in Kanoa (Nasadia) | |
| オムロン | Omron | | village in Kvaal (Tia) | |
| コパ | Copa | | village in Fangam (slime thefts) | |
| サルファ | Sulfa | | region near Hebron where a rebellion breaks out (Reiv mission) | |
| トリニテ | Trinite | | town linked to Niesen by a highway (Griffin mission) | |
| ティアズ | Tiaz | | town where "that kid" lives (Griffin mission) | |
| ソルダム | Soldam | | village attacked by bandits (Dian mission) | |
| オフランド | Offland | | the Offland Mountains, spring for the epidemic cure (Dian) | |
| レーゼル | Resel | | Mount Resel near Garf, the riddle Fiend (Yaruru) | |
| アルプ | Alp | | place in Kimbalt with frequent monsters (Yaruru mission) | |
| アーテム | Artem | | town in Kvaal attacked by Leraje (Yaruru mission) | |
| ボルサ | Borsa | | the Borsa Forest, home of winged monsters (Nasadia mission) | |
| バルバ | Barba | | Barba Island (バルバ島), where Reiv is held captive | |
| シュランク | Schrank | | the Schrank Forest, where Yaruru met Rush | |
| ルミーア | Lumia | | (FD:EnM) town in Kanoa, the Andrang castle | |
| ピスカートン | Piscarton | | (FD:EnM) town in Fangam, riot | |
| ケーレ | Kehle | | (FD:EnM) town in Kvaal, riot ("the rioters of Kehle") | |
| オレイユ | Oreille | | (FD:EnM) place with bandits ("the bandits of Oreille") | |
| ギオン | Gion | | (FD:EnM) town in Esparda, looting | |
| チリオ | Chirio | | (FD:EnM) town in Kanoa, monster rampage | |
| クルメナ | Krumena | | (FD:EnM) village a character was born in, burned down | |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 時の淀み | Stagnation of Time | | the calamity eroding Infos ("the Stagnation of Time") | |
| 神獣 | sacred beast | | Yaruru's companion | |
| 竜の使い | the Dragon's Messenger | | Ryudral's local title | |
| 建国祭 | Founding Festival | | Fangam's national festival (Ashe event) | |
| アストラル界 | the Astral Plane | | the inner world of a heart, where an angel can be attacked directly | |
| 竜の洞 | the Dragon's Den | | Aul's cave; only dragonkind may enter | |
| 闇馬車 | Dark Carriage | | slaver bandit ring, in quotes ("Dark Carriage") | |
| ダルク | Dalk | | currency ("1000 Dalk", Fiana's fee) | |
| 炎王 | Flame King | | Adramelech's title | |
| ガロンドランク | Gallon Drunk | | tavern where a dancer works (Griffin's mix-up) | |
| ベイオウルフ | Beowulf | | Griffin's band of noble thieves (義賊) | |
| 英霊祭 | Festival of Heroic Spirits | | Hebron festival with a soiree (Reiv event) | |
| ゾンビマチャント | Zombie Trader | | enemy (btname E185 plate "ZOMBIE TRADER"); the b030 speaker label uses the same name | Zombie Merchant |

## Decisions from earlier batches
- b001 3498.1550 (the gift-name list, one run of names indexed by the script): kept Japanese (`-`), phase 7 must
  find how the names are cut before it can be translated.
- b009-b013 files 34F2 34F5 34F8 34FC 3500 3504 3507 350A (about 300 rows, all of each file): codes parse but the
  text decodes as kana/kanji soup under the main table (a substitution, not a constant shift: most frequent code
  0x000E sits where 。 belongs; likely a per-scene glyph set), so `-`. Same pattern in parts of 393D, 3976-3986
  (b099, b103-b105). Phase 7: find the glyph table these files use, re-extract, re-batch, translate.
- (Replaced by D12, 2026-11-20: 様 after a name is now "-sama", e.g. "I found {name:0180}-sama!".) 天使様 stays
  "Angel".
- b020 3576.06BE-0834 (6 rows): glyph soup like 34F2 etc., `-`; phase 7 re-extract.
- b046 36FB (47 rows) and 36FD (10 rows, continues in b047): short `{fb:..}` rows of soup ending in a repeated
  `高決｡》｡`/`･》･` pattern (looks like a mission-result table under another glyph set), `-`; phase 7 re-extract.
- Gendered addresses for the angel in lines that play for either gender are neutralised: Griffin's
  ド派手姉ちゃん -> "Flashy", 娘/女 -> "that one"/"You sure can talk"; Dian's 天使さん -> "Angel"; 358B.2332
  (Yaruru's dream, お姉ちゃん) -> "you".
- 姉さん (Felimi to Miraya, his elder sister; 356C, 3570, 35F0, 35F4): "Sister" / "my sister".
- Yaruru's お姉ちゃん is its own branch: after the angel says お姉ちゃんでいいですよ (35BC, female angel), his rows
  switch from 天使様 to お姉ちゃん (twins in one file: 3802.057E/0C6A, 3994.282C/28C0). Every お姉ちゃん row to
  the angel is "Big Sis" (b028, b041, b068-b141). No お兄ちゃん twin exists for a male angel. お兄ちゃん/兄ちゃん
  to heroes (children to Reiv, 35E5, 37BF, 3A3C) stays "mister"; Tia to her brother (3A46-3A4A) "big brother".
- Stock battle lines: 魔人 "Fiend", 魔族 "Demon", `{name:0180}はXを倒した` "{name:0180} defeated X.",
  `退けた` "drove off X."; 天使の手先 "the angel's lackey"; 天使の勇者 "the angel's hero".
- PSX.EXE strings (trans/exe; in-place byte slots, but list entries (places, items, ranks, mission titles) that grow
  move to free space, up to 2 letters per cell of the list's widest Japanese entry: places 14, items 16, ranks 12,
  mission titles 16; `exetext.py check` enforces it): default angel name ラビエル "Raviel"; fairy
  commands 待機 "Stand By", 天界へ "To Heaven", 勇者と同行 "Join Hero", 休暇 "Vacation", 勇者の発見 "Find Hero",
  敵の探索 "Find Foe". Map names: 海 Sea, 森 Wood, 山脈 Range, 山地 Hills, 山 "Mt.X" (no space), 峡谷 Rift, 峠 Gap,
  島 Isle, 川 River, 湖 "Lake X", 砂漠 Sands, 氷原 Ice. Angel ranks: 天使見習い Apprentice, 幼翼 Novice,
  準翼/正翼/成翼 Junior Angel/Angel/Senior Angel, 翼宮 Court, 準X翼宮 "Jr. X" (12 letters: "Junior Prince" won't
  fit), choirs 能 Power, 権 Prince, 主 Lord, 座 Throne, 智 Cherub, 熾 Seraph, 大天使 Arch, 聖天使 Saint, 紫位 Violet,
  X天使長 "Chief X", 聖熾天使 Seraphim. Items: ピアス Earring, ブレス Bangle, ビュート Lash, ブレスト Cuirass.
  Mission titles: 盗賊・闇馬車 Dark Carriage, 魔物の罠 Monster's Trap, 教会襲撃 Church Raid. Quiz (new game) answers
  "1 ..."/"2 ...".

### This game (Enkan no Monogatari)
- Glyph-soup rows (notes "glyph soup in game 1") are left out of the batches and keep an empty `en`; any new soup
  a translator meets gets `-`. Phase 7 re-extracts them with their glyph table.
- New names (phase 6 terms pass, agent's call under D6, docs/decisions.md D10): German/European-style spellings
  matching game 1's map (Schrank, Kvaal, Joost): Juliana Andrang, Kane, Velk, Lydia, Lumia, Piscarton, Kehle,
  Oreille, Gion, Chirio, Krumena. リーダー as a speaker label "Leader"; ヒヨコ "chicks".
- b017 e817.2F1C (`{fc}`-framed run of mission titles with digit placeholders, 盗賊・闇馬車...ねらわれた花嫁): a
  data table, not a printed line, `-` like b001's gift list; phase 7: find how it is indexed (the EXE copies of the
  mission titles are translated in `script/exe.tsv`).
- Love-confession choices (e791-e802): game 1's options, padded with full-width spaces: "Promise to stay" /
  "Can't promise", 約束する "I promise", 地上には残らない "I won't stay", その約束はできない "Can't promise that".
- Walk-on speaker labels: 男１/男２ "Man 1:"/"Man 2:", 男たち "Men:" (e916). Choices there: 後を追う "Follow her",
  そっとしておく "Leave her be", 姿を現す "Show yourself", そのまま様子を見る "Keep watching".
- Juliana's arc (b026-b032): Velk is the fallen angel Rasuel in disguise (e949). Speaker labels: 手下 "Henchman:",
  首領 "Boss:", リーダー/リーダー格の男 "Leader:", 暴徒 "Rioter:", ラスエルの下僕 "Rasuel's Servant:", ケインの怪物
  "Monster Kane:", クマ "Bear:". 兄様 (Juliana to Kane) "Brother"; Ashe's バカ天使 "stupid angel" (as before).
  Fairy coordinates "Oreille (34, 22)". Choice rows without a leading 　 in the JP keep none.
- EXE/staff/card leftovers (end of phase 6): as game 1 (its D16, docs/jp_kept.tsv), the two packed label rows
  PSX.141F44/141F70, the name-entry grids PSX.184EA4/184F64 and the 8 memory-card titles (`script/sjis.tsv`) keep
  their Japanese for now: phase 7 decides them with the code that cuts or draws them. 男/女 (PSX.14F68C, 4-byte
  slots) are "Male"/"Female" pending a repoint. Staff roll: leading 　 -> 2 spaces each, capped at 28 letters; two
  names on one row "A|B"; a `%` prefix stays; six kanji readings are flagged "name reading unverified".
- Demo leftovers (e835.20EE "This version ends here!", e914.19DA "TGS version") are translated plainly like the dev
  rows; 天使Ñ様 there is "Angel {name:0080}-sama" (the honorific lint wants the suffix).
