/* eslint-disable import-headings/import-headings -- the global index.css must load before the CSS modules */
// React
import React from "react";
import ReactDOM from "react-dom/client";

// Third Party
import { initI18n } from "aa-geuthur-react";

// Styles
import "@/Styles/index.css";
import "@/Styles/skillfarm.css";

import { AppName, ProjectName } from "@/constants";
import Routing from "@/Routing";
export { AppName, ProjectName };

initI18n(ProjectName, `${AppName}-root`);

const container = document.getElementById(`${AppName}-root`);

if (!container) {
  throw new Error("AA Skillfarm React mount point #aa-skillfarm-root was not found.");
}

ReactDOM.createRoot(container).render(
  <React.StrictMode>
    <Routing />
  </React.StrictMode>
);
