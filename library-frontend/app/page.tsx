"use client";

import { useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, Database, Loader2, Play, Server } from "lucide-react";
import { Operation, OperationField, callOperation, operations } from "../lib/api";
import { PlainRecord, formatResult, getApiBaseUrl } from "../lib/protobuf";

type Status = "idle" | "loading" | "success" | "error";

const groups = ["Authors", "Books", "Members", "Loans", "Fines", "Stats"] as const;

function initialValues(operation: Operation): PlainRecord {
  const values: PlainRecord = {};
  for (const field of operation.fields) {
    values[field.name] = field.defaultValue ?? (field.type === "checkbox" ? false : "");
  }

  const dueDate = operation.fields.find((field) => field.name === "due_date");
  if (dueDate) {
    const date = new Date(Date.now() + 14 * 24 * 60 * 60 * 1000);
    values.due_date = date.toISOString().slice(0, 16);
  }

  return values;
}

export default function Home() {
  const [selectedGroup, setSelectedGroup] = useState<(typeof groups)[number]>("Authors");
  const visibleOperations = useMemo(
    () => operations.filter((operation) => operation.group === selectedGroup),
    [selectedGroup]
  );
  const [selectedOperationId, setSelectedOperationId] = useState(visibleOperations[0].id);
  const selectedOperation =
    operations.find((operation) => operation.id === selectedOperationId) ?? visibleOperations[0];
  const [values, setValues] = useState<PlainRecord>(() => initialValues(selectedOperation));
  const [status, setStatus] = useState<Status>("idle");
  const [output, setOutput] = useState("Choose an operation, enter clear text values, then run it.");

  function selectGroup(group: (typeof groups)[number]) {
    const firstOperation = operations.find((operation) => operation.group === group)!;
    setSelectedGroup(group);
    setSelectedOperationId(firstOperation.id);
    setValues(initialValues(firstOperation));
    setStatus("idle");
    setOutput("Choose an operation, enter clear text values, then run it.");
  }

  function selectOperation(operation: Operation) {
    setSelectedOperationId(operation.id);
    setValues(initialValues(operation));
    setStatus("idle");
    setOutput("Ready.");
  }

  function updateValue(field: OperationField, value: string | boolean) {
    setValues((current) => ({ ...current, [field.name]: value }));
  }

  async function runOperation() {
    setStatus("loading");
    setOutput("Sending protobuf request...");

    try {
      const result = await callOperation(selectedOperation, values);
      setStatus("success");
      setOutput(formatResult(result));
    } catch (error) {
      setStatus("error");
      setOutput(error instanceof Error ? error.message : String(error));
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <h1>Neighborhood Library Service</h1>
          <p>Clear text forms in the browser, protobuf payloads on the wire.</p>
        </div>
        <div className="server-pill" title="Backend API base URL">
          <Server size={18} />
          <span>{getApiBaseUrl()}</span>
        </div>
      </header>

      <section className="workspace">
        <aside className="sidebar" aria-label="API groups">
          <div className="sidebar-title">
            <Database size={18} />
            <span>REST APIs</span>
          </div>
          <div className="tabs">
            {groups.map((group) => (
              <button
                key={group}
                type="button"
                className={group === selectedGroup ? "tab active" : "tab"}
                onClick={() => selectGroup(group)}
              >
                {group}
              </button>
            ))}
          </div>
          <div className="operation-list">
            {visibleOperations.map((operation) => (
              <button
                key={operation.id}
                type="button"
                className={operation.id === selectedOperation.id ? "operation active" : "operation"}
                onClick={() => selectOperation(operation)}
              >
                <span>{operation.label}</span>
                <small>{operation.method}</small>
              </button>
            ))}
          </div>
        </aside>

        <section className="panel" aria-label="Request form">
          <div className="panel-heading">
            <div>
              <h2>{selectedOperation.label}</h2>
              <p>
                {selectedOperation.method} {selectedOperation.path}
              </p>
            </div>
            <button
              type="button"
              className="run-button"
              onClick={runOperation}
              disabled={status === "loading" || Boolean(selectedOperation.disabledReason)}
              title="Send protobuf request"
            >
              {status === "loading" ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
              <span>Run</span>
            </button>
          </div>

          {selectedOperation.disabledReason ? (
            <div className="notice error">
              <AlertCircle size={18} />
              <span>{selectedOperation.disabledReason}</span>
            </div>
          ) : null}

          <div className="transport">
            <span>Request body</span>
            <strong>{selectedOperation.requestType ?? "none"}</strong>
            <span>Response body</span>
            <strong>{selectedOperation.responseType ?? "empty"}</strong>
          </div>

          <form className="form" onSubmit={(event) => event.preventDefault()}>
            {selectedOperation.fields.length === 0 ? (
              <p className="empty-form">No input required for this operation.</p>
            ) : (
              selectedOperation.fields.map((field) => (
                <label key={field.name} className={field.type === "checkbox" ? "check-field" : "field"}>
                  <span>{field.label}</span>
                  {field.type === "select" ? (
                    <select
                      value={String(values[field.name] ?? "")}
                      onChange={(event) => updateValue(field, event.target.value)}
                      required={field.required}
                    >
                      {(field.options ?? []).map((option) => (
                        <option key={option || "blank"} value={option}>
                          {option || "Any"}
                        </option>
                      ))}
                    </select>
                  ) : field.type === "checkbox" ? (
                    <input
                      type="checkbox"
                      checked={Boolean(values[field.name])}
                      onChange={(event) => updateValue(field, event.target.checked)}
                    />
                  ) : (
                    <input
                      type={field.type}
                      value={String(values[field.name] ?? "")}
                      placeholder={field.placeholder}
                      onChange={(event) => updateValue(field, event.target.value)}
                      required={field.required}
                    />
                  )}
                  {field.help ? <small>{field.help}</small> : null}
                </label>
              ))
            )}
          </form>
        </section>

        <section className="panel output-panel" aria-label="Response output">
          <div className="panel-heading compact">
            <div>
              <h2>Output</h2>
              <p>Decoded protobuf response shown as clear text.</p>
            </div>
            <StatusBadge status={status} />
          </div>
          <pre className="output">{output}</pre>
        </section>
      </section>
    </main>
  );
}

function StatusBadge({ status }: { status: Status }) {
  if (status === "success") {
    return (
      <span className="status success">
        <CheckCircle2 size={16} />
        OK
      </span>
    );
  }

  if (status === "error") {
    return (
      <span className="status error">
        <AlertCircle size={16} />
        Error
      </span>
    );
  }

  if (status === "loading") {
    return (
      <span className="status loading">
        <Loader2 className="spin" size={16} />
        Running
      </span>
    );
  }

  return <span className="status">Idle</span>;
}
