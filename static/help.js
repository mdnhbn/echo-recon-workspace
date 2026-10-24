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
  const messages = [document.getElementById("setup-message"), ...document.querySelectorAll("[data-setup-message]")];
  function setupMessage(text) { messages.forEach(node => { node.textContent = text; }); }
  buttons.forEach(button => button.addEventListener("click", async () => {
    buttons.forEach(node => { node.disabled = true; });
    setupMessage("Opening the setup terminal / সেটআপ terminal খোলা হচ্ছে…");
    try {
      const response = await fetch("/api/setup-tools", {method: "POST", headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]').content
      }, body: "{}"});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Setup launch failed");
      setupMessage(data.message);
    } catch (error) { setupMessage(error.message); }
    finally { buttons.forEach(node => { node.disabled = false; }); }
  }));
})();
