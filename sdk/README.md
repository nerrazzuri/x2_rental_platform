# AimDK SDK

This directory stores the X2 AimDK SDK archive used by the platform adapter.

The SDK archive is tracked with Git LFS because it is larger than GitHub's normal file limit:

```bash
git lfs pull
unzip sdk/aimdk-aarch64-a424add7-artifacts.zip -d .tmp/aimdk-sdk
```

Use the extracted SDK in an Ubuntu / ROS 2 Humble environment when running `X2_ROBOT_ADAPTER=aimdk`.
