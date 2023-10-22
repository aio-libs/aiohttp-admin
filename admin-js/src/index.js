import React from "react";
import ReactJSXRuntime from "react/jsx-runtime";
import ReactDOM from "react-dom";
import ReactDOMClient from "react-dom/client";
import {Link, Route, useLocation, useNavigate, useParams} from 'react-router-dom';
import QueryString from 'query-string';
import {App, MODULE_LOADER} from "./App";

// Copy libraries to global location for shim.
window.React = React;
window.ReactJSXRuntime = ReactJSXRuntime;
window.ReactDOM = ReactDOM;
window.ReactDOMClient = ReactDOMClient;
window.ReactRouterDOM = {Link, Route, useLocation, useNavigate, useParams};
window.QueryString = QueryString;

const root = ReactDOMClient.createRoot(document.getElementById("root"));
MODULE_LOADER.then(() => {
    root.render(
        <React.StrictMode>
            <App />
        </React.StrictMode>
    );
});
