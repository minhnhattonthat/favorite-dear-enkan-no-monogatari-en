-- Forced text viewer for text coverage (tools/textforce.py drives it). Port of game 1's tools/lua/textforce.lua
-- (../favorite-dear-en), addresses re-found here (docs/re/debug.md §Text coverage).
-- Rides on `warp.py --event eNNN` (warp.lua points event id 32's hash at the target, so id 32 loads its file). Each
-- time an event printer moves into a row of that file that is not the row it is printing, the hook moves its index
-- to the next row still to show (TARGETS), so the scene's own print ops play every message of the file in turn
-- while warp.lua mashes through the pages.
--   TARGETS  "<start hw>,<end hw>,<want 0|1|2> ..." per row of the file, space-separated (halfword offsets from the
--            file start, in order; end = next row's start or the file end; 2 = an unshown choice menu).
-- Printers: game 1 had one printer pointer (0x8001A4B8); here 0x80187458 is the current task's object, so (as in
-- tools/lua/textlog.lua) every object seen there with its stream [obj+0] in the load buffer is remembered and all
-- are read each frame; only a printer whose index changed this frame is acted on (a finished task's object keeps a
-- stale index and must not be written).
-- Logs like textlog.lua ("SCR", "PIDX"), so `textcover_map.py convert` maps the run; PIDX is logged only for
-- indexes the printer reached itself, never for the one the hook wrote. Also "FORCE <row> f<frame>" per redirect,
-- "SHOWN <row>" once the printer moved past a wanted row's first code, "FORCE done" (then the run ends) when no
-- wanted row is left.
-- Options (globals, --var): SKIPKEY ADOPT KEYPATCH PRINTPATCH RECHOICE NOBATTLE STARTPATCH FORCECHOICE ENTRYGO
-- EG_ID SIG FORCE_ID, as in game 1 (tools/textforce.py docstring). KEYFORCE/JUMPFORCE (debugger hooks) not ported.
local mem = PCSX.getMemPtr()
local function u16(a) a = a & 0x1FFFFF; return (mem[a] & 0xFF) | ((mem[a + 1] & 0xFF) << 8) end
local function u32(a) return u16(a) + u16(a + 2) * 65536 end
local function w16(a, v) a = a & 0x1FFFFF; mem[a] = v % 256; mem[a + 1] = math.floor(v / 256) % 256 end

local BUF, BUFEND = 0x80148CBC, 0x8014FCC0   -- game 1 0x8016C608
local TABLE = 0x80148C6C                     -- loaded-event table, 10 x 8 bytes (game 1 0x8016C5B8)
local OBJP = 0x80187458                      -- current task's object (game 1's printer pointer 0x8001A4B8)
local ID = FORCE_ID or 32  -- the event id warp.lua renames (its local SLOT)
local rows = {}
for s, e, w in TARGETS:gmatch("(%d+),(%d+),(%d)") do
  -- w = 2: an unshown choice menu (｛..｝): never a redirect target, but when the scene's own print op moves the
  -- printer into it, the hook leaves it alone so the menu draws and PIDX logs it
  -- FORCECHOICE: choice rows are ordinary targets too (KEYPATCH points the 0x90 lookups at them: SMEN answers)
  rows[#rows + 1] = {s = tonumber(s), e = tonumber(e), want = w == "1" or (FORCECHOICE and w == "2"),
                     choice = w == "2" and not FORCECHOICE}
