-- freewatch.lua: is a RAM range really free? Logs the first write (frame, pc, address) to each candidate range.
--   python -X utf8 tools/debug/warp.py SCENE.. --debugger --lua tools/debug/freewatch.lua
-- Candidates: the PSX.EXE zero runs with no static reference (docs/re/space.md). A range with no FREEWATCH line after
-- a spread of scenes is a candidate for the font hook; one with a write is a run-time buffer.
local ranges = FREE_RANGES or {
  {0x80152628, 0x80153650},
  {0x80158150, 0x8015C2D0},
  {0x80187A80, 0x8018A9E0},
  {0x80192A6C, 0x80193D2C},
  {0x801956D0, 0x80197AD0},
}
for _, r in ipairs(ranges) do
  local done = false
  L.on_write(r[1], r[2] - 1, function(addr)
    if done then return end
    local pc = L.pc()
    -- BIOS/kernel (the EXE load itself) and _LOADE.EXE at 0x801C0000 (re-reads PSX.EXE sectors, pc 0x801C46B0)
    if pc < 0x80010000 or pc >= 0x801C0000 then return end
    done = true
    L.log(string.format("FREEWATCH f%d write %08X-%08X pc=%08X addr=%08X", L.frame, r[1], r[2], L.pc(), addr or 0))
  end)
end
L.log("FREEWATCH armed " .. #ranges)
