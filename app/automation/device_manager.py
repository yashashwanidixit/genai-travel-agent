import subprocess
from typing import List, Dict, Optional


class DeviceManager:
    """Detects and manages ADB connected Android devices and emulators."""

    @staticmethod
    def list_connected_devices() -> List[Dict[str, str]]:
        devices = []
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5
            )
            lines = result.stdout.strip().split("\n")[1:]
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "device":
                    devices.append({"udid": parts[0], "status": parts[1]})
        except Exception:
            # ADB might not be installed or in PATH; return mock device info
            pass
        return devices

    @staticmethod
    def get_default_capabilities(
        app_package: Optional[str] = None,
        app_activity: Optional[str] = None,
        device_name: str = "emulator-5554"
    ) -> Dict:
        caps = {
            "platformName": "Android",
            "automationName": "UiAutomator2",
            "deviceName": device_name,
            "noReset": True,
            "newCommandTimeout": 300,
        }
        if app_package:
            caps["appPackage"] = app_package
        if app_activity:
            caps["appActivity"] = app_activity
        return caps
