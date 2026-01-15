# 📱 Multi-Phone WiFi Control System

Control multiple Android phones wirelessly from your PC using ADB, scrcpy, and Python. This system mirrors actions from a master device to multiple slave devices in real time — perfect for testing, automation, or synchronized control.

---

## 🚀 Features

- Connect up to **10 Android phones** via WiFi (no USB needed after setup)
- View and control the **master phone** on your PC using scrcpy
- Automatically mirror **taps, swipes, key presses, and text input** to all slave devices
- Supports **coordinate scaling** for different screen sizes
- Includes **manual and automatic input mirroring**
- Built-in **diagnostics and troubleshooting tools**

---

## 🧰 Requirements

- Windows PC
- Android phones (USB Debugging enabled)
- Same WiFi network for all devices

### Software Dependencies

| Tool       | Purpose                         | Installation |
|------------|----------------------------------|--------------|
| ADB        | Android device communication     | Download [(developer.android.com in Bing)](https://www.bing.com/search?q="https%3A%2F%2Fdeveloper.android.com%2Fstudio%2Freleases%2Fplatform-tools") |
| scrcpy     | Screen mirroring for master phone| Download [(github.com in Bing)](https://www.bing.com/search?q="https%3A%2F%2Fgithub.com%2FGenymobile%2Fscrcpy%2Freleases") or `winget install scrcpy` |
| Python 3.7+| Script execution                 | [Download](https://www.python.org/downloads/) |
| pynput     | Mouse/keyboard input capture     | Installed via setup script |
| pywin32    | Windows GUI interaction          | Installed via setup script |

---

## 📦 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/multi-phone-control.git
   cd multi-phone-control
   ```

2. Install Python dependencies:
   ```bash
   py setup_dependencies.py
   ```

3. Add ADB and scrcpy to your system PATH.

---

## 🔧 First-Time Setup

1. Connect all phones via USB and enable USB Debugging.
2. Run:
   ```bash
   py wifi_connection.py
   ```
   This will:
   - Detect devices
   - Enable WiFi ADB
   - Connect all phones wirelessly

3. Disconnect USB cables once WiFi connection is established.

---

## 📲 Daily Usage

### Recommended Method
```bash
py main.py
```
- Select master device
- Start scrcpy window
- Begin mirroring actions to all slaves

### Manual Control
```python
from screen_mirror_controller import ScreenMirrorController

controller = ScreenMirrorController("MASTER_IP:5555", ["SLAVE1_IP:5555", "SLAVE2_IP:5555"])
controller.mirror_tap(500, 1000)
controller.mirror_swipe(500, 1500, 500, 500)
controller.mirror_key("KEYCODE_HOME")
```

---

## 🧪 Testing & Debugging

Run diagnostic scripts:
```bash
py simple_mirror_test.py
py test_mirroring.py
```

Check console output for:
- `[DEBUG] Click detected`
- `[MIRROR] Sending tap...`
- `[SUCCESS] Tap sent to all slave(s)`

---

## 🛠 File Overview

| File                      | Description                                      |
|---------------------------|--------------------------------------------------|
| `main.py`                 | Main entry point for system setup and control    |
| `wifi_connection.py`      | Connects devices via WiFi ADB                    |
| `screen_mirror_controller.py` | Handles scrcpy, input mirroring, coordinate mapping |
| `phone_controller.py`     | Core ADB command execution for devices           |
| `input_mirror_auto.py`    | Background input mirroring script                |
| `setup_dependencies.py`   | Installs required Python packages                |
| `simple_mirror_test.py`   | Basic mirroring test without scrcpy              |
| `requirements.txt`        | Python dependencies list                         |

---

## 🧠 Tips

- Use `--no-control` flag in scrcpy to avoid Android word selection issues.
- Keep phones unlocked and awake during mirroring.
- Test with 2–3 devices before scaling to 10.
- Use `controller.get_screen_info(device_id)` for accurate coordinate mapping.

---

## 📞 Support

For issues or questions:
- ADB Docs: developer.android.com [(developer.android.com in Bing)](https://www.bing.com/search?q="https%3A%2F%2Fdeveloper.android.com%2Fstudio%2Fcommand-line%2Fadb")
- scrcpy Docs: [github.com/Genymobile/scrcpy](https://github.com/Genymobile/scrcpy)
- Python Docs: [python.org](https://www.python.org/)

---

## ✅ Quick Start Checklist

- [x] Install ADB and scrcpy
- [x] Install Python 3.7+
- [x] Enable USB Debugging on all phones
- [x] Connect phones via USB
- [x] Run `py wifi_connection.py`
- [x] Disconnect USB cables
- [x] Run `py main.py`
- [x] Control master phone — actions mirror to all slaves!

---
