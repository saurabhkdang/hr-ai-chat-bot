import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const examples = [
  "who joined earlier saurabh or shanky",
  "leave balance of saurabh",
  "who is on leave today",
  "show team members of rahul",
];

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const canSubmit = question.trim().length > 0 && !isLoading;

  async function askQuestion(event) {
    event?.preventDefault();
    if (!canSubmit) return;

    setIsLoading(true);
    setError("");
    setAnswer(null);

    try {
      const response = await fetch(`${API_BASE_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: question.trim() }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || "The API returned an error.");
      }

      setAnswer(data);
    } catch (err) {
      setError(err.message || "Unable to reach the HR assistant API.");
    } finally {
      setIsLoading(false);
    }
  }

  function useExample(value) {
    setQuestion(value);
    setAnswer(null);
    setError("");
  }

  return (
    <main className="appShell">
      <section className="workspace">
        <header className="topBar">
          <div>
            <p className="eyebrow">HR AI Assistant</p>
            <h1>Ask employee data and policy questions</h1>
          </div>
          <div className="apiBadge">
            <span className="statusDot" />
            {API_BASE_URL.replace(/^https?:\/\//, "")}
          </div>
        </header>

        <form className="queryPanel" onSubmit={askQuestion}>
          <label htmlFor="question">Prompt</label>
          <div className="promptRow">
            <textarea
              id="question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask something like: who joined earlier saurabh or shanky"
              rows={3}
            />
            <button type="submit" disabled={!canSubmit}>
              {isLoading ? "Asking..." : "Ask"}
            </button>
          </div>
          <div className="examples" aria-label="Example prompts">
            {examples.map((example) => (
              <button key={example} type="button" onClick={() => useExample(example)}>
                {example}
              </button>
            ))}
          </div>
        </form>

        <section className="answerPanel" aria-live="polite">
          {isLoading && <LoadingState />}
          {error && <ErrorState message={error} />}
          {!isLoading && !error && !answer && <EmptyState />}
          {!isLoading && !error && answer && <ResponseRenderer response={answer} />}
        </section>
      </section>
    </main>
  );
}

function EmptyState() {
  return (
    <div className="emptyState">
      <div className="emptyIcon">?</div>
      <h2>Ready for a prompt</h2>
      <p>Your answer will appear here as text, a table, or grouped sections.</p>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="loadingState">
      <div className="spinner" />
      <p>Working through the HR data...</p>
    </div>
  );
}

function ErrorState({ message }) {
  return (
    <div className="errorState">
      <h2>Request failed</h2>
      <p>{message}</p>
    </div>
  );
}

function ResponseRenderer({ response }) {
  if (!response || typeof response !== "object") {
    return <TextBlock title="Response" content={String(response || "")} />;
  }

  if (response.type === "hybrid" && Array.isArray(response.sections)) {
    return (
      <div className="sectionStack">
        {response.sections.map((section, index) => (
          <SectionRenderer key={`${section.type}-${index}`} section={section} />
        ))}
      </div>
    );
  }

  if (response.type === "comparison" && Array.isArray(response.sections)) {
    return (
      <div className="sectionStack">
        {response.sections.map((section, index) => (
          <SectionRenderer key={`${section.type}-${index}`} section={section} />
        ))}
      </div>
    );
  }

  if (response.type === "table") {
    return (
      <div className="sectionStack">
        {response.summary && <TextBlock title="Summary" content={response.summary} />}
        <DataTable columns={response.columns} rows={response.rows} />
      </div>
    );
  }

  return (
    <TextBlock
      title={response.type ? titleCase(response.type) : "Response"}
      content={response.message || response.content || JSON.stringify(response, null, 2)}
    />
  );
}

function SectionRenderer({ section }) {
  if (section.type === "table") {
    return <DataTable title={section.title} columns={section.columns} rows={section.rows} />;
  }

  return (
    <TextBlock
      title={section.title || titleCase(section.type || "Response")}
      content={section.content || section.message || ""}
    />
  );
}

function TextBlock({ title, content }) {
  return (
    <article className="resultBlock">
      <div className="resultHeader">
        <h2>{title}</h2>
      </div>
      <p className="resultText">{content}</p>
    </article>
  );
}

function DataTable({ title = "Result", columns = [], rows = [] }) {
  const normalizedRows = useMemo(() => {
    if (!Array.isArray(rows)) return [];
    return rows.map((row) => (Array.isArray(row) ? row : Object.values(row || {})));
  }, [rows]);

  const normalizedColumns = useMemo(() => {
    if (Array.isArray(columns) && columns.length) return columns;
    if (normalizedRows[0]) return normalizedRows[0].map((_, index) => `Column ${index + 1}`);
    return [];
  }, [columns, normalizedRows]);

  return (
    <article className="resultBlock">
      <div className="resultHeader">
        <h2>{title}</h2>
        <span>{normalizedRows.length} rows</span>
      </div>
      <div className="tableWrap">
        <table>
          <thead>
            <tr>
              {normalizedColumns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {normalizedRows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {normalizedColumns.map((column, columnIndex) => (
                  <td key={`${column}-${columnIndex}`}>{formatCell(row[columnIndex])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
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

createRoot(document.getElementById("root")).render(<App />);