end
local left = 0
for _, r in ipairs(rows) do if r.want then left = left + 1 end end
L.log(string.format("FORCE rows %d wanted %d", #rows, left))

local function row_of(rel)
  for i, r in ipairs(rows) do if rel >= r.s and rel < r.e then return i end end
  return nil
end
local function next_want(from)  -- `from` itself first: a target the script abandoned before printing it
  for k = 0, #rows - 1 do
    local i = (from - 1 + k) % #rows + 1
    if rows[i].want then return i end
  end
  return nil
end

local tab, last, cur, written, done_at = {}, {}, nil, nil, nil
local chainp, pendq, saveq = nil, nil, nil  -- patched terminator / patched clear before a chained row (buffer hw idx)
local function rd(i) return u16(BUF + 2 * i) end
local function wr(i, v) w16(BUF + 2 * i, v) end

-- when another wanted row is left, turn row t's terminating 0xFFFF (searched from buffer index s) into {wait}
-- (0xFFF3) so the printer stops there instead of ending the message; the frame handler then chains to the next row
local function arm(hoff, t, s)
  for k, r in ipairs(rows) do
    if r.want and k ~= t then
      for p = s, hoff + rows[t].e - 1 do
        if rd(p) == 0xFFFF then chainp = p; wr(p, 0xFFF3); break end
      end
      return
    end
  end
end

local tries = {}
local function start(obj, hoff, t, clear, n)
  -- a row the printer never moves into (a choice menu drawn by its own op, a table) gets 2 tries, then is skipped
  tries[t] = (tries[t] or 0) + 1
  if tries[t] > 2 then
    rows[t].want = false; left = left - 1
    L.log(string.format("SKIP %d f%d", t, n))
    local u = next_want(t)
    if not u then L.log(string.format("FORCE done f%d", n)); done_at = n + 600; return nil end
    t = u
    tries[t] = (tries[t] or 0) + 1
  end
  cur = t
  local s = hoff + rows[t].s
  -- a row opening with its FFFB key (op 0x90 looks messages up by it and starts the printer after it): start there
  if SKIPKEY and rd(s) == 0xFFFB then s = s + 2 end
  local at = s
  if clear then
    pendq, saveq = s - 1, rd(s - 1)
    wr(s - 1, 0xFFF2)
    at = s - 1
  end
  local nb = BUF + 2 * at
  w16(obj, nb % 65536); w16(obj + 2, math.floor(nb / 65536)); w16(obj + 0x10, 0)
  written = at
  arm(hoff, t, s)
  L.log(string.format("FORCE %d f%d%s", t, n, chainp and " chain" or ""))
  return at
end

-- the next wanted row (from `cur`) that opens with its FFFB key, and that key: what a patched 0x90 should print
local function keyed_target(hoff, cpc)
  for k = 0, #rows - 1 do
    local t = ((cur or 1) - 1 + k) % #rows + 1
    if rows[t].want and rows[t].s >= cpc and rd(hoff + rows[t].s) == 0xFFFB then
      return t, rd(hoff + rows[t].s + 1) & 0x7FFF
    end
  end
  return nil
end
-- KEYPATCH: files that print through `0x90 <value> <table>` (a message picked by its FFFB key) print nothing when
-- the cold-boot value matches no key. The first frame the file is in the buffer, patch every
-- `0090 <value> <ref to a row opening with FFFB>` outside the message rows to print the next wanted keyed row.
local inrow = {}
for _, r in ipairs(rows) do for p = r.s, r.e - 1 do inrow[p] = true end end
local rowstart = {}
for i, r in ipairs(rows) do rowstart[r.s] = i end
local patched_at = nil
local startpatch  -- defined below
local sp_entry = nil
local kp_why = nil
local function sig_ok(hoff)
  if not SIG then return true end
  for pos, v in SIG:gmatch("(%d+):(%d+)") do
    if rd(hoff + tonumber(pos)) ~= tonumber(v) then return false end
  end
  return true
end
local function keypatch(hoff, n)
  local cpc = math.floor(rd(hoff + 2) / 2)
  local t, key = keyed_target(hoff, cpc)
  -- loaded = header u16 6, a sane code offset, the last row's sector in, and the file's own code words (SIG)
  local loaded = rd(hoff) == 6 and cpc <= rows[1].s and rd(hoff + rows[#rows].s) ~= 0 and sig_ok(hoff)
  if not loaded or (not t and not STARTPATCH and not PRINTPATCH) then
    local why = string.format("KEYPATCH wait hdr %X code %X target %s", rd(hoff), cpc, tostring(t))
    if why ~= kp_why then kp_why = why; L.log(why .. string.format(" f%d", n)) end
    return
  end
  patched_at = hoff
  if NOBATTLE then
    -- story events: their battle (op 0xD3/0xE3 <stage> <ref>) ends at once in a warp, and the result checks after
    -- it (`002B/002C <a> <b> <ref to an 0037 end>`) then end the event before its text: make them gotos to the
    -- next op (`0028 <ref>`; the leftover args are jumped over). Also gotos to an end block (`00BF 00C0 0037`).
    local cnt = 0
    local function is_end(ref)
      local q = cpc + (ref & 0x7FFF)
      while rd(hoff + q) == 0xBF or rd(hoff + q) == 0xC0 do q = q + 1 end
      return rd(hoff + q) == 0x37
    end
    for p = cpc, rows[1].s - 4 do
      local op = rd(hoff + p)
      if not inrow[p] and (op == 0xD3 or op == 0xE3) and (rd(hoff + p + 2) & 0xFF00) == 0x8000 then
        wr(hoff + p, 0x28); wr(hoff + p + 1, 0x8000 | (p + 3 - cpc)); cnt = cnt + 1
      elseif not inrow[p] and (op == 0x2B or op == 0x2C) and rd(hoff + p + 3) >= 0x8000
          and is_end(rd(hoff + p + 3)) then
        wr(hoff + p, 0x28); wr(hoff + p + 1, 0x8000 | (p + 4 - cpc)); cnt = cnt + 1
      elseif not inrow[p] and op == 0x28 and p > cpc + 1 and rd(hoff + p + 1) >= 0x8000
          and is_end(rd(hoff + p + 1)) then
        wr(hoff + p + 1, 0x8000 | (p + 2 - cpc)); cnt = cnt + 1
      end
    end
    L.log(string.format("NOBATTLE sites %d f%d", cnt, n))
  end
  if PRINTPATCH then
    -- a row behind a script branch the cold boot never takes: point every plain print `003C <ref to a row start>`
    -- outside the rows at the first wanted row
    local w
    for i, r in ipairs(rows) do if r.want and r.s >= cpc then w = i; break end end
    local cnt = 0
    -- code can sit between a message's 0xFFFF and the next message: measure the real message here
    local inmsg = {}
    for _, r in ipairs(rows) do
      for p = r.s, r.e - 1 do inmsg[p] = true; if rd(hoff + p) == 0xFFFF then break end end
    end
    -- a conditional jump (0x2B-0x2F <a> <b> <ref>) to a print of a wanted row becomes a goto there
    for p = cpc, rows[1].s - 4 do
      local op, a = rd(hoff + p), rd(hoff + p + 3)
      if not inmsg[p] and op >= 0x2B and op <= 0x2F and a >= 0x8000 then
        local q = (a & 0x7FFF) + cpc
        local b = rd(hoff + q + 1)
        local r = rd(hoff + q) == 0x3C and b >= 0x8000 and rowstart[(b & 0x7FFF) + cpc]
        if r and rows[r].want then
          wr(hoff + p, 0x28); wr(hoff + p + 1, a); cnt = cnt + 1
          L.log(string.format("PRINTPATCH take %X -> %X (row %d) f%d", p - cpc, q - cpc, r, n))
        end
      end
    end
    for p = cpc, (w and rows[#rows].e - 2 or cpc - 1) do
      local a = rd(hoff + p + 1)
      if not inmsg[p] and rd(hoff + p) == 0x3C and a >= 0x8000 and rowstart[(a & 0x7FFF) + cpc]
          and rowstart[(a & 0x7FFF) + cpc] ~= w then
        wr(hoff + p + 1, 0x8000 | (rows[w].s - cpc)); cnt = cnt + 1
      end
    end
    L.log(string.format("PRINTPATCH %s sites %d f%d", tostring(w), cnt, n))
    if cnt > 0 and not t then return end  -- keyed rows too: the 0x90 sites below
  end
  if not t and not STARTPATCH then return end
  if not t then startpatch(hoff, n); return end
  local cnt = 0
  for p = cpc, rows[#rows].e - 3 do
    if not inrow[p] and rd(hoff + p) == 0x90 then
      local a2 = rd(hoff + p + 2)
      local tgt = (a2 & 0x7FFF) + cpc
      if a2 >= 0x8000 and rowstart[tgt] and rd(hoff + tgt) == 0xFFFB then
        wr(hoff + p + 1, key); wr(hoff + p + 2, 0x8000 | (rows[t].s - cpc)); cnt = cnt + 1
      end
    end
  end
  L.log(string.format("KEYPATCH %d key %X sites %d f%d", t, key, cnt, n))
  if cnt == 0 and STARTPATCH then startpatch(hoff, n) end
end

-- STARTPATCH (untested here): replace the file's entry with `00BA; 003C <first wanted row>; 00B9; 0037` (open,
-- print, close, end) and move the VM task there (obj+0x12 = pc, obj+0x16 = call depth, as in game 1).
startpatch = function(hoff, n)
  local cpc = math.floor(rd(hoff + 2) / 2)
  local c = hoff + cpc
  local entry = rd(c) == 0x28 and (rd(c + 1) & 0x7FFF) or 0
  for t, r in ipairs(rows) do
    if r.want and r.s >= cpc then
      local seq = {0x00BA, 0x003C, 0x8000 | (r.s - cpc), 0x00B9, 0x0037}
      for k, v in ipairs(seq) do wr(c + entry + k - 1, v) end
      sp_entry = entry
      L.log(string.format("STARTPATCH %d at pc %X f%d", t, entry, n))
      return
    end
  end
end

-- ENTRYGO "<at>:<to>": the first frame the file's code words are in the buffer (SIG), write `0028 <ref to>` (goto)
-- at code pc <at>. "<at>:c<pc>" takes <to> from the ref of the conditional jump `002B a b <ref>` at code pc <pc>.
local function entrygo(hoff, n)
  if rd(hoff) ~= 6 then return end
  local cpc = math.floor(rd(hoff + 2) / 2)
  local at0 = tonumber(ENTRYGO:match("^(%w+)"))
  if rd(hoff + cpc + at0) == 0x28 then return end  -- patched already
  if not sig_ok(hoff) then return end
  local at, c, to = ENTRYGO:match("(%w+):(c?)(%w+)")
  at, to = tonumber(at), tonumber(to)
  if c == "c" then to = rd(hoff + cpc + to + 3) & 0x7FFF end
  wr(hoff + cpc + at, 0x28); wr(hoff + cpc + at + 1, 0x8000 | to)
  L.log(string.format("ENTRYGO pc %X -> %X f%d", at, to, n))
end

local printers = {}
local function handle(obj, hoff, n)
  local base = u32(obj)
  if u16(obj + 8) ~= 0 or base < BUF or base >= BUFEND then return end  -- name/insert sub-stream, or not ours
  local idx = (base - BUF) / 2 + u16(obj + 0x10)
  if idx == last[obj] then return end
  local fileidx = hoff and idx >= hoff and idx < hoff + rows[#rows].e
  if fileidx and not done_at then
    if pendq and idx > pendq then wr(pendq, saveq); pendq = nil end
    local rel = idx - hoff
    if cur and rows[cur].want and rel > rows[cur].s and rel < rows[cur].e then
      rows[cur].want = false; left = left - 1
      L.log(string.format("SHOWN %d f%d", cur, n))
    end
    if chainp then
      if idx == chainp or idx == chainp + 1 then  -- at the {wait} that replaced the terminator: chain
        wr(chainp, 0xFFFF); chainp = nil
        local t = next_want(cur)
        if t then idx = start(obj, hoff, t, true, n) or idx; rel = idx - hoff end
      elseif idx < hoff + rows[cur].s - 1 or idx > chainp + 1 then  -- the script moved the printer elsewhere
        L.log(string.format("UNCHAIN %d at %d idx %d f%d", cur, chainp, idx, n))
        wr(chainp, 0xFFFF); chainp = nil
      end
    end
    local i = row_of(rel)
    if i and rows[i].choice and i ~= cur then
      rows[i].choice = false
      L.log(string.format("CHOICE %d f%d", i, n))
      cur = i
      if KEYPATCH and RECHOICE then patched_at = nil end  -- re-patch the answer's lookups
    elseif not chainp and i and i ~= cur and idx ~= written then
      local own = rows[i].want and rel == rows[i].s
      local t = own and i or next_want(cur or i)
      if ADOPT then
        -- obj+0x10 moves a page at a time, so the hook first sees a row when its first page is already drawn:
        -- keep it, credit it, and redirect only at its end, through the {wait} chain
        if rows[i].want and rel > rows[i].s then
          rows[i].want = false; left = left - 1
          L.log(string.format("SHOWN %d f%d", i, n))
        end
        if next_want(i) == nil then
          L.log(string.format("FORCE done f%d", n)); done_at = n + 600
        else
          cur = i
          arm(hoff, i, idx)
          L.log(string.format("ADOPT %d +%d f%d%s", i, rel - rows[i].s, n, chainp and " chain" or ""))
        end
      elseif t == nil then
        L.log(string.format("FORCE done f%d", n)); done_at = n + 600  -- let the last page draw, then stop
      elseif own then
        cur = t
      else
        idx = start(obj, hoff, t, false, n) or idx  -- the print op set obj+0 and obj+0x10: move both
      end
    end
  end
  last[obj] = idx
  if idx ~= written then L.log(string.format("PIDX %d %X f%d", idx, obj, n)) end
end

L.on_frame(function(n)
  local hoff
  for s = 0, 9 do
    local e = TABLE + 8 * s
    local id, off = u16(e), u16(e + 2)
    local v = string.format("%d %d", id, off)
    if tab[s] ~= v then tab[s] = v; L.log(string.format("SCR %d %s", s, v)) end
    if id == ID then hoff = off end
    if ENTRYGO and EG_ID and id == EG_ID then entrygo(off, n) end
  end
  if ENTRYGO and hoff then entrygo(hoff, n) end
  if done_at and n >= done_at then L.finish(0) end
  if (hoff ~= nil) ~= (patched_at ~= nil or kp_why ~= nil) and KEYPATCH then
    L.log(string.format("KEYPATCH file %s f%d", hoff and "in" or "out", n))
  end
  if KEYPATCH and hoff and hoff ~= patched_at and not done_at then keypatch(hoff, n) end
  if not hoff then patched_at, kp_why, sp_entry = nil, nil, nil end
  local hi = u16(OBJP + 2)
  local cobj = (hi >= 0x8000 and hi < 0x8020) and u32(OBJP) or nil
  if sp_entry and hoff and cobj and u16(cobj + 6) == ID then
    L.log(string.format("STARTPATCH jump obj %X pc %X -> %X f%d", cobj, u16(cobj + 0x12), sp_entry, n))
    w16(cobj + 0x12, sp_entry); w16(cobj + 0x16, 0)
    sp_entry = nil
  end
  if cobj and not printers[cobj] then
    local b = u32(cobj)
    if b >= BUF and b < BUFEND then
      printers[cobj] = true
      L.log(string.format("PRINTER %X f%d", cobj, n))
    end
  end
  if not hoff and chainp then L.log(string.format("UNLOAD f%d", n)) end
  if not hoff then chainp, pendq = nil, nil end  -- the file left the buffer: its patches went with it
  for p in pairs(printers) do handle(p, hoff, n) end
end)
