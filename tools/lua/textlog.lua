-- Text coverage log for tools/textcover_map.py (port of game 1's tools/lua/textlog.lua; addresses re-found with
-- tools/addrmap.py, docs/re/debug.md). Per frame, read the event printer's object (pointer at 0x80187458, game 1
-- 0x8001A4B8: 624 matching code sites; its stream is the pointer at obj+0 plus 2 * the u16 index at obj+0x10) and the
-- loaded-event table at 0x80148C6C (10 x 8 bytes: u16 event id, u16 halfword offset into the buffer 0x80148CBC).
-- Logs "SCR <slot> <id> <off>" when the table changes and "PIDX <index> <obj> f<frame>" when the printer index changes.
-- No --debugger needed. Usage: warp.py SCENE --lua tools/lua/textlog.lua
local mem = PCSX.getMemPtr()
local function u16(a) a = a & 0x1FFFFF; return (mem[a] & 0xFF) | ((mem[a + 1] & 0xFF) << 8) end
local function u32(a) return u16(a) | (u16(a + 2) << 16) end
local TABLE, BUF, OBJP = 0x80148C6C, 0x80148CBC, 0x80187458
local tab = {}
local last = {}
local lastobj
local printers = {}
L.on_frame(function()
  for s = 0, 9 do
    local e = TABLE + 8 * s
    local v = string.format("%d %d", u16(e), u16(e + 2))
    if tab[s] ~= v then
      tab[s] = v
      L.log(string.format("SCR %d %s", s, v))
    end
  end
  local obj = u32(OBJP)
  if DEBUG_OBJ then
    local s = string.format("OBJ %08X %04X%04X sub=%04X idx=%04X", obj & 0xFFFFFFFF, u16(obj + 2), u16(obj),
                            u16(obj + 8), u16(obj + 0x10))
    if s ~= lastobj then lastobj = s; L.log(s .. string.format(" f%d", L.frame)) end
  end
  -- 0x80187458 is the current task's object, so one sample per frame mostly sees other tasks (KAIWA1 run: 4 of ~30
  -- index changes). Every object seen there with a stream in the load buffer is remembered as a printer (0x80169118
  -- in week-1 events) and all of them are read every frame.
  local hi = u16(OBJP + 2)  -- LuaJIT bit ops are signed 32-bit: range-check the high half
  if hi >= 0x8000 and hi < 0x8020 then
    local b = u16(obj) + u16(obj + 2) * 65536
    if b >= BUF and b < 0x8014FCC0 and not printers[obj] then
      printers[obj] = true
      L.log(string.format("PRINTER %X f%d", obj, L.frame))
    end
  end
  for p in pairs(printers) do
    -- the printer reads code = u16 at [obj+0] + 2 * u16(obj+0x10) (obj+8 set: a sub-stream at [obj+4] + 2 *
    -- u16(obj+0xA), the name/insert strings, not logged). [obj+0] is the message start (KAIWA1: 0x80149932). Log the
    -- halfword index into the load buffer (which ends at 0x8014FCBE, docs/re/text.md).
    if u16(p + 8) == 0 then
      local base = u16(p) + u16(p + 2) * 65536  -- arithmetic, not <<: keeps it unsigned
      local idx = (base - BUF) / 2 + u16(p + 0x10)
      if base >= BUF and base < 0x8014FCC0 and idx ~= last[p] then
        last[p] = idx
        L.log(string.format("PIDX %d %X f%d", idx, p, L.frame))
      end
    end
  end
end)
