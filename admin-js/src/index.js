import React from "react";
import ReactJSXRuntime from "react/jsx-runtime";
import ReactDOM from "react-dom";
import ReactDOMClient from "react-dom/client";
import {Link, Route, useLocation, useNavigate, useParams} from 'react-router-dom';
import QueryString from 'query-string';
import {COMPONENTS, FUNCTIONS, App} from "./App";

// Copy libraries to global location for shim.
window.React = React;
window.ReactJSXRuntime = ReactJSXRuntime;
window.ReactDOM = ReactDOM;
window.ReactDOMClient = ReactDOMClient;
window.ReactRouterDOM = {Link, Route, useLocation, useNavigate, useParams};
window.QueryString = QueryString;

const _body = document.querySelector("body");
const STATE = Object.freeze(JSON.parse(_body.dataset.state));

let MODULE_LOADER;
if (STATE["js_module"]) {
    // The inline comment skips the webpack import() and allows us to use the native
    // browser's import() function. Needed to dynamically import a module.
    MODULE_LOADER = import(/* webpackIgnore: true */ STATE["js_module"]).then((mod) => {
        Object.assign(COMPONENTS, mod.components);
        Object.assign(FUNCTIONS, mod.functions);
    });
} else {
    MODULE_LOADER = Promise.resolve();
}

const root = ReactDOMClient.createRoot(document.getElementById("root"));
MODULE_LOADER.then(() => {
    root.render(
        <React.StrictMode>
            <App aiohttp-state={STATE} />
        </React.StrictMode>
    );
});
