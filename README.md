# X2 Rental Scenario Platform

Windows desktop foundation for the X2 rental scenario orchestration platform.

## Current Direction

The first product shape is a Windows desktop app, not a browser-first web app.

```text
Windows Desktop App
↓
Local Python API
↓
Scenario Engine / Safety Controller
↓
Robot Adapter
↓
X2 AimDK / ROS2
```

The desktop app contains two modes:

```text
Admin Setup
- Configure clients, events, templates, scripts, assets, and licenses.

Operator Console
- Run the live event flow, control steps, replay, stop, volume, and emergency stop.
```

## Repository Layout

```text
windows-app/
- React + TypeScript desktop UI shell.
- Tauri metadata lives in windows-app/src-tauri.

local-api/
- FastAPI local service called by the desktop app.
- Starts as the local orchestration entrypoint.

docs/superpowers/plans/
- Implementation plans for agentic development.

docs/x2-aimdk-adapter.md
- AimDK 1.0 robot adapter mapping and mock-to-formal runtime instructions.

sdk/
- X2 AimDK SDK archive tracked with Git LFS for Ubuntu / ROS 2 continuation.
```

## Local API

Create and use a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r local-api\requirements-dev.txt
```

Run tests:

```powershell
.\.venv\Scripts\python -m pytest local-api\tests -q
```

Start the local API:

```powershell
.\scripts\start-local-api.ps1
```

Health check:

```text
http://127.0.0.1:8765/health
```

Robot adapter status:

```text
http://127.0.0.1:8765/robot-adapter/status
```

## Robot Adapter Modes

The API defaults to a mock robot adapter for local development:

```powershell
$env:X2_ROBOT_ADAPTER = "mock"
```

To use the formal AimDK 1.0 ROS 2 adapter, run the API inside the X2 AimDK ROS 2 environment and set:

```powershell
$env:X2_ROBOT_ADAPTER = "aimdk"
```

If `rclpy` or `aimdk_msgs` is missing, robot commands return HTTP `503` with `aimdk_runtime_unavailable`; they are not silently marked as executed. Full mapping and deployment notes are in `docs/x2-aimdk-adapter.md`.

## SDK Archive

The AimDK SDK zip is stored at:

```text
sdk\aimdk-aarch64-a424add7-artifacts.zip
```

It is tracked through Git LFS. After cloning on Ubuntu, run:

```bash
git lfs pull
unzip sdk/aimdk-aarch64-a424add7-artifacts.zip -d .tmp/aimdk-sdk
```

## Windows App

Install dependencies:

```powershell
cd windows-app
npm install
```

Run the desktop UI in browser dev mode:

```powershell
.\scripts\dev-windows-app.ps1
```

Build the desktop UI assets:

```powershell
cd windows-app
npm run build
```

If the local API is running on an AimDK host instead of this Windows machine, build with:

```powershell
$env:VITE_LOCAL_API_URL = "http://<aimdk-api-host>:8765"
.\scripts\build-windows-app.ps1
```

## Tauri Packaging

Tauri packaging requires:

```text
1. Rust/Cargo in PATH.
2. Microsoft Visual Studio Build Tools with the MSVC C++ toolchain.
3. Windows SDK components.
```

If Cargo is installed in the default user directory but the current shell cannot find it, restart the terminal or temporarily run:

```powershell
$env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
```

Check the Tauri environment:

```powershell
cd windows-app
npm run tauri -- info
```

Build the Windows desktop app:

```powershell
.\scripts\build-windows-app.ps1
```

The generated installer is written under:

```text
windows-app\src-tauri\target\release\bundle\nsis\
```
