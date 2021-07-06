const net = require("net");
const server = new net.Socket();
const port = process.argv[2];
server.connect(port, "127.0.0.1", () => {
    server.write(JSON.stringify({ type: "connect", lang: "JavaScript" }));
});

let FUNC_ITER = null;

server.on("data", (data) => {
    try {
        let jsonData = JSON.parse(data);
        let ditlang_callback = null;
        let exe_ditlang = null;
        if (jsonData["type"] == "call_func") {
            // importing the actual function from file
            var script = require(jsonData["func_path"]);
            FUNC_ITER = script.reserved_name();
        } else if (jsonData["type"] == "ditlang_callback") {
            ditlang_callback = jsonData["result"];
        }
        // .next either starts the generator function,
        // or resumes from the previous yield point.
        exe_ditlang = FUNC_ITER.next(ditlang_callback);

        // 0 is used as a control value, only returned when the function is over.
        if (exe_ditlang.value == 0) {
            let finishMessage = JSON.stringify({
                type: "finish_func",
                result: null,
            });
            server.write(finishMessage);
        } else {
            let exeMessage = JSON.stringify({
                type: "exe_ditlang",
                result: exe_ditlang.value,
            });
            server.write(exeMessage);
        }
    } catch (err) {
        crashMessage = JSON.stringify({
            type: "crash",
            result: err.stack,
        });
        server.write(crashMessage);
    }
});
