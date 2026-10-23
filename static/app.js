"use strict";
const $ = (id) => document.getElementById(id);
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
  $("job-domain").textContent = job.domain + (job.demo ? " · SIMULATED DEMO" : "");
  $("job-meta").textContent = `Scope: ${job.scope.join(", ")} · Created: ${new Date(job.created).toLocaleString()}`;
  $("job-state").textContent = job.status;
  $("job-state").className = `pill ${job.status}`;
  const done = terminal.has(job.status);
  $("cancel").hidden = done;
  $("demo").disabled = !done;
  $("start").disabled = !done;
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
  message("");
  $("demo").disabled = true;
  $("start").disabled = true;
  try { const job = await api("/api/jobs", {method: "POST", body: JSON.stringify(payload)}); await watch(job.id); }
  catch (error) { message(error.message); $("demo").disabled = false; $("start").disabled = false; }
}
$("demo").addEventListener("click", () => start({demo: true}));
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
    button.append(element("strong", `${job.domain}${job.demo ? " · demo" : ""}`),
      element("small", new Date(job.created).toLocaleString()), element("span", job.status, `pill ${job.status}`));
    button.addEventListener("click", () => watch(job.id));
    return button;
  }));
  return jobs;
}
$("check-tools").addEventListener("click", async () => {
  $("check-tools").disabled = true;
  $("tool-list").textContent = "Checking local help output / যাচাই হচ্ছে…";
  try {
    const tools = await api("/api/tools");
    $("tool-list").replaceChildren(...Object.entries(tools).map(([name, tool]) => {
      const item = element("div", undefined, "tool-item");
      item.append(element("strong", name), element("span", tool.status, `pill ${tool.status}`), element("small", tool.detail));
      return item;
    }));
  } catch (error) { $("tool-list").textContent = error.message; }
  finally { $("check-tools").disabled = false; }
});
history().then(jobs => {
  const requested = new URLSearchParams(location.search).get("job");
  const selected = jobs?.find(job => job.id === requested) || jobs?.find(job => !terminal.has(job.status));
  if (selected) watch(selected.id);
}).catch(error => message(error.message));
