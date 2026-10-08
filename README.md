# Multi-Phone WiFi Control System

A Python automation project for communicating with multiple Android phones from a Windows PC through ADB and scrcpy.

The controller connects devices over WiFi, opens the primary phone in a scrcpy window and dispatches input commands to connected devices. The code includes screen-coordinate mapping, parallel command execution and diagnostic utilities.

## Components

| File | Responsibility |
| --- | --- |
| `main.py` | Device discovery, primary-device selection and controller startup |
| `wifi_connection.py` | USB-assisted setup and WiFi ADB connections |
| `phone_controller.py` | ADB commands, device information and parallel dispatch |
| `screen_mirror_controller.py` | scrcpy integration, screen mapping and input handling |
| `input_mirror_auto.py` | Additional input-mirroring entry point |
| `simple_mirror_test.py` | Basic command-dispatch diagnostics |
| `requirements.txt` | Python dependencies for automatic input capture |

## Requirements

- Windows PC.
- At least two Android phones for the main multi-device workflow.
- USB debugging enabled and authorised on the devices.
- A shared WiFi network and initial USB connections for setup.
- [Android SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools) with ADB on PATH.
- [scrcpy](https://github.com/Genymobile/scrcpy) on PATH.
- Python with dependencies compatible with the chosen Windows/Python environment.

## Setup

Clone the repository and install the listed Python dependencies:

```powershell
git clone https://github.com/Ehsan-Ch/Multi-Phone-WiFi-Control-System.git
cd Multi-Phone-WiFi-Control-System
py -m pip install -r requirements.txt
```

The requirements file pins `pynput==1.7.6` and `pywin32==306`.

Connect the phones by USB, authorise debugging, and run:

```powershell
py wifi_connection.py
```

After successful WiFi connections, the USB cables can be disconnected.

## Run

```powershell
py main.py
```

Select the primary device when prompted. The application starts `MasterSlaveController` and opens the primary screen with scrcpy. Use Ctrl+C to stop.

The implementation uses "master" and "slave" in class names and prompts. Here, they refer to the primary phone and the additional controlled phones.

## Diagnostics and current status

```powershell
py simple_mirror_test.py
```

The recorded [diagnostic notes](DIAGNOSIS_RESULTS.md) describe three connected devices and successful ADB command dispatch, alongside an input-capture issue. These notes are evidence of that development session, not a current end-to-end verification or a ten-device performance benchmark.

For the intended Windows/Android setup, verify device connections, scrcpy window detection, input capture and coordinate mapping separately. See [troubleshooting](TROUBLESHOOTING.md), [input-handling notes](MASTER_INPUT_FIX.md) and [quick-fix notes](QUICK_FIX.md) for the existing development history.

## Technical focus

Python subprocess integration, concurrent command dispatch, Windows input handling, screen-coordinate translation and hardware/software debugging.


## Automated regression checks

```powershell
py -m unittest discover -s tests -v
```

Five hardware-free tests cover literal text quoting for the Android shell,
empty-device handling, stale-device cleanup after a failed scan, installation
exit status and USB-only discovery. USB setup now uses `adb devices -l` and
requires a USB transport marker, excluding existing wireless transports.
These mocked checks do not replace end-to-end tests with Windows and phones.
