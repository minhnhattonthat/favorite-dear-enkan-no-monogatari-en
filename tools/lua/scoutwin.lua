-- scoutwin.lua: make every hero scout succeed (for building hero stress saves without a grind). Debug only.
-- Game 1's (../favorite-dear-en/tools/lua/scoutwin.lua). Scout scripts test the join with
-- `006D 0016 8002 0001 <yes> <no>` and run `0093 0001` (join) on the yes branch; every 10 frames this rewrites
-- <no> to <yes> in the loaded-script buffer (RAM 0x80148CBC here, game 1 0x8016C608; up to 0x7000 bytes,
-- docs/re/debug.md).
local ffi = require("ffi")
local h = ffi.cast("uint16_t*", PCSX.getMemPtr())
local BASE = (0x80148CBC - 0x80000000) / 2
local N = 0x7000 / 2
L.on_frame(function(n)
  if n % 10 ~= 0 then return end
  for i = BASE, BASE + N - 6 do
    if h[i] == 0x006D and h[i + 1] == 0x0016 and h[i + 2] == 0x8002 and h[i + 3] == 0x0001
        and h[i + 5] ~= h[i + 4] then
      h[i + 5] = h[i + 4]
      print(string.format("SCOUTWIN f%d at 0x%08X", n, 0x80000000 + i * 2))
    end
  end
end)
