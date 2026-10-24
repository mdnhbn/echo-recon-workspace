"use strict";
const $ = (id) => document.getElementById(id);
const canAssess = document.body.dataset.assessmentEnabled !== "false";
const csrf = document.querySelector('meta[name="csrf-token"]').content;
let activeId = null;
let polling = null;
const terminal = new Set(["complete", "partial", "error", "cancelled", "interrupted"]);
async function api(path, options = {}) {
  const res = await fetch(path, { ...options, headers: {"Content-Type": "application/json", "X-CSRF-Token": csrf, ...options.headers} });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `Request failed: ${res.status}`);
  return data;
}
function message(text) { $("message").textContent = text; }
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function render(job) {
  $("empty").hidden = true;
  $("job-content").hidden = false;
  $("job-domain").textContent = job.domain;
  $("job-meta").textContent = `Scope: ${job.scope.join(", ")} · Created: ${new Date(job.created).toLocaleString()}`;
  $("job-state").textContent = job.status;
  $("job-state").className = `pill ${job.status}`;
  const done = terminal.has(job.status);
  $("cancel").hidden = done;
  $("start").disabled = !done || !canAssess;
  $("phases").replaceChildren(...job.phases.map((phase) => {
    const row = element("div", undefined, `phase ${phase.status}`);
    const text = element("div");
    text.append(element("strong", phase.label), element("small", `${phase.tool} · ${phase.duration}s`));
    row.append(element("span", "", "indicator"), text, element("span", phase.status, "phase-state"));
    return row;
  }));
  $("logs").textContent = job.log.join("\n");
  $("logs").scrollTop = $("logs").scrollHeight;
  $("reports").hidden = !done;
  $("view-report").href = `/reports/${job.id}.html`;
  $("download-html").href = `/reports/${job.id}.html?download=1`;
  $("download-json").href = `/reports/${job.id}.json`;
  return done;
}
async function watch(id) {
  activeId = id;
  clearTimeout(polling);
  try {
    const done = render(await api(`/api/jobs/${id}`));
    if (done) await history();
    else polling = setTimeout(() => watch(id), 1000);
  } catch (error) {
    message(`${error.message}. Retrying / আবার চেষ্টা হচ্ছে…`);
    polling = setTimeout(() => watch(id), 3000);
  }
}
async function start(payload) {
  if (!canAssess) { message("Assessment execution is disabled for this dashboard. Tool setup and saved reports remain available."); return; }
  message("");
  $("start").disabled = true;
  try { const job = await api("/api/jobs", {method: "POST", body: JSON.stringify(payload)}); await watch(job.id); }
  catch (error) { message(error.message); $("start").disabled = !canAssess; }
}
$("scan-form").addEventListener("submit", (event) => {
  event.preventDefault();
  start({domain: $("domain").value, scope: $("scope").value.split(/\s+/).filter(Boolean),
    authorized: $("authorized").checked, understands_limits: $("limits").checked,
    tools: [...document.querySelectorAll('input[name="tool"]:checked')].map(input => input.value),
    rate: Number($("rate").value), timeout: Number($("timeout").value)});
});
$("cancel").addEventListener("click", async () => {
  if (!activeId) return;
  try { await api(`/api/jobs/${activeId}/cancel`, {method: "POST", body: "{}"}); message("Stop requested. Waiting for process cleanup / বন্ধের অনুরোধ পাঠানো হয়েছে।"); }
  catch (error) { message(error.message); }
});
async function history() {
  const jobs = await api("/api/jobs");
  if (!jobs.length) return;
  $("history-list").replaceChildren(...jobs.map(job => {
    const button = element("button", undefined, "history-item");
    button.append(element("strong", job.domain),
      element("small", new Date(job.created).toLocaleString()), element("span", job.status, `pill ${job.status}`));
    button.addEventListener("click", () => watch(job.id));
    return button;
  }));
  return jobs;
}
let latestTools = {};
$("check-tools").addEventListener("click", async () => {
  $("check-tools").disabled = true;
  $("check-tools-top").disabled = true;
  $("tool-list").textContent = "Checking local help output / যাচাই হচ্ছে…";
  try {
    const tools = await api("/api/tools?refresh=1");
    latestTools = tools;
    document.querySelectorAll("#download-list [data-tool-status]").forEach(pill => {
      const state = latestTools[pill.dataset.toolStatus]?.status || "not checked";
      pill.textContent = state;
      pill.className = `pill ${state}`;
    });
    $("tool-list").replaceChildren(...Object.entries(tools).map(([name, tool]) => {
      const item = element("div", undefined, "tool-item");
      item.append(element("strong", name), element("span", tool.status, `pill ${tool.status}`), element("small", tool.detail));
      if (tool.status !== "ready") {
        const setup = element("button", "Download / setup →", "button");
        setup.addEventListener("click", () => showDownloads(name));
        item.append(setup);
      }
      return item;
    }));
  } catch (error) { $("tool-list").textContent = error.message; }
  finally {
    $("check-tools").disabled = false;
    $("check-tools-top").disabled = false;
    document.dispatchEvent(new CustomEvent("echo:tools-checked"));
  }
});
$("check-tools-top").addEventListener("click", () => {
  $("tools").scrollIntoView({block: "start"});
  $("check-tools").click();
});

