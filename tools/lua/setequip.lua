-- setequip.lua: hold every hero's three equipment slots (debug only), for the hero status screen's Equip box.
--   warp.py hub_ability4 --cue C:/.../build/fd3_en.cue --lua tools/debug/herosel.lua --var HERO=1 \
--       --lua tools/lua/setequip.lua [--var "EQUIP='17,185,47'"]
-- Game 1's (../favorite-dear-en/tools/lua/setequip.lua). Hero records: 0x8018C680 + 0x6C * hero (heroes 0..12;
-- game 1 0x8001F6E4), u16 item codes at +0x2A/+0x2C/+0x2E (0xFFFF = empty), read by 0x800DD3FC (stat bonus) and
-- 0x800E9C50 (Equip box names). Defaults are the widest English names in the caps font (tests/test_equip.py):
-- 17 Battle Boomerang (74 px), 185 Power Boomerang (72 px), 47 Lamellar Armor (68 px).
local ffi = require("ffi")
local mem = ffi.cast("uint16_t*", PCSX.getMemPtr())
local codes = {}
for c in string.gmatch(EQUIP or "17,185,47", "%d+") do codes[#codes + 1] = tonumber(c) end
L.on_frame(function(n)
  if n < (EQUIP_FROM or 4000) then return end
  for hero = 0, 12 do
    for slot = 1, 3 do
      mem[(0x18C680 + 0x6C * hero + 0x28 + 2 * slot) / 2] = codes[slot] or 0xFFFF
    end
  end
end)
