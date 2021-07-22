local json = require("rxi-json-lua")
local socket = require("socket")
SOCKET = assert(socket.tcp())
local host, port = "127.0.0.1", arg[1]
package.path = '/tmp/dit/?.lua;' .. package.path
SOCKET:connect(host, port);
local connectMes = json.encode({type = "connect", lang = "Lua"})
SOCKET:send(connectMes)

GENERATOR = nil

local function daemon_loop()
    local s, status, partial = SOCKET:receive()
    if status ~= "closed" then
        local jsonData = json.decode(s)
        local genParam = nil
        if jsonData['type'] == "call_func" then
            genParam = require(string.sub(jsonData["func_path"], 10, -5))
            GENERATOR = coroutine.create(function (func_to_call)
                    func_to_call()
                end)
        elseif jsonData['type'] == "ditlang_callback" then
            genParam = jsonData["result"]
        end

        local no_errors, genResult = coroutine.resume(GENERATOR, genParam)
        if genResult == 0 then
            local finish_message = json.encode({type = "finish_func", result = nil})
            SOCKET:send(finish_message)
        else
            local exeMessage = json.encode({type = "exe_ditlang", result = genResult})
            SOCKET:send(exeMessage)
        end
    end
end

while true do
    local status, err = pcall(daemon_loop) 
    if status == false then
        local crashMessage = json.encode({type = "crash", result = err})
        SOCKET:send(crashMessage)
    end
end

SOCKET:close()