import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider } from "@mui/material/styles";
import { CssBaseline } from "@mui/material";

import App from "./App";
import theme from "./theme/theme";

import { VehicleProvider } from "./context/VehicleContext";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <VehicleProvider>
          <App />
        </VehicleProvider>
      </BrowserRouter>
    </ThemeProvider>
  </React.StrictMode>
);