function link(label, href) {
  const anchor = element("a", label, "button");
  anchor.href = href;
  anchor.target = "_blank";
  anchor.rel = "noopener noreferrer";
  return anchor;
}
async function showDownloads(focusTool = null) {
  const dialog = $("tool-downloads");
  if (!dialog.open) dialog.showModal();
  $("download-list").textContent = "Loading official sources / লিংক আসছে…";
  try {
    const sources = await api("/api/tool-sources");
    const entries = Object.entries(sources);
    if (focusTool) entries.sort(([a], [b]) => Number(b === focusTool) - Number(a === focusTool));
    $("download-list").replaceChildren(...entries.map(([name, source]) => {
      const row = element("section", undefined, "download-item");
      const heading = element("h3", `${name} — ${source.label}`);
      const state = latestTools[name]?.status || "not checked";
      const status = element("span", state, `pill ${state}`);
      status.dataset.toolStatus = name;
      row.append(heading, status);
      row.append(element("p", source.note));
      if (state === "unverified") row.append(element("p", "Check version/PATH first; reinstalling may not be necessary. / আগে সঠিক version ও PATH দেখুন।", "download-note"));
      const actions = element("div", undefined, "download-actions");
      actions.append(link("Official download / উৎস ↗", source.url), link("Setup guide / ইনস্টল নিয়ম ↗", source.setup_url));
      row.append(actions);
      return row;
    }));
    dialog.scrollTop = 0;
  } catch (error) { $("download-list").textContent = error.message; }
}
$("download-tools").addEventListener("click", () => showDownloads());
$("download-tools-top").addEventListener("click", () => showDownloads());
$("close-downloads").addEventListener("click", () => $("tool-downloads").close());

// Original Echo-style binary rain. Respect reduced motion and pause hidden tabs.
const rain = $("rain");
if (rain && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
  const ctx = rain.getContext("2d");
  let drops = [];
  function resizeRain() {
    rain.width = innerWidth;
    rain.height = innerHeight;
    drops = Array.from({length: Math.ceil(innerWidth / 18)}, () => Math.random() * -60);
  }
  addEventListener("resize", resizeRain);
  resizeRain();
  setInterval(() => {
    if (document.hidden) return;
    ctx.fillStyle = "rgba(12, 17, 15, .09)";
    ctx.fillRect(0, 0, rain.width, rain.height);
    ctx.fillStyle = "rgba(89, 180, 121, .28)";
    ctx.font = "15px monospace";
    drops.forEach((drop, index) => {
      ctx.fillText(Math.random() > .5 ? "1" : "0", index * 18, drop * 18);
      drops[index] = drop * 18 > rain.height && Math.random() > .975 ? -2 : drop + .5;
    });
  }, 70);
}
history().then(jobs => {
  const requested = new URLSearchParams(location.search).get("job");
  const selected = jobs?.find(job => job.id === requested) || jobs?.find(job => !terminal.has(job.status));
  if (selected) watch(selected.id);
}).catch(error => message(error.message));

$("start").disabled = !canAssess;
