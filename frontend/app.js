const API_BASE = "http://localhost:8000";

const elements = {
  backendSummary: document.querySelector("#backendSummary"),
  readyPill: document.querySelector("#readyPill"),
  apiState: document.querySelector("#apiState"),
  databaseState: document.querySelector("#databaseState"),
  storageState: document.querySelector("#storageState"),
  refreshStatus: document.querySelector("#refreshStatus"),
  uploadForm: document.querySelector("#uploadForm"),
  fileInput: document.querySelector("#fileInput"),
  fileName: document.querySelector("#fileName"),
  uploadResult: document.querySelector("#uploadResult"),
  chatForm: document.querySelector("#chatForm"),
  chatQuestion: document.querySelector("#chatQuestion"),
  chatTopK: document.querySelector("#chatTopK"),
  chatMessages: document.querySelector("#chatMessages"),
  searchForm: document.querySelector("#searchForm"),
  searchQuery: document.querySelector("#searchQuery"),
  searchTopK: document.querySelector("#searchTopK"),
  searchResults: document.querySelector("#searchResults"),
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setBusy(button, busy) {
  button.disabled = busy;
}

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};

  if (!response.ok) {
    const detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail || data);
    throw new Error(detail);
  }

  return data;
}

async function refreshStatus() {
  elements.apiState.textContent = "...";
  elements.databaseState.textContent = "...";
  elements.storageState.textContent = "...";
  elements.readyPill.textContent = "...";
  elements.readyPill.className = "status-pill";

  try {
    const health = await requestJson("/health");
    const ready = await requestJson("/ready");
    elements.backendSummary.textContent = `${health.status} · ${health.env} · v${health.version}`;
    elements.apiState.textContent = "healthy";
    elements.databaseState.textContent = ready.database;
    elements.storageState.textContent = ready.storage;
    elements.readyPill.textContent = "ready";
    elements.readyPill.classList.add("ready");
  } catch (error) {
    elements.backendSummary.textContent = error.message;
    elements.apiState.textContent = "erro";
    elements.databaseState.textContent = "-";
    elements.storageState.textContent = "-";
    elements.readyPill.textContent = "offline";
    elements.readyPill.classList.add("fail");
  }
}

function renderUploadResult(data) {
  elements.uploadResult.innerHTML = `
    <p class="success">Documento indexado.</p>
    <p><strong>${escapeHtml(data.filename)}</strong></p>
    <p>${data.chunks_count} chunks · ${escapeHtml(data.document_id)}</p>
  `;
}

function renderError(target, message) {
  target.innerHTML = `<p class="error">${escapeHtml(message)}</p>`;
}

function addMessage(role, title, content, sources = []) {
  const node = document.createElement("article");
  node.className = `message ${role}`;
  const sourceHtml = sources.length
    ? `<div class="source-list">${sources
        .map(
          (source) => `
            <div class="source-item">
              [${source.index}] ${escapeHtml(source.file_name)} · score ${Number(source.score).toFixed(3)}
            </div>
          `,
        )
        .join("")}</div>`
    : "";

  node.innerHTML = `
    <h3>${escapeHtml(title)}</h3>
    <p>${escapeHtml(content)}</p>
    ${sourceHtml}
  `;
  elements.chatMessages.appendChild(node);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function renderSearchResults(results) {
  if (!results.length) {
    elements.searchResults.innerHTML = '<div class="result-item"><p>Nenhum trecho encontrado.</p></div>';
    return;
  }

  elements.searchResults.innerHTML = results
    .map(
      (item) => `
        <article class="result-item">
          <h3>${escapeHtml(item.file_name)}</h3>
          <div class="meta-line">
            <span>score ${Number(item.score).toFixed(3)}</span>
            <span>${escapeHtml(item.chunk_id)}</span>
          </div>
          <p>${escapeHtml(item.content)}</p>
        </article>
      `,
    )
    .join("");
}

elements.fileInput.addEventListener("change", () => {
  const file = elements.fileInput.files[0];
  elements.fileName.textContent = file ? file.name : "Selecionar documento";
});

elements.uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  const file = elements.fileInput.files[0];

  if (!file) {
    renderError(elements.uploadResult, "Selecione um documento.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  setBusy(button, true);
  elements.uploadResult.innerHTML = "<p>Enviando...</p>";

  try {
    const data = await requestJson("/upload", {
      method: "POST",
      body: formData,
    });
    renderUploadResult(data);
  } catch (error) {
    renderError(elements.uploadResult, error.message);
  } finally {
    setBusy(button, false);
  }
});

elements.searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  const query = elements.searchQuery.value.trim();
  const topK = Number(elements.searchTopK.value || 5);

  if (!query) {
    renderError(elements.searchResults, "Digite uma busca.");
    return;
  }

  setBusy(button, true);
  elements.searchResults.innerHTML = '<div class="result-item"><p>Buscando...</p></div>';

  try {
    const data = await requestJson("/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: topK }),
    });
    renderSearchResults(data.results);
  } catch (error) {
    renderError(elements.searchResults, error.message);
  } finally {
    setBusy(button, false);
  }
});

elements.chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  const question = elements.chatQuestion.value.trim();
  const topK = Number(elements.chatTopK.value || 5);

  if (!question) {
    return;
  }

  addMessage("user", "Pergunta", question);
  elements.chatQuestion.value = "";
  setBusy(button, true);

  try {
    const data = await requestJson("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k: topK }),
    });
    addMessage("assistant", "Resposta", data.answer, data.sources);
  } catch (error) {
    addMessage("assistant", "Erro", error.message);
  } finally {
    setBusy(button, false);
  }
});

document.querySelectorAll(".tab-button").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab-button").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    document.querySelector(`#${button.dataset.tab}`).classList.add("active");
  });
});

elements.refreshStatus.addEventListener("click", refreshStatus);
refreshStatus();
