-- giveitems.lua: fill the angel's item bag (debug only) so the hero-visit GIFT screen has something to list.
--   emu.py CUE --state-in S --lua tools/lua/giveitems.lua [--var "ITEMS='0x01,0x20,0x40'"] [--var ITEMS_AT=N]
-- Game 1's (../favorite-dear-en/tools/lua/giveitems.lua). Bag: u8 count at 0x801940C4, u8 item codes from
-- 0x801940C5 (game 1 0x80026FAC; tools/addrmap.py, 10 of 23 game-1 sites agree).
local ffi = require("ffi")
local mem = ffi.cast("uint8_t*", PCSX.getMemPtr())
local codes = {}
for c in string.gmatch(ITEMS or "0x01,0x02,0x20,0x40,0x60,0x80", "0x%x+") do codes[#codes + 1] = tonumber(c) end
L.on_frame(function(n)
  if n ~= (ITEMS_AT or 2) then return end
  mem[0x1940C4] = #codes
  for i, c in ipairs(codes) do mem[0x1940C4 + i] = c end
  L.log("giveitems: " .. #codes .. " items")
end)
