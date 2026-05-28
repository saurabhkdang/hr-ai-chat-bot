(function () {
  const currentScript = document.currentScript;
  const apiBaseUrl = currentScript?.dataset.apiBaseUrl || "http://localhost:8000";
  const widgetTitle = currentScript?.dataset.title || "HR Assistant";
  const widgetSubtitle = currentScript?.dataset.subtitle || "Ask employee or policy questions";

  const styles = `
    .hrcw-root, .hrcw-root * {
      box-sizing: border-box;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }

    .hrcw-root {
      position: fixed;
      right: 22px;
      bottom: 22px;
      z-index: 2147483000;
      color: #172026;
    }

    .hrcw-launcher {
      width: 62px;
      height: 62px;
      border: 0;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background: #177e89;
      color: white;
      box-shadow: 0 18px 46px rgba(18, 66, 72, 0.28);
      cursor: pointer;
      transition: transform 160ms ease, background 160ms ease;
    }

    .hrcw-launcher:hover {
      transform: translateY(-2px);
      background: #116974;
    }

    .hrcw-launcher svg {
      width: 29px;
      height: 29px;
    }

    .hrcw-panel {
      position: absolute;
      right: 0;
      bottom: 78px;
      width: 390px;
      max-width: calc(100vw - 32px);
      height: min(620px, calc(100vh - 120px));
      display: none;
      grid-template-rows: auto 1fr auto;
      overflow: hidden;
      border: 1px solid #d3dddf;
      border-radius: 8px;
      background: #f8fbfb;
      box-shadow: 0 24px 70px rgba(20, 39, 46, 0.22);
    }

    .hrcw-root.hrcw-open .hrcw-panel {
      display: grid;
    }

    .hrcw-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 16px;
      background: #ffffff;
      border-bottom: 1px solid #dce6e8;
    }

    .hrcw-title {
      margin: 0;
      color: #172026;
      font-size: 16px;
      font-weight: 800;
      line-height: 1.2;
    }

    .hrcw-subtitle {
      margin: 3px 0 0;
      color: #63767d;
      font-size: 12px;
      line-height: 1.35;
    }

    .hrcw-close {
      width: 34px;
      height: 34px;
      display: grid;
      place-items: center;
      flex: 0 0 auto;
      border: 1px solid #d7e1e3;
      border-radius: 8px;
      background: #f7fafb;
      color: #4d6168;
      cursor: pointer;
      font-size: 22px;
      line-height: 1;
    }

    .hrcw-messages {
      min-height: 0;
      overflow-y: auto;
      padding: 16px;
    }

    .hrcw-message {
      display: grid;
      gap: 8px;
      margin-bottom: 14px;
    }

    .hrcw-bubble {
      max-width: 92%;
      padding: 11px 12px;
      border-radius: 8px;
      font-size: 14px;
      line-height: 1.45;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .hrcw-message-user {
      justify-items: end;
    }

    .hrcw-message-user .hrcw-bubble {
      color: white;
      background: #177e89;
    }

    .hrcw-message-bot {
      justify-items: start;
    }

    .hrcw-message-bot .hrcw-bubble {
      color: #24353b;
      background: #ffffff;
      border: 1px solid #dce6e8;
    }

    .hrcw-section {
      width: 100%;
      max-width: 100%;
      overflow: hidden;
      border: 1px solid #dce6e8;
      border-radius: 8px;
      background: #ffffff;
    }

    .hrcw-section-title {
      margin: 0;
      padding: 10px 12px;
      border-bottom: 1px solid #e4ecee;
      color: #23343a;
      font-size: 13px;
      font-weight: 800;
    }

    .hrcw-section-content {
      margin: 0;
      padding: 11px 12px;
      color: #2d4148;
      font-size: 14px;
      line-height: 1.5;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .hrcw-table-wrap {
      width: 100%;
      overflow-x: auto;
    }

    .hrcw-table {
      width: 100%;
      min-width: 320px;
      border-collapse: collapse;
      font-size: 12px;
    }

    .hrcw-table th,
    .hrcw-table td {
      padding: 9px 10px;
      border-bottom: 1px solid #e7eef0;
      text-align: left;
      vertical-align: top;
    }

    .hrcw-table th {
      color: #52666d;
      background: #f5f8f9;
      font-weight: 800;
    }

    .hrcw-composer {
      padding: 12px;
      border-top: 1px solid #dce6e8;
      background: #ffffff;
    }

    .hrcw-form {
      display: grid;
      grid-template-columns: 1fr 42px;
      gap: 8px;
    }

    .hrcw-input {
      width: 100%;
      min-height: 42px;
      max-height: 110px;
      resize: none;
      border: 1px solid #cad8db;
      border-radius: 8px;
      padding: 10px 12px;
      color: #172026;
      background: #fbfdfd;
      font-size: 14px;
      line-height: 1.35;
      outline: none;
    }

    .hrcw-input:focus {
      border-color: #177e89;
      box-shadow: 0 0 0 3px rgba(23, 126, 137, 0.12);
    }

    .hrcw-send {
      width: 42px;
      min-height: 42px;
      border: 0;
      border-radius: 8px;
      display: grid;
      place-items: center;
      color: white;
      background: #177e89;
      cursor: pointer;
    }

    .hrcw-send:disabled {
      cursor: not-allowed;
      opacity: 0.54;
    }

    .hrcw-send svg {
      width: 19px;
      height: 19px;
    }

    .hrcw-typing {
      display: inline-flex;
      gap: 4px;
      align-items: center;
      padding: 10px 12px;
      border: 1px solid #dce6e8;
      border-radius: 8px;
      background: white;
    }

    .hrcw-typing span {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #789098;
      animation: hrcwPulse 900ms ease-in-out infinite;
    }

    .hrcw-typing span:nth-child(2) {
      animation-delay: 140ms;
    }

    .hrcw-typing span:nth-child(3) {
      animation-delay: 280ms;
    }

    @keyframes hrcwPulse {
      0%, 100% { opacity: 0.35; transform: translateY(0); }
      50% { opacity: 1; transform: translateY(-3px); }
    }

    @media (max-width: 520px) {
      .hrcw-root {
        right: 14px;
        bottom: 14px;
      }

      .hrcw-panel {
        right: -2px;
        bottom: 74px;
        width: calc(100vw - 28px);
        height: min(610px, calc(100vh - 104px));
      }
    }
  `;

  injectStyles(styles);

  const root = document.createElement("div");
  root.className = "hrcw-root";
  root.innerHTML = `
    <section class="hrcw-panel" aria-label="${escapeHtml(widgetTitle)} chat panel">
      <header class="hrcw-header">
        <div>
          <h2 class="hrcw-title">${escapeHtml(widgetTitle)}</h2>
          <p class="hrcw-subtitle">${escapeHtml(widgetSubtitle)}</p>
        </div>
        <button class="hrcw-close" type="button" aria-label="Close chat">×</button>
      </header>
      <div class="hrcw-messages"></div>
      <div class="hrcw-composer">
        <form class="hrcw-form">
          <textarea class="hrcw-input" rows="1" placeholder="Ask HR assistant..."></textarea>
          <button class="hrcw-send" type="submit" aria-label="Send question">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M4 12L20 4L16 20L12.5 13.5L4 12Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            </svg>
          </button>
        </form>
      </div>
    </section>
    <button class="hrcw-launcher" type="button" aria-label="Open HR assistant">
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M5 6.5C5 5.12 6.12 4 7.5 4H16.5C17.88 4 19 5.12 19 6.5V13.5C19 14.88 17.88 16 16.5 16H10L5 20V6.5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        <path d="M8 8H16M8 11H13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>
  `;

  document.body.appendChild(root);

  const launcher = root.querySelector(".hrcw-launcher");
  const closeButton = root.querySelector(".hrcw-close");
  const messages = root.querySelector(".hrcw-messages");
  const form = root.querySelector(".hrcw-form");
  const input = root.querySelector(".hrcw-input");
  const sendButton = root.querySelector(".hrcw-send");

  let isLoading = false;

  addBotMessage({
    type: "text",
    message: "Hi, ask me about employee data, attendance, leave balance, or HR policies.",
  });

  launcher.addEventListener("click", () => {
    root.classList.toggle("hrcw-open");
    if (root.classList.contains("hrcw-open")) {
      setTimeout(() => input.focus(), 80);
    }
  });

  closeButton.addEventListener("click", () => {
    root.classList.remove("hrcw-open");
  });

  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 110)}px`;
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = input.value.trim();
    if (!question || isLoading) return;

    addUserMessage(question);
    input.value = "";
    input.style.height = "auto";
    setLoading(true);

    const typingNode = addTyping();

    try {
      const response = await fetch(`${apiBaseUrl}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      const data = await response.json();
      typingNode.remove();

      if (!response.ok) {
        throw new Error(data?.detail || "The assistant API returned an error.");
      }

      addBotMessage(data);
    } catch (error) {
      typingNode.remove();
      addBotMessage({
        type: "text",
        message: error.message || "Unable to reach the assistant right now.",
      });
    } finally {
      setLoading(false);
    }
  });

  function setLoading(value) {
    isLoading = value;
    sendButton.disabled = value;
    input.disabled = value;
  }

  function addUserMessage(text) {
    const wrapper = document.createElement("div");
    wrapper.className = "hrcw-message hrcw-message-user";
    wrapper.innerHTML = `<div class="hrcw-bubble">${escapeHtml(text)}</div>`;
    messages.appendChild(wrapper);
    scrollToBottom();
  }

  function addBotMessage(response) {
    const wrapper = document.createElement("div");
    wrapper.className = "hrcw-message hrcw-message-bot";
    wrapper.appendChild(renderResponse(response));
    messages.appendChild(wrapper);
    scrollToBottom();
  }

  function addTyping() {
    const wrapper = document.createElement("div");
    wrapper.className = "hrcw-message hrcw-message-bot";
    wrapper.innerHTML = `
      <div class="hrcw-typing" aria-label="Assistant is typing">
        <span></span><span></span><span></span>
      </div>
    `;
    messages.appendChild(wrapper);
    scrollToBottom();
    return wrapper;
  }

  function renderResponse(response) {
    if (!response || typeof response !== "object") {
      return bubble(String(response || ""));
    }

    if ((response.type === "hybrid" || response.type === "comparison") && Array.isArray(response.sections)) {
      const container = document.createElement("div");
      container.style.display = "grid";
      container.style.gap = "8px";
      container.style.width = "100%";

      response.sections.forEach((section) => {
        container.appendChild(renderSection(section));
      });

      return container;
    }

    if (response.type === "table") {
      const container = document.createElement("div");
      container.style.display = "grid";
      container.style.gap = "8px";
      container.style.width = "100%";

      if (response.summary) {
        container.appendChild(renderTextSection("Summary", response.summary));
      }

      container.appendChild(renderTableSection("Result", response.columns, response.rows));
      return container;
    }

    return bubble(response.message || response.content || JSON.stringify(response, null, 2));
  }

  function renderSection(section) {
    if (section?.type === "table") {
      return renderTableSection(section.title || "Result", section.columns, section.rows);
    }

    return renderTextSection(
      section?.title || titleCase(section?.type || "Response"),
      section?.content || section?.message || ""
    );
  }

  function renderTextSection(title, content) {
    const section = document.createElement("article");
    section.className = "hrcw-section";
    section.innerHTML = `
      <h3 class="hrcw-section-title">${escapeHtml(title)}</h3>
      <p class="hrcw-section-content">${escapeHtml(content || "-")}</p>
    `;
    return section;
  }

  function renderTableSection(title, columns = [], rows = []) {
    const safeRows = Array.isArray(rows)
      ? rows.map((row) => (Array.isArray(row) ? row : Object.values(row || {})))
      : [];
    const safeColumns = Array.isArray(columns) && columns.length
      ? columns
      : safeRows[0]?.map((_, index) => `Column ${index + 1}`) || [];

    const section = document.createElement("article");
    section.className = "hrcw-section";

    const tableRows = safeRows
      .map((row) => `
        <tr>
          ${safeColumns.map((_, index) => `<td>${escapeHtml(formatCell(row[index]))}</td>`).join("")}
        </tr>
      `)
      .join("");

    section.innerHTML = `
      <h3 class="hrcw-section-title">${escapeHtml(title)}</h3>
      <div class="hrcw-table-wrap">
        <table class="hrcw-table">
          <thead>
            <tr>${safeColumns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr>
          </thead>
          <tbody>${tableRows || `<tr><td colspan="${Math.max(safeColumns.length, 1)}">No rows</td></tr>`}</tbody>
        </table>
      </div>
    `;

    return section;
  }

  function bubble(text) {
    const element = document.createElement("div");
    element.className = "hrcw-bubble";
    element.textContent = text || "-";
    return element;
  }

  function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
  }

  function injectStyles(css) {
    const style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatCell(value) {
    if (value === null || value === undefined || value === "") return "-";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
  }

  function titleCase(value) {
    return String(value)
      .replace(/_/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }
})();
