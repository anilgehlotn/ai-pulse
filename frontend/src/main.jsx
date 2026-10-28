import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
// Self-hosted: Vite bundles the font files, so the page makes no external font requests.
import "@fontsource/plus-jakarta-sans/400.css";
import "@fontsource/plus-jakarta-sans/500.css";
import "@fontsource/plus-jakarta-sans/600.css";
import "./styles.css";

createRoot(document.getElementById("root")).render(<App />);
