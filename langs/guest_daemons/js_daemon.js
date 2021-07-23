const net = require("net");
const SOCKET = new net.Socket();
const port = process.argv[2];
SOCKET.connect(port, "127.0.0.1", () => {
  SOCKET.write(JSON.stringify({ type: "connect", lang: "JavaScript" }));
});

let GENERATOR_STACK = [];

SOCKET.on("data", (data) => {
  try {
    let jsonData = JSON.parse(data);
    let genParam = null;
    let genResult = null;
    if (jsonData["type"] == "call_func") {
      // importing the actual function from file
      var script = require(jsonData["func_path"]);
      gen = script.reserved_name();
      GENERATOR_STACK.push(gen);
    } else if (jsonData["type"] == "ditlang_callback") {
      // we executed some ditLang code, and genParam is now the result
      genParam = jsonData["result"];
      gen = GENERATOR_STACK[GENERATOR_STACK.length - 1];
    } else if (jsonData["type"] == "return_keyword") {
      return finish();
    } else {
      throw new Error("Unknown message type");
    }
    // .next either starts the generator function,
    // or resumes from the previous yield point.
    // genParam will be used as the value of the yield expression.
    genResult = gen.next(genParam);

    if (genResult.done) {
      finish();
    } else {
      // genResult.value is ditLang code we need to execute
      let exeMessage = JSON.stringify({
        type: "exe_ditlang",
        result: genResult.value,
      });
      SOCKET.write(exeMessage);
    }
  } catch (err) {
    crashMessage = JSON.stringify({
      type: "crash",
      result: err.stack,
    });
    SOCKET.write(crashMessage);
  }
});

function finish() {
  GENERATOR_STACK.pop();
  let finishMessage = JSON.stringify({
    type: "finish_func",
    result: null,
  });
  SOCKET.write(finishMessage);
}
