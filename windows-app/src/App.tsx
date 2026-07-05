import {
  Activity,
  AlertTriangle,
  Bot,
  CalendarDays,
  CircleStop,
  Database,
  FileText,
  MapPinned,
  MonitorCog,
  Play,
  Radio,
  RefreshCcw,
  Route,
  Settings,
  Sparkles,
  StepForward,
  UploadCloud,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const localApiUrl = import.meta.env.VITE_LOCAL_API_URL ?? "http://127.0.0.1:8765";

type WorkflowState = {
  clientId?: string;
  eventId?: string;
  assetId?: string;
  scriptId?: string;
  scenarioId?: string;
  runId?: string;
  robotId: string;
};

type ApiStatus = "checking" | "online" | "offline";

async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${localApiUrl}${path}`, {
    headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : `HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");
  const [workflow, setWorkflow] = useState<WorkflowState>({ robotId: "X2U-001" });
  const [messages, setMessages] = useState<string[]>([]);
  const [logs, setLogs] = useState<Array<{ log_id: string; type: string; message: string }>>([]);
  const [busyAction, setBusyAction] = useState<string | null>(null);

  const workflowReady = useMemo(
    () => Boolean(workflow.eventId && workflow.scenarioId && workflow.runId),
    [workflow.eventId, workflow.runId, workflow.scenarioId],
  );

  useEffect(() => {
    void checkApi();
  }, []);

  function pushMessage(message: string) {
    setMessages((current) => [message, ...current].slice(0, 8));
  }

  async function runAction(label: string, action: () => Promise<void>) {
    setBusyAction(label);
    try {
      await action();
    } catch (error) {
      pushMessage(`${label}: ${error instanceof Error ? error.message : "failed"}`);
    } finally {
      setBusyAction(null);
    }
  }

  async function checkApi() {
    await runAction("API check", async () => {
      const health = await apiRequest<{ status: string; service: string }>("/health");
      setApiStatus(health.status === "ok" ? "online" : "offline");
      pushMessage(`API online: ${health.service}`);
    }).catch(() => {
      setApiStatus("offline");
    });
  }

  async function createDemoSetup() {
    await runAction("Create demo setup", async () => {
      const client = await apiRequest<{ client_id: string }>("/clients", {
        method: "POST",
        body: JSON.stringify({ name: "ABC Tech", contact_name: "Event Manager" }),
      });
      const event = await apiRequest<{ event_id: string }>("/events", {
        method: "POST",
        body: JSON.stringify({
          client_id: client.client_id,
          name: "ABC Product Launch",
          robot_id: workflow.robotId,
          language: "zh-CN",
        }),
      });
      await apiRequest("/licenses", {
        method: "POST",
        body: JSON.stringify({
          event_id: event.event_id,
          robot_id: workflow.robotId,
          license_type: "weekly",
          start_date: "2026-07-01",
          end_date: "2026-07-07",
        }),
      });
      const asset = await apiRequest<{ asset_id: string }>(`/events/${event.event_id}/assets`, {
        method: "POST",
        body: JSON.stringify({
          asset_type: "video",
          name: "product_a.mp4",
          uri: "local://assets/product_a.mp4",
          mime_type: "video/mp4",
        }),
      });
      const script = await apiRequest<{ script_id: string }>(`/events/${event.event_id}/scripts`, {
        method: "POST",
        body: JSON.stringify({
          name: "Product A Intro",
          language: "zh-CN",
          content: "大家好，接下来为您介绍我们的核心产品。",
        }),
      });
      setWorkflow((current) => ({
        ...current,
        clientId: client.client_id,
        eventId: event.event_id,
        assetId: asset.asset_id,
        scriptId: script.script_id,
      }));
      pushMessage(`Demo setup ready for event ${event.event_id}`);
    });
  }

  async function publishScenario() {
    await runAction("Publish scenario", async () => {
      if (!workflow.eventId || !workflow.assetId || !workflow.scriptId) {
        throw new Error("create demo setup first");
      }
      const scenario = await apiRequest<{ scenario_id: string }>(
        `/events/${workflow.eventId}/scenarios/publish`,
        {
          method: "POST",
          body: JSON.stringify({
            template_id: "product_presenter",
            name: "Product Presenter Main Flow",
            config: {
              product_name: "Product A",
              screen_asset_id: workflow.assetId,
              intro_script_id: workflow.scriptId,
              motion_id: "right_hand_raise",
            },
          }),
        },
      );
      const run = await apiRequest<{ run_id: string }>("/runs", {
        method: "POST",
        body: JSON.stringify({
          event_id: workflow.eventId,
          scenario_id: scenario.scenario_id,
          robot_id: workflow.robotId,
        }),
      });
      setWorkflow((current) => ({ ...current, scenarioId: scenario.scenario_id, runId: run.run_id }));
      pushMessage(`Scenario published: ${scenario.scenario_id}`);
    });
  }

  async function controlRun(action: "start" | "next" | "replay" | "stop") {
    await runAction(`Run ${action}`, async () => {
      if (!workflow.runId) {
        throw new Error("publish scenario first");
      }
      const run = await apiRequest<{ status: string; current_step_id?: string }>(
        `/runs/${workflow.runId}/${action}`,
        { method: "POST" },
      );
      pushMessage(`Run ${run.status}: ${run.current_step_id ?? action}`);
      await loadLogs();
    });
  }

  async function emergencyStop() {
    await runAction("Emergency stop", async () => {
      const result = await apiRequest<{ safety_state: string }>("/safety/emergency-stop", {
        method: "POST",
        body: JSON.stringify({ robot_id: workflow.robotId }),
      });
      pushMessage(`Safety state: ${result.safety_state}`);
    });
  }

  async function resetSafety() {
    await runAction("Safety reset", async () => {
      const result = await apiRequest<{ safety_state: string }>("/safety/reset", {
        method: "POST",
        body: JSON.stringify({ robot_id: workflow.robotId }),
      });
      pushMessage(`Safety state: ${result.safety_state}`);
    });
  }

  async function runExtensionDemo(kind: "rag" | "movement" | "docking" | "status") {
    await runAction(kind, async () => {
      if (kind === "rag") {
        const result = await apiRequest<{ draft: string }>("/rag/product-intros", {
          method: "POST",
          body: JSON.stringify({
            product_name: "X2 Ultra",
            language: "en",
            duration_seconds: 30,
            materials: "Humanoid service robot for reception, product demos, and event hosting.",
          }),
        });
        pushMessage(`RAG draft: ${result.draft.slice(0, 80)}...`);
      }
      if (kind === "movement") {
        const result = await apiRequest<{ status: string; total_distance_m: number }>(
          "/movement/scripts/simulate",
          {
            method: "POST",
            body: JSON.stringify({
              robot_id: workflow.robotId,
              script: [{ type: "forward", distance_m: 1.2 }],
            }),
          },
        );
        pushMessage(`Movement ${result.status}: ${result.total_distance_m}m`);
      }
      if (kind === "docking") {
        const result = await apiRequest<{ status: string; marker_id: number }>(
          "/visual-marker/docking/simulate",
          {
            method: "POST",
            body: JSON.stringify({ robot_id: workflow.robotId, marker_id: 3, stop_distance_m: 0.5 }),
          },
        );
        pushMessage(`Docking ${result.status}: marker ${result.marker_id}`);
      }
      if (kind === "status") {
        const result = await apiRequest<{ online: boolean; battery_percent: number }>(
          `/robots/${workflow.robotId}/status`,
        );
        pushMessage(`Robot ${result.online ? "online" : "offline"}, battery ${result.battery_percent}%`);
      }
    });
  }

  async function loadLogs() {
    await runAction("Load logs", async () => {
      if (!workflow.eventId) {
        throw new Error("create demo setup first");
      }
      const result = await apiRequest<Array<{ log_id: string; type: string; message: string }>>(
        `/events/${workflow.eventId}/logs`,
      );
      setLogs(result.slice(-10).reverse());
      pushMessage(`Loaded ${result.length} logs`);
    });
  }

  const disabled = busyAction !== null || apiStatus !== "online";

  return (
    <main className="app-shell">
      <section className="top-bar" aria-label="Application status">
        <div>
          <p className="eyebrow">X2 Rental Scenario Platform</p>
          <h1>Desktop Control Center</h1>
        </div>
        <div className={`api-status ${apiStatus}`}>
          <Radio size={18} aria-hidden="true" />
          <span>{apiStatus === "checking" ? "Checking local API" : `${localApiUrl} ${apiStatus}`}</span>
          <button className="icon-button" type="button" title="Refresh API status" onClick={checkApi}>
            <RefreshCcw size={16} aria-hidden="true" />
          </button>
        </div>
      </section>

      <section className="mode-grid" aria-label="Application modes">
        <article className="mode-card">
          <div className="mode-heading">
            <Settings size={24} aria-hidden="true" />
            <div>
              <h2>Admin Setup</h2>
              <p>Create a demo client, event, weekly license, asset, script, and Product Presenter scenario.</p>
            </div>
          </div>
          <div className="action-grid">
            <button className="tool-button" type="button" disabled={disabled} onClick={createDemoSetup}>
              <Database size={20} aria-hidden="true" />
              <span>Demo Setup</span>
            </button>
            <button
              className="tool-button"
              type="button"
              disabled={disabled || !workflow.eventId}
              onClick={publishScenario}
            >
              <UploadCloud size={20} aria-hidden="true" />
              <span>Publish Flow</span>
            </button>
            <button className="tool-button" type="button" disabled={disabled} onClick={() => runExtensionDemo("rag")}>
              <Sparkles size={20} aria-hidden="true" />
              <span>RAG Draft</span>
            </button>
            <button className="tool-button" type="button" disabled={disabled || !workflow.eventId} onClick={loadLogs}>
              <FileText size={20} aria-hidden="true" />
              <span>View Logs</span>
            </button>
          </div>
        </article>

        <article className="mode-card operator">
          <div className="mode-heading">
            <MonitorCog size={24} aria-hidden="true" />
            <div>
              <h2>Operator Console</h2>
              <p>Run the live scenario through controlled steps and keep emergency controls available.</p>
            </div>
          </div>
          <div className="action-grid">
            <button className="tool-button" type="button" disabled={disabled || !workflowReady} onClick={() => controlRun("start")}>
              <Play size={20} aria-hidden="true" />
              <span>Start</span>
            </button>
            <button className="tool-button" type="button" disabled={disabled || !workflowReady} onClick={() => controlRun("next")}>
              <StepForward size={20} aria-hidden="true" />
              <span>Next Step</span>
            </button>
            <button className="tool-button" type="button" disabled={disabled || !workflowReady} onClick={() => controlRun("replay")}>
              <RefreshCcw size={20} aria-hidden="true" />
              <span>Replay</span>
            </button>
            <button className="tool-button" type="button" disabled={disabled || !workflowReady} onClick={() => controlRun("stop")}>
              <CircleStop size={20} aria-hidden="true" />
              <span>Stop</span>
            </button>
            <button className="tool-button warning" type="button" disabled={disabled} onClick={emergencyStop}>
              <AlertTriangle size={20} aria-hidden="true" />
              <span>Emergency</span>
            </button>
            <button className="tool-button" type="button" disabled={disabled} onClick={resetSafety}>
              <Activity size={20} aria-hidden="true" />
              <span>Reset Safety</span>
            </button>
          </div>
        </article>
      </section>

      <section className="extension-grid" aria-label="Extensions and logs">
        <article className="compact-panel">
          <h2>Extensions</h2>
          <div className="toolbar-row">
            <button className="tool-button" type="button" disabled={disabled} onClick={() => runExtensionDemo("status")}>
              <Bot size={18} aria-hidden="true" />
              <span>Status</span>
            </button>
            <button className="tool-button" type="button" disabled={disabled} onClick={() => runExtensionDemo("movement")}>
              <Route size={18} aria-hidden="true" />
              <span>Move</span>
            </button>
            <button className="tool-button" type="button" disabled={disabled} onClick={() => runExtensionDemo("docking")}>
              <MapPinned size={18} aria-hidden="true" />
              <span>Dock</span>
            </button>
          </div>
          <dl className="state-list">
            <div>
              <dt>Client</dt>
              <dd>{workflow.clientId ?? "-"}</dd>
            </div>
            <div>
              <dt>Event</dt>
              <dd>{workflow.eventId ?? "-"}</dd>
            </div>
            <div>
              <dt>Scenario</dt>
              <dd>{workflow.scenarioId ?? "-"}</dd>
            </div>
            <div>
              <dt>Run</dt>
              <dd>{workflow.runId ?? "-"}</dd>
            </div>
          </dl>
        </article>

        <article className="compact-panel">
          <h2>Activity</h2>
          <div className="message-list">
            {(messages.length ? messages : ["No activity yet."]).map((message, index) => (
              <p key={`${message}-${index}`}>{message}</p>
            ))}
          </div>
        </article>

        <article className="compact-panel logs-panel">
          <h2>Logs</h2>
          <div className="message-list">
            {(logs.length ? logs : []).map((log) => (
              <p key={log.log_id}>
                <strong>{log.type}</strong> {log.message}
              </p>
            ))}
            {!logs.length && <p>Run a scenario, then load logs.</p>}
          </div>
        </article>
      </section>
      {busyAction && <div className="busy-indicator">{busyAction}</div>}
    </main>
  );
}

export default App;
