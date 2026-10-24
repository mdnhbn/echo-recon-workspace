"use strict";

// Theme changes only presentation. No navigation, form reset or job requests.
(() => {
  const storageKey = "echo-recon-theme";
  const root = document.documentElement;
  const button = document.getElementById("theme-toggle");
  const validTheme = (value) => value === "light" || value === "dark";

  function applyTheme(value, persist = false) {
    const theme = validTheme(value) ? value : "dark";
    root.dataset.theme = theme;
    if (button) {
      const nextLight = theme === "dark";
      button.textContent = nextLight ? "Light layout / হালকা" : "Dark layout / ডার্ক";
      button.setAttribute("aria-label", nextLight
        ? "Switch to light layout / হালকা ইন্টারফেস দেখুন"
        : "Switch to dark layout / ডার্ক ইন্টারফেস দেখুন");
      button.setAttribute("aria-pressed", String(theme === "light"));
      button.title = theme === "light"
        ? "Current: light layout / বর্তমান: হালকা ইন্টারফেস"
        : "Current: dark layout / বর্তমান: ডার্ক ইন্টারফেস";
    }
    if (persist) {
      try { window.localStorage.setItem(storageKey, theme); }
      catch (_) { /* The theme still works when browser storage is unavailable. */ }
    }
  }

  let saved = "dark";
  try {
    const stored = window.localStorage.getItem(storageKey);
    if (validTheme(stored)) saved = stored;
  } catch (_) { /* Start with the original dark layout. */ }
  applyTheme(saved);

  button?.addEventListener("click", () => {
    applyTheme(root.dataset.theme === "light" ? "dark" : "light", true);
  });

  // Keep another open workspace tab in step without altering assessment data.
  window.addEventListener("storage", (event) => {
    if (event.key === storageKey) applyTheme(validTheme(event.newValue) ? event.newValue : "dark");
  });
})();
