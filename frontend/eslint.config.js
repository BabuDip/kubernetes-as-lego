import js from "@eslint/js";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import jsxA11y from "eslint-plugin-jsx-a11y";
import prettierConfig from "eslint-config-prettier";
import globals from "globals";

// Flat config (ESLint 9+). Prettier owns formatting — it must stay last so its
// config can disable any stylistic rules the other presets turn on.
export default [
  { ignores: ["dist/**", "node_modules/**"] },
  js.configs.recommended,
  react.configs.flat.recommended,
  react.configs.flat["jsx-runtime"],
  jsxA11y.flatConfigs.recommended,
  {
    files: ["**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: "module",
      globals: globals.browser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    settings: {
      react: { version: "detect" },
    },
    rules: {
      ...reactHooks.configs["recommended-latest"].rules,
      // This codebase deliberately syncs local state to external systems (websocket
      // events, the wall clock, URL search params) inside effects — the textbook use
      // case for useEffect. Keep the rule visible as a warning rather than blocking.
      "react-hooks/set-state-in-effect": "warn",
      // Vite's HMR fast-refresh only works if a module exports just components;
      // small-constant exports (labels, config objects) are common here and fine.
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
      // No PropTypes/TypeScript in this codebase yet — don't ask for a form of
      // type-checking that isn't actually used.
      "react/prop-types": "off",
      // Security-conscious defaults.
      "no-eval": "error",
      "no-implied-eval": "error",
      "no-new-func": "error",
      "react/no-danger": "error",
      "no-console": ["warn", { allow: ["warn", "error"] }],
    },
  },
  {
    // The Context-provider-plus-hook file (`useX` exported next to `XProvider`) is
    // React's own documented pattern for context — splitting it into two files per
    // context would add indirection with no real benefit at this app's size.
    files: ["**/context/*.jsx", "**/components/LiveDuration.jsx"],
    rules: {
      "react-refresh/only-export-components": "off",
    },
  },
  prettierConfig,
];
