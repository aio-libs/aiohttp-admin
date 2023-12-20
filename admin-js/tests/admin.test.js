const http = require("http")
const {spawn} = require("child_process");
import {configure, render, screen, waitFor} from "@testing-library/react";

const {App} = require("../src/App");

jest.setTimeout(300000);  // 5 mins
configure({"asyncUtilTimeout": 10000})

let pythonProcess;
let STATE;
let APP;

beforeAll(async () => {
    pythonProcess = spawn("python3", ["examples/simple.py"], {"cwd": ".."});

    await new Promise(resolve => setTimeout(resolve, 2000));

    await new Promise(resolve => {
        http.get("http://localhost:8080/admin", resp => {
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
   //APP = <App aiohttp-state={STATE} />;
});


test("data is displayed", async () => {
    render(<App aiohttp-state={STATE} />);

    await waitFor(() => screen.getByText("Username"));

    screen.debug();

    expect(screen.getByText("Username")).toBeInTheDocument();
});
