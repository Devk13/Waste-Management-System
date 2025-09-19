"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var react_1 = require("react");
var client_1 = require("react-dom/client");
var App_1 = require("./App");
require("./styles.css");
// IMPORTANT: enable WTN auto-open & banner
require("./wtnHook");
var WtnPrompt_1 = require("./components/WtnPrompt");
client_1.default.createRoot(document.getElementById('root')).render(<react_1.default.StrictMode>
    <App_1.default />
    {/* Renders globally so any page benefits */}
    <WtnPrompt_1.default />
  </react_1.default.StrictMode>);
