-- Favorite Dear: Enkan no Monogatari debug warp: cold boot -> any scene, no save and no savestate needed.
-- Port of game 1's tools/debug/warp.lua (../favorite-dear-en); addresses re-found here (docs/re/debug.md).
-- Normally run through tools/debug/warp.py SCENE, which reads tools/debug/scenes.tsv and sets these globals:
--   KIND   'title' | 'load' | 'option' | 'newgame' | 'week' | 'week2' | 'map' | 'event' | 'exec' | 'save'
--          ('week2': the week-1 orders, then circle through the week until the week screen is back)
--   EVENT  KIND 'event': a game-1 event name (MYH16, SEND01, SS0204 ..: its name hash is in this game's list) or
--          'eNNN', a GDATA entry 395-964 (the 108 events new in this game have no known name)
--   EXE    program for KIND 'exec' (OMK FD_BALL EPILOG FIN FD_MOV PS_MOV GOVER), started from the week-1 screen
--   SAVE   save number (1-3) for KIND 'save': loads it from the memory card given with emu.py --sav; arrival is
--          the week screen reached through the hub's 予定, so a rejected or corrupt save never arrives
--   PROOF  frames from arrival to the proof shot arrived.png (default 30)
--   AFTER  'mash' (default: press circle every MASH_EVERY frames once there) | 'hold' (no input once there)
--   MASH_EVERY  frames between circle presses after arrival (default 45)
--   MASH_ROTATE N: press down 0..N-1 times (pseudo-random) before each of those circle presses (choice menus)
--   POST   presses after arrival, route syntax with ';' between steps ("60 -;6 cross;500 -"): submenus of a
--          scene. Shot post.png when they are done; STATE is then saved there instead.
--   STATE  absolute path: save a savestate here 60 frames after arrival
--   TRACE  any value: log every change of the MODE/PHASE flags and the loaded-event table
--   HERO   KIND 'event': current-hero index (byte CUR_HERO) the swapped-in script sees
--   BATTLE KIND 'event': a battle's own event (T0101.., any id in the battle table). The host EVENT must start
--          battle STAGE_IDX (SS0204 does, for hero 2): the stage-table entry is rewritten to BATTLE's id.
--   SWAP   'ID=NAME': also make event id ID load NAME
--   MINI   N (1-12), KIND 'exec' with EXE 'OMK': the Omake Mini Event plays scene N. The script (OMK.EXE's own,
--          run in place at 0x8014AF08; docs/re/text.md §OMK mini events) reads the scene number from the EXE
--          (`007E 8002`) and switches on it twice (op 0x52 at pc 0x16 and 0x40, 12 cases): every case's target is
--          rewritten to case N's.
--
-- How it works (docs/re/debug.md): the opening is driven with the newgame route, then circle until the week screen
-- flag; the week-1 route sends both fairies to hero search, which makes the game load event MYH16 (id 32).
-- load_event(id) (0x800A161C) reads a u16 name hash at IDTAB + 2*id and finds it in the hash list HASHES
-- (index + 395 = GDATA entry). For KIND 'event' the hash in MYH16's slot is overwritten with the target's, so the
-- game's own loader fetches that script instead.
local mem = PCSX.getMemPtr()
local function rd16(a) a = a & 0x1FFFFF; return mem[a] | (mem[a + 1] << 8) end
local function wr16(a, v) a = a & 0x1FFFFF; mem[a] = v & 0xFF; mem[a + 1] = (v >> 8) & 0xFF end
local function rd32(a) a = a & 0x1FFFFF; return rd16(a) | (rd16(a + 2) << 16) end

local IDTAB = 0x8014FCFC        -- event id -> u16 name hash (game 1: 9-byte names at 0x80173640)
local HASHES, NHASH, GBASE = 0x801040E4, 570, 395   -- hash list; its index + 395 = GDATA entry
local SLOT = 32                 -- MYH16: first event of week 1 with both fairies on hero search
local SLOT_HASH = 0x354E        -- hash("MYH16"): PSX.EXE is loaded once this sits in SLOT
local NIDS = 600                -- ids scanned for BATTLE/TRACE (game 1 had 462)
local ENTRIES = 0x80148C6C      -- loaded-event table: 10 x (u16 id, u16 offset, u16, u16) (game 1 0x8016C5B8)
local MODE, PHASE = 0x80187448, 0x801875F0                 -- game 1 0x8001A4A8, 0x8001A654
local CUR_HERO = 0x8018DA05                                -- game 1 0x80020991
local STAGES, STAGE_IDX = 0x80150780, 0xC0                 -- game 1 0x80174BD8; SS0204's command D3 uses 0xC0

KIND = KIND or "event"
AFTER = AFTER or "mash"
MASH_EVERY = MASH_EVERY or 45

-- the loader's name hash (0x8001392C): sum of c * 11^i over the characters (mod 2^32), then folded to 16 bits
local function name_hash(s)
  local sum, m = 0, 1
  for i = 1, #s do
    sum = (sum + s:byte(i) * m) % 4294967296
    m = (m * 11) % 4294967296
  end
  return (sum + math.floor(sum / 65536)) % 65536
end
local function target_hash(name)
  local e = name:match("^e(%d+)$")
  if e then
    e = tonumber(e)
    assert(e >= GBASE and e < GBASE + NHASH, "event entry out of range: " .. name)
    return rd16(HASHES + 2 * (e - GBASE))
  end
  local h = name_hash(name)
  for i = 0, NHASH - 1 do if rd16(HASHES + 2 * i) == h then return h end end
  error("no event named " .. name .. " in this game (hash " .. string.format("%04X", h) .. ")")
end
local function id_of(name)
  local h = target_hash(name)
  for id = 0, NIDS - 1 do if rd16(IDTAB + 2 * id) == h then return id end end
  error("no event id loads " .. name)
end

local function week_screen() return rd16(MODE) == 5 and rd16(PHASE) == 1 end
local function exe_loaded() return rd16(IDTAB + 2 * SLOT) == SLOT_HASH end
local function event_loaded(id)
  for i = 0, 9 do if rd16(ENTRIES + 8 * i) == id then return true end end
  return false
end

-- KIND 'exec': from the week screen, jump the CPU into PSX.EXE's exec(path) (0x80014910, game 1 0x8003C7D4), with
-- a0 = the path string "\<EXE>.EXE;1" in PSX.EXE's data. Arrival = the CPU has gone through _LOADE.EXE
-- (0x801C0000-0x801C6800) and left it again.
local EXEC_FN, EXEC_FIRST = 0x80014910, 0x27BDFFE8   -- addiu sp, sp, -0x18 (checked before jumping)
local function find_str(s, lo, hi)
  local b1 = s:byte(1)
  for a = lo & 0x1FFFFF, (hi & 0x1FFFFF) - #s do
    if mem[a] == b1 then
      local ok = true
      for i = 2, #s do if mem[a + i - 1] ~= s:byte(i) then ok = false; break end end
      if ok then return 0x80000000 | a end
    end
  end
end
local function in_loader(pc) return pc >= 0x801C0000 and pc < 0x801C6800 end

local function route(steps) for _, s in ipairs(steps) do L.press(s[2], s[1]) end end
-- past logos and the opening movie to the title menu (New Game / Load Game / Option)
local TITLE = { {1500, "-"}, {6, "start"}, {300, "-"}, {6, "start"}, {300, "-"}, {6, "start"}, {600, "-"},
                {6, "start"}, {900, "-"}, {6, "start"}, {120, "-"} }
local NEWGAME = { {6, "circle"}, {600, "-"} }
-- title menu -> Load Game / Option (cursor moves need ~40 frames between presses)
local TITLE_SUB = { load = { {6, "down"}, {40, "-"}, {6, "circle"}, {1800, "-"} },
                    option = { {60, "-"}, {6, "down"}, {60, "-"}, {6, "down"}, {60, "-"}, {6, "circle"}, {600, "-"} } }
-- tools/routes/week1.txt: both fairies -> hero search, confirm
local WEEK1 = { {30, "-"}, {6, "right"}, {40, "-"}, {6, "circle"}, {60, "-"}, {6, "down"}, {40, "-"}, {6, "circle"},
                {90, "-"}, {6, "right"}, {40, "-"}, {6, "circle"}, {60, "-"}, {6, "down"}, {40, "-"}, {6, "circle"},
                {90, "-"}, {6, "left"}, {40, "-"}, {6, "left"}, {40, "-"}, {6, "circle"}, {90, "-"}, {6, "down"},
                {40, "-"}, {6, "circle"}, {90, "-"} }

local EXE_PATHS = { OMK = "\\OMK.EXE;1", GOVER = "\\GOVER.EXE;1", FD_BALL = "\\FD_BALL.EXE;1",
                    EPILOG = "\\TITLE\\EPILOG.EXE;1", FIN = "\\DATA\\FIN.EXE;1", FD_MOV = "\\TITLE\\FD_MOV.EXE;1",
                    PS_MOV = "\\PS_MOV.EXE;1" }
local exec_seen = false
PROOF = PROOF or 30

local stage = "boot"
local arrived_at = nil
local patched = false
local battle_id = nil
local map_at = nil
local post_done = nil
local left_week = false
local function go(s) stage = s; L.log(string.format("WARP %s f%d", s, L.frame)) end
local function arrive()
  arrived_at = L.frame
  go("arrived")
  L.log(string.format("WARP OK %s f%d", KIND == "event" and (BATTLE or EVENT) or KIND == "exec" and EXE or KIND, L.frame))
end

if KIND == "event" then
  assert(type(EVENT) == "string" and #EVENT >= 1 and #EVENT <= 8, "EVENT must be a 1-8 char event name or eNNN")
end

-- KIND 'save': Load Game -> slot 1 -> (card check) -> save SAVE (1-3) -> "ロードしますか？" (cursor on いいえ: left,
-- circle) -> the hub; then circle (予定) until the week screen flag: arrival proves the save loaded with no error.
SAVE = SAVE or 1
local SAVE_LOAD = { {6, "circle"}, {900, "-"} }
for _ = 2, SAVE do SAVE_LOAD[#SAVE_LOAD + 1] = {6, "down"}; SAVE_LOAD[#SAVE_LOAD + 1] = {40, "-"} end
for _, s in ipairs({ {6, "circle"}, {300, "-"}, {6, "left"}, {100, "-"}, {6, "circle"}, {1500, "-"} }) do
  SAVE_LOAD[#SAVE_LOAD + 1] = s
end

route(TITLE)
if KIND == "save" then route(TITLE_SUB.load); route(SAVE_LOAD)
elseif TITLE_SUB[KIND] then route(TITLE_SUB[KIND])
elseif KIND ~= "title" then route(NEWGAME) end
go("newgame")

local last_mode, last_events = nil, nil
local MINI_CODE = 0x8014AF08
local function mini_patch(n)
  for _, sw in ipairs({0x16, 0x40}) do
    local a = MINI_CODE + 2 * sw
    if rd16(a) ~= 0x52 or rd16(a + 2) ~= 0x8002 then return end
  end
  local done = true
  for _, sw in ipairs({0x16, 0x40}) do
    local a = MINI_CODE + 2 * sw
    local t = rd16(a + 4 * MINI + 2)
    for k = 1, 12 do
      if rd16(a + 4 * k) ~= k then return end  -- not the switch we know (12 cases, values 1..12)
      if rd16(a + 4 * k + 2) ~= t then wr16(a + 4 * k + 2, t); done = false end
    end
  end
  if not done then L.log(string.format("WARP mini scene %d f%d", MINI, n)) end
end
L.on_frame(function(n)
  if MINI then mini_patch(n) end
  if TRACE then
    local m = string.format("%d/%d", rd16(MODE), rd16(PHASE))
    if m ~= last_mode then L.log(string.format("TRACE mode/phase %s f%d", m, n)); last_mode = m end
    local ids = {}
    for i = 0, 9 do
      local id = rd16(ENTRIES + 8 * i)
      if id ~= 0xFFFF then ids[#ids + 1] = tostring(id) end
    end
    local e = table.concat(ids, ",")
    if e ~= last_events then L.log(string.format("TRACE events %s f%d", e, n)); last_events = e end
  end
  if KIND == "event" and not patched and exe_loaded() then
    if BATTLE then battle_id = id_of(BATTLE) end  -- before the slot is rewritten (MYH16's id could match)
    wr16(IDTAB + 2 * SLOT, target_hash(EVENT))
    patched = true
    L.log(string.format("WARP patched slot %d -> %s f%d", SLOT, EVENT, n))
    if SWAP then
      local id, nm = SWAP:match("^(%d+)=(%w+)$")
      wr16(IDTAB + 2 * tonumber(id), target_hash(nm))
      L.log(string.format("WARP swapped id %s -> %s f%d", id, nm, n))
    end
    if BATTLE then
      wr16(STAGES + 2 * STAGE_IDX, battle_id)
      L.log(string.format("WARP stage %d -> %s (id %d) f%d", STAGE_IDX, BATTLE, battle_id, n))
    end
  end

  if stage == "newgame" then
    if KIND == "save" then
      if L.route_done() then go("loaded") end
    elseif KIND == "title" or TITLE_SUB[KIND] then
      if L.route_done() then arrive() end
    elseif KIND == "newgame" then
      if rd16(MODE) == 2 and n > 5000 then arrive() end  -- name entry panel
    elseif L.route_done() then
      go("opening")
    end
  elseif stage == "loaded" then
    if week_screen() then
      if not arrived_at then arrived_at = n end
      if n - arrived_at >= 30 then arrive() end
    elseif L.route_done() and n % 60 == 0 then
      L.press("circle", 6)
    end
  elseif stage == "opening" then
    if week_screen() then
      go("week_wait")
      arrived_at = n
    elseif L.route_done() and n % 20 == 0 then
      L.press("circle", 6)
    end
  elseif stage == "week_wait" then
    if n - arrived_at >= 30 then
      if KIND == "week" then
        arrive()
      elseif KIND == "exec" then
        local path = assert(EXE_PATHS[EXE], "unknown EXE " .. tostring(EXE))
        local s = find_str(path .. "\0", 0x80011000, 0x80012000)
        assert(s, "exec path string not found in PSX.EXE: " .. path)
        assert(rd32(EXEC_FN) == EXEC_FIRST, "exec() moved: no addiu sp at 0x80014910")
        local r = PCSX.getRegisters()
        L.log(string.format("WARP exec %s (a0=%08x, pc was %08x) f%d", path, s, tonumber(r.pc), n))
        if ENDING or ENDING2 then
          -- EPILOG.EXE (0x8001EF00) reads its ending from the scratchpad: u16 0x14 = ending (0xFF: use byte 0x1C,
          -- the hero); u16 0x16 == 1: hero + 13 (game 1: + 12). ENDING = n writes 0x14 = n, 0x16 = 0, 0x1C = n; ENDING2 = hero
          -- writes 0x14 = 0xFF, 0x16 = 1, 0x1C = hero.
          local sp = assert(PCSX.getScratchPtr, "no PCSX.getScratchPtr")()
          local e, alt = ENDING, 0
          if ENDING2 then e, alt = 0xFF, 1 end
          sp[0x14] = e & 0xFF; sp[0x15] = 0; sp[0x16] = alt; sp[0x17] = 0
          sp[0x1C] = ENDING2 or ENDING
          L.log(string.format("WARP ending scratch 0x14=%d 0x16=%d 0x1C=%d f%d", e, alt, sp[0x1C], n))
        end
        r.GPR.n.a0 = s
        r.pc = EXEC_FN
        go("exec_wait")
      else
        route(WEEK1); go("week1")
      end
    end
  elseif stage == "exec_wait" then
    local pc = tonumber(PCSX.getRegisters().pc)
    if in_loader(pc) then exec_seen = true
    elseif exec_seen then arrive() end
  elseif stage == "week1" then
    if L.route_done() then go("to_event"); arrived_at = n end
  elseif stage == "to_event" then
    -- the world map shows ~f400-550 after MODE turns 1 (the orders confirmed; no text in between)
    if KIND == "week2" then
      -- play week 1 through (circle every 60 frames) until the week screen is back: week 2
      if not week_screen() then left_week = true end
      if left_week and week_screen() then
        if not map_at then map_at = n end
        if n - map_at >= 30 then arrive() end
      elseif L.route_done() and n % 60 == 0 then
        L.press("circle", 6)
      end
    elseif KIND == "map" and rd16(MODE) == 1 then
      if not map_at then map_at = n end
      if n - map_at >= 450 then arrive() end
    elseif KIND == "event" and not BATTLE and event_loaded(SLOT) then
      arrive()
    elseif BATTLE and battle_id and event_loaded(battle_id) then
      arrive()
    elseif BATTLE and event_loaded(SLOT) then
      local s = STAGES + 2 * STAGE_IDX
      if rd16(s) ~= battle_id then
        L.log(string.format("WARP stage %d was %d, rewritten f%d", STAGE_IDX, rd16(s), n))
        wr16(s, battle_id)
      end
      if HERO then mem[CUR_HERO & 0x1FFFFF] = HERO end  -- the host reads the hero before it starts the battle
      if n % 60 == 0 then L.press("circle", 6) end
    elseif not map_at and L.route_done() and n % 60 == 0 then
      L.press("circle", 6)
    end
  elseif stage == "arrived" then
    local dt = n - arrived_at
    if HERO and KIND == "event" and dt <= 10 then
      mem[CUR_HERO & 0x1FFFFF] = HERO
      if dt == 0 then L.log(string.format("WARP hero %d f%d", HERO, n)) end
    end
    if dt == PROOF then
      L.shot("arrived.png")
      if POST then
        for f, keys in POST:gmatch("(%d+)%s+([%w+%-]+)") do L.press(keys, tonumber(f)) end
      end
    end
    if dt > PROOF and POST and L.route_done() and not post_done then
      post_done = n
      L.shot("post.png")
      L.log(string.format("WARP POST done f%d", n))
    end
    if STATE and (POST and post_done == n or not POST and dt == PROOF + 30) then
      L.save_state(STATE); L.log("WARP state " .. STATE)
    end
    if AFTER == "hold" and dt >= PROOF + 60 and (not POST or post_done) then L.shot("final.png"); L.finish(0) end
    -- with a POST route, mash only once it is done (its presses would otherwise steer the menu it walks)
    if AFTER == "mash" and dt > 0 and dt % MASH_EVERY == 0 and L.route_done() and (not POST or post_done) then
      if MASH_ROTATE then
        rot_seed = ((rot_seed or ROT_SEED or 1) * 75 + 74) % 65537   -- ZX81 LCG: exact in doubles (LuaJIT)
        for _ = 1, rot_seed % MASH_ROTATE do L.press("down", 6); L.press("-", 10) end
      end
      L.press("circle", 6)
    end
  end
end)
