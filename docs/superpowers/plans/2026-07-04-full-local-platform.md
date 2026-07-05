# Full Local Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete locally testable Windows desktop version of the X2 rental platform using mockable adapters for hardware, RAG, movement, and visual docking.

**Architecture:** The local FastAPI service owns business state, event configuration, templates, scenario execution, safety validation, mock robot commands, logs, RAG draft generation, movement scripts, and visual docking simulations. The Windows app is a desktop control surface that calls the local API and exposes Admin Setup plus Operator Console workflows. Real X2/RAG/hardware integrations remain isolated behind adapter-shaped local endpoints so they can be replaced without changing business flows.

**Tech Stack:** Python 3.10, FastAPI, Pydantic, pytest, React, TypeScript, Vite, Tauri.

---

### Task 1: API Contract Tests

**Files:**
- Create: `local-api/tests/test_platform_workflow.py`
- Create: `local-api/tests/test_robot_runtime.py`

- [ ] **Step 1: Write workflow tests**

Cover:
- Create client.
- Create event.
- Create active license.
- Upload asset metadata.
- Create script.
- List templates.
- Publish Product Presenter scenario.
- Start run.
- Advance next step.
- Confirm command logs.

- [ ] **Step 2: Write runtime tests**

Cover:
- Expired license blocks robot execution.
- Emergency stop blocks movement.
- Mock robot command returns command receipt.
- RAG draft generation requires product material.
- Movement script returns simulated completion.
- Visual docking returns simulated marker completion.

- [ ] **Step 3: Verify tests fail before implementation**

Run:

```powershell
.\.venv\Scripts\python -m pytest local-api\tests -q
```

Expected before implementation: new tests fail on missing routes.

---

### Task 2: Local API Implementation

**Files:**
- Create: `local-api/app/platform.py`
- Create: `local-api/app/templates.py`
- Modify: `local-api/app/main.py`

- [ ] **Step 1: Implement in-memory state**

State collections:
- clients
- events
- licenses
- assets
- scripts
- scenario_versions
- runs
- robot_commands
- logs
- robot_status

- [ ] **Step 2: Implement business endpoints**

Endpoints:
- `POST /clients`
- `GET /clients`
- `POST /events`
- `GET /events`
- `POST /events/{event_id}/copy`
- `POST /licenses`
- `GET /licenses/{event_id}/status`

- [ ] **Step 3: Implement asset and script endpoints**

Endpoints:
- `POST /events/{event_id}/assets`
- `GET /events/{event_id}/assets`
- `POST /events/{event_id}/scripts`
- `GET /events/{event_id}/scripts`

- [ ] **Step 4: Implement templates and scenario runtime**

Endpoints:
- `GET /templates`
- `GET /templates/{template_id}`
- `POST /events/{event_id}/scenarios/publish`
- `POST /runs`
- `GET /runs/{run_id}`
- `POST /runs/{run_id}/start`
- `POST /runs/{run_id}/next`
- `POST /runs/{run_id}/previous`
- `POST /runs/{run_id}/replay`
- `POST /runs/{run_id}/stop`

- [ ] **Step 5: Implement safety and mock robot runtime**

Endpoints:
- `GET /robots/{robot_id}/status`
- `POST /robots/{robot_id}/commands`
- `POST /safety/emergency-stop`
- `POST /safety/reset`

- [ ] **Step 6: Implement extension endpoints**

Endpoints:
- `POST /rag/product-intros`
- `POST /faq/answer`
- `POST /movement/scripts/simulate`
- `POST /visual-marker/docking/simulate`
- `GET /events/{event_id}/logs`

- [ ] **Step 7: Verify API tests pass**

Run:

```powershell
.\.venv\Scripts\python -m pytest local-api\tests -q
```

Expected: all API tests pass.

---

### Task 3: Windows App Workflow UI

**Files:**
- Modify: `windows-app/src/App.tsx`
- Modify: `windows-app/src/App.css`

- [ ] **Step 1: Add API client helpers**

Use fetch calls against `http://127.0.0.1:8765`.

- [ ] **Step 2: Add Admin Setup workflow**

Controls:
- Create demo client/event/license.
- List templates.
- Publish Product Presenter scenario.

- [ ] **Step 3: Add Operator Console workflow**

Controls:
- Start run.
- Next step.
- Replay.
- Stop.
- Emergency stop.
- Robot status.

- [ ] **Step 4: Add extension panels**

Controls:
- Generate RAG product intro.
- Simulate movement script.
- Simulate visual docking.
- View logs.

- [ ] **Step 5: Verify frontend build**

Run:

```powershell
cd windows-app
npm run build
```

Expected: build succeeds.

---

### Task 4: Full Verification

**Files:**
- Read: all changed files

- [ ] **Step 1: Run API tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest local-api\tests -q
```

- [ ] **Step 2: Run frontend build**

Run:

```powershell
cd windows-app
npm run build
```

- [ ] **Step 3: Run Tauri installer build**

Run:

```powershell
.\scripts\build-windows-app.ps1
```

- [ ] **Step 4: Confirm installer exists**

Expected:

```text
windows-app\src-tauri\target\release\bundle\nsis\X2 Rental Platform_0.1.0_x64-setup.exe
```
