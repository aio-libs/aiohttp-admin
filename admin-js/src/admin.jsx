import React from "react";
import ReactJSXRuntime from "react/jsx-runtime";
import ReactDOM from "react-dom";
import ReactDOMClient from "react-dom/client";
import {Link, Route, useLocation, useNavigate, useParams} from 'react-router-dom';
import QueryString from 'query-string';
import {App} from "./App";

// Copy libraries to global location for shim.
window.React = React;
window.ReactJSXRuntime = ReactJSXRuntime;
window.ReactDOM = ReactDOM;
window.ReactDOMClient = ReactDOMClient;
window.ReactRouterDOM = {Link, Route, useLocation, useNavigate, useParams};
window.QueryString = QueryString;

const _body = document.querySelector("body");
const STATE = Object.freeze(JSON.parse(_body.dataset.state));

const root = ReactDOMClient.createRoot(document.getElementById("root"));
root.render(
    <React.StrictMode>
        <App aiohttpState={STATE} />
    </React.StrictMode>
);
