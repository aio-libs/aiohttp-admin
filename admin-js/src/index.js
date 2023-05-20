import React from "react";
import ReactDOM from "react-dom/client";
import {App, MODULE_LOADER} from "./App";

const root = ReactDOM.createRoot(document.getElementById("root"));
MODULE_LOADER.then(() => {
    root.render(
        <React.StrictMode>
            <App />
        </React.StrictMode>
    );
});
