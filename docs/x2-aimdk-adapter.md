# X2 AimDK 1.0 Robot Adapter

This document explains how the platform switches from the local mock executor to the formal AimDK 1.0 ROS 2 executor.

## Runtime Modes

The local API uses `X2_ROBOT_ADAPTER` at command time:

```powershell
$env:X2_ROBOT_ADAPTER = "mock"   # default, no robot required
$env:X2_ROBOT_ADAPTER = "aimdk"  # formal AimDK ROS 2 adapter
```

Check the selected adapter:

```text
GET /robot-adapter/status
```

In `aimdk` mode, the API fails closed. If `rclpy` or `aimdk_msgs` is not available, robot commands return HTTP `503` with `aimdk_runtime_unavailable` instead of pretending the robot executed the command.

## Where AimDK Mode Runs

AimDK mode must run inside an X2 AimDK ROS 2 environment, not a plain Windows Python shell.

Expected runtime:

```bash
source /opt/ros/humble/setup.bash
source <aimdk-workspace>/install/setup.bash
export X2_ROBOT_ADAPTER=aimdk
uvicorn app.main:app --host 0.0.0.0 --port 8765
```

AimDK 1.0 says SDK packages and URDF files are currently obtained or updated through after-sales technical support. Keep platform files outside `$HOME/aimdk*`, because that path is system-maintained and firmware operations can move or erase user data.

If the Windows desktop app talks to an API running on the robot or a development compute unit, build the desktop app with:

```powershell
$env:VITE_LOCAL_API_URL = "http://<aimdk-api-host>:8765"
.\scripts\build-windows-app.ps1
```

## Action Mapping

| Platform action | AimDK interface | Notes |
| --- | --- | --- |
| `tts` | `/aimdk_5Fmsgs/srv/PlayTts` (`PlayTts`) | Uses `payload.text`, platform `priority`, and command id as trace id. |
| `audio_file` / `audio` | `/aimdk_5Fmsgs/srv/PlayAudioFile` (`PlayAudioFile`) | Requires `file_path` and `file_name`, or an absolute `asset_uri`. The SDK example sends `file_path` with a trailing slash. Files must live on the interaction compute unit and be readable. |
| `screen_video` / `video` | `/face_ui_proxy/play_video` (`PlayVideo`) | Requires an absolute robot-side `video_path` or `asset_uri`; `local://` demo assets are mock-only. |
| `emoji` | `/face_ui_proxy/play_emoji` (`PlayEmoji`) | Uses `emoji_id`, `mode`, and priority. |
| `motion` | `/aimdk_5Fmsgs/srv/SetMcPresetMotion` (`SetMcPresetMotion`) | Uses `motion_id` to resolve AimDK `motion` and `area`; the robot must be in Stable Stand first. |
| `locomotion` | `/aima/mc/locomotion/velocity` (`McLocomotionVelocity`) | Publishes velocity fields after registering `X2_AIMDK_INPUT_SOURCE` through `SetMcInputSource`. |
| `led` | `/aimdk_5Fmsgs/srv/SetPmuLed` (`SetPmuLed`) | Supports steady, breathing, blinking, and flowing modes. AimDK notes LED service calls can take about five seconds. |
| `linkcraft` | `/aimdk_5Fmsgs/srv/ExecuteActionResource` (`ExecuteActionResource`) | Uses `resource_key`, optional version, and LinkCraft meta JSON. |

Preset motion ids currently built into the adapter include `wave`, `right_hand_wave`, `left_hand_wave`, `right_hand_raise`, `left_hand_raise`, `clap`, `heart_both_hands`, `hug`, `cheer`, `raise_both_hands`, `wave_goodbye`, and `bow`.

## Environment Variables

```text
X2_ROBOT_ADAPTER=aimdk
X2_AIMDK_INPUT_SOURCE=x2_rental_platform
X2_AIMDK_INPUT_SOURCE_PRIORITY=40
X2_AIMDK_INPUT_SOURCE_TIMEOUT_MS=1000
X2_AIMDK_SERVICE_TIMEOUT_SECONDS=5.0
X2_AIMDK_AUTO_REGISTER_INPUT_SOURCE=true
```

The default input source priority is `40`, matching AimDK's mid-level/custom control range guidance. Increase it only when the operator workflow intentionally needs to override lower-priority sources.

## SDK Request Details

The adapter now follows the request header paths used by the SDK Python examples:

```text
PlayTts / PlayVideo / PlayEmoji / ExecuteActionResource -> header.header.stamp
PlayAudioFile / SetPmuLed / SetMcInputSource -> request.header.stamp
SetMcPresetMotion -> header.stamp
McLocomotionVelocity -> header.stamp
```

Preset motion calls treat either `response.header.code == 0` or `response.state.value == 400` (`RUNNING`) as accepted, matching the SDK example behavior.

## Safety Constraints

AimDK 1.0 requires motion and locomotion to be used only when the robot is in a safe posture. The adapter does not switch robot mode automatically yet. Operator flow should explicitly put the robot into Stable Stand before `motion` and `locomotion`.

For locomotion, AimDK documents start thresholds around `forward_velocity=0.09`, `lateral_velocity=0.60`, and `angular_velocity=0.03`, but warns that firmware releases can change them. Keep scenario movement commands conservative and retest after firmware updates.
