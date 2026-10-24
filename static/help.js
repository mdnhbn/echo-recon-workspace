"use strict";
(() => {
  const guide = document.getElementById("usage-guide");
  function openGuide(target) {
    const downloads = document.getElementById("tool-downloads");
    if (downloads.open) downloads.close();
    if (!guide.open) guide.showModal();
    document.getElementById("close-guide").focus({preventScroll: true});
    const section = target && document.getElementById(target);
    guide.scrollTop = section ? Math.max(0, section.offsetTop - 75) : 0;
  }
  for (const id of ["open-guide", "open-guide-top"]) {
    document.getElementById(id).addEventListener("click", () => openGuide());
  }
  document.querySelectorAll("[data-guide-target]").forEach(button => {
    button.addEventListener("click", () => openGuide(button.dataset.guideTarget));
  });
  document.getElementById("close-guide").addEventListener("click", () => guide.close());
  const buttons = [...document.querySelectorAll("[data-setup-tools]")];
  const messages = [document.getElementById("setup-message"), ...document.querySelectorAll("[data-setup-message]")].filter(Boolean);
  const logs = [...document.querySelectorAll("[data-setup-log]")];
  let setupTimer = null;
  let setupGeneration = 0;
  let setupWasRunning = false;
  function setupMessage(text) { messages.forEach(node => { node.textContent = text; }); }
  function setupLog(text) {
    logs.forEach(node => {
      node.textContent = text;
      node.hidden = !text;
      node.scrollTop = node.scrollHeight;
    });
  }
  function disableSetup(disabled) { buttons.forEach(node => { node.disabled = disabled; }); }
  let toolsRefreshPending = false;
  function refreshToolsAfterSetup() {
    const checker = document.getElementById("check-tools");
    if (!checker.disabled) { checker.click(); return; }
    if (toolsRefreshPending) return;
    toolsRefreshPending = true;
    document.addEventListener("echo:tools-checked", () => {
      toolsRefreshPending = false;
      checker.click();
    }, {once: true});
  }
  async function setupResponse(path, options) {
    const response = await fetch(path, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Setup request failed");
    return data;
  }
  async function pollSetup(generation) {
    try {
      const data = await setupResponse("/api/setup-status");
      if (generation !== setupGeneration) return;
      setupMessage(data.message);
      setupLog(data.log || "");
      disableSetup(data.running);
      const finished = setupWasRunning && !data.running;
      setupWasRunning = data.running;
      if (data.running) setupTimer = setTimeout(() => pollSetup(generation), 1000);
      else if (finished) refreshToolsAfterSetup();
    } catch (error) {
      if (generation !== setupGeneration) return;
      if (setupWasRunning) {
        setupMessage(`${error.message}. Retrying setup progress…`);
        setupTimer = setTimeout(() => pollSetup(generation), 3000);
      } else {
        setupMessage(error.message);
        disableSetup(false);
      }
    }
  }
  buttons.forEach(button => button.addEventListener("click", async () => {
    clearTimeout(setupTimer);
    const generation = ++setupGeneration;
    disableSetup(true);
    setupMessage("Starting tool setup / টুল সেটআপ শুরু হচ্ছে…");
    setupLog("");
    try {
      const data = await setupResponse("/api/setup-tools", {method: "POST", headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]').content
      }, body: "{}"});
      if (generation !== setupGeneration) return;
      setupMessage(data.message);
      setupWasRunning = true;
      await pollSetup(generation);
    } catch (error) {
      if (generation !== setupGeneration) return;
      setupMessage(error.message);
      setupWasRunning = false;
      disableSetup(false);
    }
  }));
  pollSetup(setupGeneration);
})();
