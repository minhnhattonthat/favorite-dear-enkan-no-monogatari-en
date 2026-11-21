-- herosel.lua (debug only): show a hero's status screen from a card without heroes (asm/skill.inc check).
-- From frame FROM (default 8700) the selected-character byte 0x801942E9 (s8; heroes 0-12, renderer 0x800E9EF4)
-- is forced to HERO every frame, so the status screen opened by the hub_ability4 route renders that hero.
-- LONG=1 also points every hero's three skills at the three longest English names (u16 halfword offsets from
-- 0x801517C8 in the table 0x8019AE84, 3 per hero): Double Boomerang (16 letters), Tempest Hearts, Megaton Hammer.
--   python -X utf8 tools/debug/warp.py hub_ability4 --cue C:/.../build/fd3_en.cue --root work/qa/p8/skill \
--       --lua C:/.../tools/debug/herosel.lua --var HERO=1 [--var LONG=1] --name ...
local ffi = require("ffi")
local m8 = ffi.cast("int8_t *", PCSX.getMemPtr())
local m16 = ffi.cast("uint16_t *", PCSX.getMemPtr())
local hero = HERO or 0
local from = FROM or 8700
local LONG_VALS = { 125, 296, 287 }
L.on_frame(function()
  if L.frame < from then return end
  m8[0x1942E9] = hero
  if LONG and LONG_VALS then
    for h = 0, 12 do
      for k = 0, 2 do m16[(0x19AE84 + h * 6 + k * 2) / 2] = LONG_VALS[k + 1] end
    end
  end
end)
