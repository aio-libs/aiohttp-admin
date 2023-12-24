const http = require("http");
const {spawn} = require("child_process");
import "whatwg-fetch";  // https://github.com/jsdom/jsdom/issues/1724
import "@testing-library/jest-dom";
import failOnConsole from "jest-fail-on-console";
import {configure, render} from "@testing-library/react";
import * as structuredClone from "@ungap/structured-clone";

const {App} = require("../src/App");

let pythonProcess;
let STATE;

jest.setTimeout(300000);  // 5 mins
configure({"asyncUtilTimeout": 10000});

// https://github.com/jsdom/jsdom/issues/3363#issuecomment-1387439541
global.structuredClone = structuredClone.default;

// To render full-width
window.matchMedia = (query) => ({
    matches: true,
    addListener: () => {},
    removeListener: () => {}
});

// Ignore not implemented errors
window.scrollTo = jest.fn();

failOnConsole({
    silenceMessage: (msg) => {
        // Suppress act() warnings, because there's too many async changes happening.
        return msg.includes("inside a test was not wrapped in act(...).");
    }
});

beforeAll(async() => {
    if (!global.pythonProcessPath)
        return;

    if (global.__coverage__)
        pythonProcess = spawn("coverage", ["run", "--source=examples/,aiohttp_admin/", global.pythonProcessPath], {"cwd": ".."});
    else
        pythonProcess = spawn("python3", ["-u", global.pythonProcessPath], {"cwd": ".."});

    pythonProcess.stderr.on("data", (data) => {console.error(`stderr: ${data}`);});

    await new Promise(resolve => setTimeout(resolve, 2500));

    await new Promise(resolve => {
        http.get("http://localhost:8080/admin", {"timeout": 2000}, resp => {
            if (resp.statusCode !== 200)
                throw new Error("Request failed");

            let html = "";
            resp.on("data", (chunk) => { html += chunk; });
            resp.on("end", () => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, "text/html");
                STATE = JSON.parse(doc.querySelector("body").dataset.state);
                resolve();
            });
        });
    });
});

afterAll(() => {
    if (pythonProcess)
        pythonProcess.kill("SIGINT");
});


beforeEach(() => {
    if (STATE)
        render(<App aiohttp-state={STATE} />);
});
