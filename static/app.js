"use strict";
const $ = (id) => document.getElementById(id);
const canAssess = document.body.dataset.assessmentEnabled !== "false";
const csrf = document.querySelector('meta[name="csrf-token"]').content;
let activeId = null;
let polling = null;
const terminal = new Set(["complete", "partial", "error", "cancelled", "interrupted"]);
const finishedPhases = new Set(["done", "error", "missing", "unverified", "skipped", "cancelled", "output_limit", "timeout"]);
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
function formatDuration(value) {
  const seconds = Math.max(0, Math.floor(Number(value) || 0));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const rest = seconds % 60;
  return hours ? hours + "h " + minutes + "m" : minutes ? minutes + "m " + rest + "s" : rest + "s";
}
function since(value, end = Date.now()) {
  const start = Date.parse(value || "");
  return Number.isFinite(start) ? formatDuration((end - start) / 1000) : "—";
}
function render(job) {
  $("empty").hidden = true;
  $("job-content").hidden = false;
  $("job-domain").textContent = job.domain;
  $("job-meta").textContent = "Scope: " + job.scope.join(", ") + " · Elapsed / চলেছে: " + since(job.created, terminal.has(job.status) && job.finished_at ? Date.parse(job.finished_at) : Date.now());
  $("job-state").textContent = job.status;
  $("job-state").className = `pill ${job.status}`;
  const done = terminal.has(job.status);
  $("cancel").hidden = done;
  $("start").disabled = !done || !canAssess;
  const completedPhases = job.phases.filter(phase => finishedPhases.has(phase.status)).length;
  const percent = job.phases.length ? Math.round(completedPhases / job.phases.length * 100) : 0;
  $("overall-progress-fill").style.width = percent + "%";
  $("overall-progress").setAttribute("aria-valuenow", String(percent));
  $("overall-progress-text").textContent = percent + "% complete / সম্পন্ন · " + (100 - percent) + "% remaining / বাকি · " + completedPhases + "/" + job.phases.length + " checks resolved / ধাপ শেষ";
  const samples = job.phases.filter(phase => finishedPhases.has(phase.status) && Number(phase.duration) > 0)
    .map(phase => Number(phase.duration));
  const remaining = job.phases.length - completedPhases;
  $("overall-eta").textContent = done ? "Assessment finished / পরীক্ষা শেষ"
    : samples.length && remaining
      ? "Rough ETA / আনুমানিক বাকি: ~" + formatDuration(samples.reduce((sum, value) => sum + value, 0) / samples.length * remaining) + "; tool speeds vary / tool-এর গতি আলাদা।"
      : remaining ? "ETA appears after a tool finishes / একটি tool শেষ হলে ETA দেখা যাবে; within-tool % may be unavailable / tool-এর ভেতরের % নাও পাওয়া যেতে পারে।" : "";
  $("phases").replaceChildren(...job.phases.map((phase) => {
    const row = element("div", undefined, `phase ${phase.status}`);
    const text = element("div", undefined, "phase-copy");
    text.append(element("strong", phase.label));
    const attempts = Array.isArray(phase.attempts) ? phase.attempts.length : 0;
    const completedHosts = Number(phase.completed_hosts ?? attempts);
    const totalHosts = Number(phase.total_hosts || (phase.status === "done" ? completedHosts : 0));
    const hostPercent = totalHosts ? Math.round(completedHosts / totalHosts * 100)
      : phase.status === "done" ? 100 : 0;
    let detail = phase.status;
    if (phase.status === "running") {
      const started = phase.current_started_at || phase.started_at;
      const hostProgress = totalHosts ? " · hosts " + completedHosts + "/" + totalHosts : "";
      const current = phase.current_host ? " · " + phase.current_host : "";
      const estimate = completedHosts && totalHosts > completedHosts
        ? " · rough ETA / আনুমানিক বাকি ~" + formatDuration(Number(phase.duration) / completedHosts * (totalHosts - completedHosts))
        : " · ETA appears after a host finishes / একটি host শেষ হলে ETA আসবে";
      detail = "Running / চলছে · " + hostPercent + "% complete / সম্পন্ন · " + (100 - hostPercent) + "% remaining / বাকি · elapsed / চলেছে " + since(started) + hostProgress + current + estimate + " · within-host % unavailable / host-এর ভেতরের % নেই";
    } else if (phase.duration) {
      detail = phase.status + " · " + hostPercent + "% complete / সম্পন্ন · " + (100 - hostPercent) + "% remaining / বাকি · " + formatDuration(phase.duration) + " · hosts attempted / host চেষ্টা " + completedHosts + "/" + (totalHosts || completedHosts);
    } else {
      detail = phase.status + " · " + hostPercent + "% complete / সম্পন্ন · " + (100 - hostPercent) + "% remaining / বাকি";
    }
    text.append(element("small", detail));
    const track = element("div", undefined, "phase-progress-track");
    track.setAttribute("role", "progressbar");
    track.setAttribute("aria-valuemin", "0");
    track.setAttribute("aria-valuemax", "100");
    track.setAttribute("aria-valuenow", String(hostPercent));
    track.setAttribute("aria-label", phase.label + ": " + hostPercent + "% complete, " + (100 - hostPercent) + "% remaining; " + completedHosts + " of " + (totalHosts || completedHosts) + " host attempts finished");
    const fill = element("span", undefined, "phase-progress-fill");
    fill.style.width = hostPercent + "%";
    track.append(fill);
    text.append(track);
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
  start({target_url: $("target-url").value, scope: $("scope").value.split(/\s+/).filter(Boolean),
    authorized: $("authorized").checked, understands_limits: $("limits").checked,
    tools: [...document.querySelectorAll('input[name="tool"]:checked')].map(input => input.value),
    rate: Number($("rate").value)});
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

history().then(jobs => {
  const requested = new URLSearchParams(location.search).get("job");
  const selected = jobs?.find(job => job.id === requested) || jobs?.find(job => !terminal.has(job.status));
  if (selected) watch(selected.id);
}).catch(error => message(error.message));

$("start").disabled = !canAssess;
