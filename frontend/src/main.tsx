// React
import React from "react";
import ReactDOM from "react-dom/client";

// Styles
import "@/index.css";

import App, { AppName } from "@/App";

const container = document.getElementById(`${AppName}-root`);

if (!container) {
  throw new Error("AA Skillfarm React mount point #aa-skillfarm-root was not found.");
}

ReactDOM.createRoot(container).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
