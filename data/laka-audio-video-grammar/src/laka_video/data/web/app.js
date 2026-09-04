const form = document.querySelector("#upload-form");
const fileInput = document.querySelector("#files");
const dropzone = document.querySelector("#dropzone");
const fileList = document.querySelector("#file-list");
const formError = document.querySelector("#form-error");
const submitButton = document.querySelector("#submit-button");
const statusSection = document.querySelector("#status-section");
const statusHeading = document.querySelector("#status-heading");
const statusMessage = document.querySelector("#status-message");
const statusPercent = document.querySelector("#status-percent");
const progress = document.querySelector("#render-progress");
const jobError = document.querySelector("#job-error");
const result = document.querySelector("#result");
const menuButton = document.querySelector("#menu-button");
const menuPanel = document.querySelector("#menu-panel");

const narrationExtensions = new Set(["aac", "flac", "m4a", "mkv", "mov", "mp3", "mp4", "oga", "ogg", "opus", "wav", "webm"]);
const stageOrder = ["preparing", "compiling", "rendering", "complete"];
let pollTimer;

function extension(filename) {
  return filename.includes(".") ? filename.split(".").pop().toLowerCase() : "";
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

function renderFiles() {
  fileList.replaceChildren();
  for (const file of fileInput.files) {
    const item = document.createElement("li");
    const kind = document.createElement("span");
    kind.className = "file-kind";
    kind.setAttribute("aria-hidden", "true");
    kind.textContent = extension(file.name) === "srt" ? "T" : "A";
    const name = document.createElement("strong");
    name.textContent = file.name;
    const size = document.createElement("span");
    size.textContent = formatBytes(file.size);
    item.append(kind, name, size);
    fileList.append(item);
  }
}

function showError(container, message) {
  container.querySelector("p").textContent = message;
  container.hidden = false;
  container.focus();
}

function clearError(container) {
  container.hidden = true;
  container.querySelector("p").textContent = "";
}

function validateFiles() {
  const files = [...fileInput.files];
  const unsupported = files.find((file) => !narrationExtensions.has(extension(file.name)) && extension(file.name) !== "srt");
  const narration = files.filter((file) => narrationExtensions.has(extension(file.name)));
  const transcripts = files.filter((file) => extension(file.name) === "srt");
  if (unsupported) return `Files: unsupported type for ${unsupported.name}. Add audio, video, or an SRT transcript.`;
  if (!narration.length) return "Narration: add one audio or video file. An SRT alone has no soundtrack to render.";
  if (narration.length > 1) return "Narration: add only one audio or video file per render.";
  if (transcripts.length > 1) return "Transcript: add no more than one SRT file per render.";
  return "";
}

function setStepper(status, jobProgress) {
  let index = status === "queued" ? 0 : stageOrder.indexOf(status);
  if (status === "failed") index = jobProgress >= 28 ? 2 : jobProgress >= 14 ? 1 : 0;
  document.querySelectorAll("#stepper li").forEach((item, itemIndex) => {
    item.classList.toggle("is-complete", itemIndex < index || status === "complete");
    item.classList.toggle("is-current", itemIndex === index && status !== "complete");
    if (itemIndex === index && status !== "complete") item.setAttribute("aria-current", "step");
    else item.removeAttribute("aria-current");
  });
}

function renderResult(job) {
  result.hidden = false;
  const shell = result.querySelector(".video-shell");
  shell.style.aspectRatio = `${job.output.width} / ${job.output.height}`;
  shell.replaceChildren();
  const video = document.createElement("video");
  video.controls = true;
  video.preload = "metadata";
  video.src = job.video_url;
  shell.append(video);

  const meta = result.querySelector("#result-meta");
  meta.replaceChildren();
  const rows = [
    ["Duration", `${job.output.duration.toFixed(1)}s`],
    ["Frame", `${job.output.width}×${job.output.height}`],
    ["Scenes", String(job.output.scenes)],
    ["Lint score", `${job.output.lint_score}/100`],
  ];
  for (const [label, value] of rows) {
    const row = document.createElement("div");
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value;
    row.append(term, description);
    meta.append(row);
  }

  const actions = result.querySelector(".result-actions") || document.createElement("div");
  actions.className = "result-actions";
  actions.replaceChildren();
  const download = document.createElement("a");
  download.className = "button button-primary";
  download.href = job.download_url;
  download.textContent = "Download MP4";
  const report = document.createElement("a");
  report.className = "button button-secondary";
  report.href = job.report_url;
  report.textContent = "Decision report";
  actions.append(download, report);
  if (!actions.parentElement) result.querySelector(".result-copy").append(actions);
}

function renderJob(job) {
  statusSection.hidden = false;
  statusHeading.textContent = job.step;
  statusMessage.textContent = job.message;
  statusPercent.textContent = `${job.progress}%`;
  progress.value = job.progress;
  progress.textContent = `${job.progress}%`;
  setStepper(job.status, job.progress);
  statusSection.setAttribute("aria-busy", String(!new Set(["complete", "failed"]).has(job.status)));
  if (job.error) showError(jobError, `${job.step}: ${job.error}`);
  else clearError(jobError);
  if (job.status === "complete") renderResult(job);
  else result.hidden = true;
}

async function pollJob(url) {
  window.clearTimeout(pollTimer);
  try {
    const response = await fetch(url, { headers: { Accept: "application/json" } });
    const job = await response.json();
    if (!response.ok) throw new Error(job.error || "The render status could not be read.");
    renderJob(job);
    if (!new Set(["complete", "failed"]).has(job.status)) {
      pollTimer = window.setTimeout(() => pollJob(job.status_url), 750);
    } else {
      submitButton.disabled = false;
    }
  } catch (error) {
    showError(jobError, `Status: ${error.message}`);
    submitButton.disabled = false;
  }
}

fileInput.addEventListener("change", () => {
  clearError(formError);
  renderFiles();
});

for (const eventName of ["dragenter", "dragover"]) {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add("is-dragging");
  });
}

