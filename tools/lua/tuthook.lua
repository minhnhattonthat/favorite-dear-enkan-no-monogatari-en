-- tuthook.lua: the opening's tutorial state machine (PSX.EXE handlers 0x800DFD48..0x800E1484 at task obj+0x44).
-- Handler 0x800E0C9C ends its lines with the choice "1. Start now. 2. See the overall flow." (PSX.132FEC, message
-- table 0x80145CBC entry 8), then 0x800E0E30 runs the choice: cursor u16 0x80194944 (0/1; pad word 0x80161624:
-- 0x1000 up, 0x4000 down, 0x20 circle). Choice 2 shows the e203 game-flow chart.
-- Logs "TUT <handler> f<frame>" when the current task's handler in 0x800DF000-0x800E2000 changes.
-- --var FLOW=1 holds the cursor on choice 2 while 0x800E0E30 runs, so warp.lua's mash picks it.
-- Usage: warp.py week1 --lua tools/lua/tuthook.lua --var FLOW=1 --shot-every 30   (choice at ~f10142)
local mem = PCSX.getMemPtr()
local function u16(a) a = a & 0x1FFFFF; return (mem[a] & 0xFF) | ((mem[a + 1] & 0xFF) << 8) end
local function u32(a) return u16(a) + u16(a + 2) * 65536 end
local OBJP, CURSOR = 0x80187458, 0x80194944
local last, left_choice, choice_at
L.on_frame(function()
  local hi = u16(OBJP + 2)
  if hi < 0x8000 or hi >= 0x8020 then return end
  local obj = u32(OBJP)
  local h = u32(obj + 0x44)
  if h >= 0x800DF000 and h < 0x800E2000 and h ~= last then
    if last == 0x800E0E30 then left_choice = true end  -- poke the first choice only (later prompts share CURSOR)
    last = h
    L.log(string.format("TUT %08X f%d", h, L.frame))
  end
  if FLOW and last == 0x800E0E30 and not choice_at then choice_at = L.frame end
  -- poke until warp.lua's next circle (every 20 frames) has picked it: the chart viewer and later prompts share CURSOR
  if FLOW and choice_at and L.frame - choice_at < 25 and not left_choice then
    mem[CURSOR & 0x1FFFFF] = 1; mem[(CURSOR + 1) & 0x1FFFFF] = 0
  end
end)
