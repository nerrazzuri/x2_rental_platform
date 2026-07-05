# Windows Desktop Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the platform direction from web-first to a Windows desktop application foundation with a local Python API and a desktop-ready React UI.

**Architecture:** The Windows app owns the operator UI and talks to a local FastAPI service over HTTP. The local API owns health checks, app mode state, and future access to scenario runtime, safety, and robot adapter modules. Tauri is the target packaging shell, but this machine currently lacks Rust/Cargo, so the first pass creates a Tauri-ready structure and verifies the API plus React build.

**Tech Stack:** Python 3.10, FastAPI, pytest, Node 22, React, TypeScript, Vite, Tauri configuration.

---

### Task 1: Update Architecture Documentation

**Files:**
- Modify: `X2_Rental_Platform_Development_Modules.md`
- Create: `README.md`

- [ ] **Step 1: Update module architecture language**

Replace web-first references with Windows desktop wording:

```text
Windows App UI
↓
Local Python API
↓
Scenario Engine / Safety Controller
↓
Robot Adapter
↓
X2 AimDK / ROS2
```

- [ ] **Step 2: Add README quick start**

Create `README.md` with commands:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r local-api\requirements-dev.txt
.\.venv\Scripts\python -m pytest local-api\tests -q
cd windows-app
npm install
npm run build
```

- [ ] **Step 3: Verify docs have no placeholders**

Run:

```powershell
rg -n "T[B]D|T[O]DO|待[定]|占[位]|以[后]补|未[定义]" README.md X2_Rental_Platform_Development_Modules.md
```

Expected: no matches.

---

### Task 2: Local API Health Contract

**Files:**
- Create: `local-api/requirements.txt`
- Create: `local-api/requirements-dev.txt`
- Create: `local-api/app/__init__.py`
- Create: `local-api/app/main.py`
- Create: `local-api/tests/test_health.py`

- [ ] **Step 1: Write the failing health test**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_desktop_local_api_identity():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "x2-local-api",
        "mode": "windows-desktop",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
.\.venv\Scripts\python -m pytest local-api\tests\test_health.py -q
```

Expected before implementation: FAIL because `app.main` does not exist.

- [ ] **Step 3: Write minimal FastAPI implementation**

```python
from fastapi import FastAPI

app = FastAPI(title="X2 Rental Local API")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "x2-local-api",
        "mode": "windows-desktop",
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
.\.venv\Scripts\python -m pytest local-api\tests\test_health.py -q
```

Expected: `1 passed`.

---

### Task 3: Local API App Mode Contract

**Files:**
- Modify: `local-api/app/main.py`
- Create: `local-api/tests/test_app_mode.py`

- [ ] **Step 1: Write failing app mode test**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_get_app_mode_defaults_to_admin():
    client = TestClient(app)

    response = client.get("/app-mode")

    assert response.status_code == 200
    assert response.json() == {
        "mode": "admin",
        "available_modes": ["admin", "operator"],
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
.\.venv\Scripts\python -m pytest local-api\tests\test_app_mode.py -q
```

Expected before implementation: FAIL with 404 for `/app-mode`.

- [ ] **Step 3: Add minimal endpoint**

```python
@app.get("/app-mode")
def app_mode():
    return {
        "mode": "admin",
        "available_modes": ["admin", "operator"],
    }
```

- [ ] **Step 4: Run all API tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest local-api\tests -q
```

Expected: `2 passed`.

---

### Task 4: Windows App React Shell

**Files:**
- Create: `windows-app/package.json`
- Create: `windows-app/index.html`
- Create: `windows-app/tsconfig.json`
- Create: `windows-app/tsconfig.node.json`
- Create: `windows-app/vite.config.ts`
- Create: `windows-app/src/main.tsx`
- Create: `windows-app/src/App.tsx`
- Create: `windows-app/src/App.css`

- [ ] **Step 1: Create React shell**

The first screen contains two modes:

```text
Admin Setup
Operator Console
```

It also shows local API target:

```text
http://127.0.0.1:8765
```

- [ ] **Step 2: Install frontend dependencies**

Run:

```powershell
cd windows-app
npm install
```

Expected: dependencies installed and `windows-app/package-lock.json` created.

- [ ] **Step 3: Build frontend**

Run:

```powershell
cd windows-app
npm run build
```

Expected: Vite build succeeds.

---

### Task 5: Tauri Packaging Metadata

**Files:**
- Create: `windows-app/src-tauri/tauri.conf.json`

- [ ] **Step 1: Add Tauri config**

Use app identifier:

```text
com.x2rental.desktop
```

Set dev URL:

```text
http://localhost:5173
```

Set dist dir:

```text
../dist
```

- [ ] **Step 2: Record current build limitation**

Add README note:

```text
Tauri packaging requires Rust/Cargo. This machine currently does not have Cargo installed, so frontend build is verified first and `.exe` packaging is a follow-up environment step.
```

---

### Task 6: Verification

**Files:**
- Read: all files changed in this plan

- [ ] **Step 1: Verify API tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest local-api\tests -q
```

Expected: all tests pass.

- [ ] **Step 2: Verify frontend build**

Run:

```powershell
cd windows-app
npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Verify repository status**

Run:

```powershell
git status --short
```

Expected: only intentional project files are untracked or modified.