for (const eventName of ["dragleave", "drop"]) {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove("is-dragging");
  });
}

dropzone.addEventListener("drop", (event) => {
  if (!event.dataTransfer?.files.length) return;
  const transfer = new DataTransfer();
  for (const file of event.dataTransfer.files) transfer.items.add(file);
  fileInput.files = transfer.files;
  clearError(formError);
  renderFiles();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError(formError);
  clearError(jobError);
  const problem = validateFiles();
  if (problem) {
    showError(formError, problem);
    return;
  }
  submitButton.disabled = true;
  submitButton.querySelector("span").textContent = "Sending files…";
  try {
    const response = await fetch(form.action, {
      method: "POST",
      headers: { Accept: "application/json" },
      body: new FormData(form),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "The files could not be submitted.");
    window.history.replaceState({}, "", `/?job=${encodeURIComponent(payload.id)}`);
    renderJob(payload);
    statusSection.scrollIntoView({ behavior: "smooth", block: "start" });
    pollJob(payload.status_url);
  } catch (error) {
    showError(formError, error.message);
    submitButton.disabled = false;
  } finally {
    submitButton.querySelector("span").textContent = "Compile my video";
  }
});

menuButton.addEventListener("click", () => {
  const willOpen = menuButton.getAttribute("aria-expanded") !== "true";
  menuButton.setAttribute("aria-expanded", String(willOpen));
  menuPanel.hidden = !willOpen;
});

menuPanel.addEventListener("click", (event) => {
  if (!event.target.closest("a")) return;
  menuButton.setAttribute("aria-expanded", "false");
  menuPanel.hidden = true;
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || menuPanel.hidden) return;
  menuButton.setAttribute("aria-expanded", "false");
  menuPanel.hidden = true;
  menuButton.focus();
});

const initialJobId = document.body.dataset.jobId;
if (initialJobId) pollJob(`/api/jobs/${encodeURIComponent(initialJobId)}`);
