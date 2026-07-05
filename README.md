# X2 Rental Scenario Platform

Windows desktop foundation for the X2 rental scenario orchestration platform.

## Current Direction

The first product shape is a Windows desktop app, not a browser-first web app.

```text
Windows Desktop App
-> Windows Business API
-> X2 PC2 Robot Gateway
-> X2 AimDK / ROS2
-> X2 PC3 media resources when audio/video/screen actions need files
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
- FastAPI service with two roles:
  - Windows business API.
  - X2 PC2 robot gateway.

scripts/
- Windows and Ubuntu start scripts for business API, desktop dev, Tauri build, and PC2 robot gateway.

docs/superpowers/plans/
- Implementation plans for agentic development.

docs/x2-aimdk-adapter.md
- AimDK 1.0 robot adapter mapping and mock-to-formal runtime instructions.

sdk/
- X2 AimDK SDK archive tracked with Git LFS for Ubuntu / ROS 2 continuation.
```

## Windows Business API

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

Start the Windows business API with local mock robot execution:

```powershell
.\scripts\start-local-api.ps1
```

For the production split where Windows keeps the business system and X2 PC2 runs AimDK, point the Windows business API at the PC2 robot gateway:

```powershell
$env:X2_ROBOT_GATEWAY_URL = "http://<x2-pc2-ip>:8766"
.\scripts\start-local-api.ps1
```

Health check:

```text
http://127.0.0.1:8765/health
```

Robot adapter / gateway status:

```text
http://127.0.0.1:8765/robot-adapter/status
```

## X2 PC2 Robot Gateway

Run the robot gateway on X2 PC2 inside the X2 AimDK ROS 2 environment:

```bash
source /opt/ros/humble/setup.bash
source <aimdk-workspace>/install/setup.bash
export X2_ROBOT_ADAPTER=aimdk
./scripts/start-robot-gateway.sh
```

The gateway listens on `0.0.0.0:8766` by default and exposes only robot endpoints, not business endpoints.

If `rclpy` or `aimdk_msgs` is missing, robot commands return HTTP `503` with `aimdk_runtime_unavailable`; they are not silently marked as executed. Full mapping and deployment notes are in `docs/x2-aimdk-adapter.md`.

Recommended deployment:

```text
Windows
- Desktop UI
- Business API, scenario engine, licensing, logs
- X2_ROBOT_GATEWAY_URL=http://<x2-pc2-ip>:8766

X2 PC2
- Robot gateway
- X2_ROBOT_ADAPTER=aimdk
- ROS 2 / AimDK command calls

X2 PC3
- Audio/video/screen resources referenced by AimDK paths
```

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

If the Windows business API is not running on the same machine as the desktop app, build with:

```powershell
$env:VITE_LOCAL_API_URL = "http://<windows-business-api-host>:8765"
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
