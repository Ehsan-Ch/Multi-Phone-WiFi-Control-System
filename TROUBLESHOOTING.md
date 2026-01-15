# Troubleshooting: Slave Devices Not Responding

## Step 1: Test Basic Connectivity

Run this diagnostic script first:
```bash
py test_mirroring.py
```

This will test:
- If slave devices are connected
- If ADB commands work on slaves
- If the mirror function works
- If the scrcpy window can be detected

## Step 2: Test Direct Commands

Run this simple test:
```bash
py simple_mirror_test.py
```

This bypasses window detection and directly sends commands to slaves.
**If this works**, the issue is with input capture.
**If this doesn't work**, the issue is with ADB/slave connectivity.

## Step 3: Check Common Issues

### Issue: Dependencies Not Installed
**Symptoms:** No error messages, but nothing happens

**Solution:**
```bash
pip install pynput pywin32
# OR
py setup_dependencies.py
```

Verify installation:
```bash
pip list | findstr pynput
pip list | findstr pywin32
```

### Issue: Slave Devices Not Connected
**Symptoms:** "No slave devices" or connection errors

**Check:**
```bash
adb devices
```

**Solution:**
- Make sure all phones are on the same WiFi network
- Reconnect via USB and run: `py wifi_connection.py`
- Manually connect: `adb connect IP_ADDRESS:5555`

### Issue: Window Detection Failing
**Symptoms:** "Could not find scrcpy window" message

**Solution:**
1. Make sure scrcpy window is open and visible
2. Check window title matches (should contain "Phone Master" or "scrcpy")
3. Try clicking directly on the scrcpy window (not outside it)
4. Restart scrcpy: Close and reopen the window

### Issue: Commands Not Reaching Slaves
**Symptoms:** Debug shows "Click detected" but slaves don't respond

**Check:**
1. Verify slave devices are connected:
   ```bash
   adb devices
   ```

2. Test direct command on one slave:
   ```bash
   adb -s SLAVE_IP:5555 shell input tap 500 1000
   ```
   (Replace SLAVE_IP with actual IP)

3. Check if devices have proper permissions:
   ```bash
   adb -s SLAVE_IP:5555 shell getprop ro.build.version.sdk
   ```

### Issue: Coordinate Conversion Failing
**Symptoms:** Clicks detected but coordinates are wrong

**Debug:**
- Look for `[DEBUG]` messages in console
- Check if coordinates are being converted correctly
- Verify master device screen size is detected

**Solution:**
- Make sure master device screen is unlocked
- Try manual coordinate test: `controller.mirror_tap(500, 1000)`

## Step 4: Enable Debug Mode

The updated code now includes debug output. When you click on the scrcpy window, you should see:
```
[DEBUG] Click detected: window(x, y) -> phone(x, y)
[MIRROR] Sending tap (x, y) to N slave(s)...
[SUCCESS] Tap sent to all N slave(s)
```

If you don't see these messages:
- Input capture is not working (check pynput/win32gui)
- Window detection failed (check scrcpy window)

If you see `[DEBUG]` but not `[SUCCESS]`:
- Commands are not reaching slaves (check ADB connection)

## Step 5: Manual Testing

Test each component separately:

### Test 1: Slave Connectivity
```bash
adb -s SLAVE_IP:5555 shell input tap 500 1000
```
(Should tap on the slave device)

### Test 2: Python Mirror Function
```python
from screen_mirror_controller import ScreenMirrorController

controller = ScreenMirrorController("MASTER_IP:5555", ["SLAVE1_IP:5555"])
controller.mirror_tap(500, 1000)
```
(Should tap on slave)

### Test 3: Window Detection
```python
import win32gui

def find_window(hwnd, ctx):
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if 'scrcpy' in title.lower():
            print(f"Found: {title}")
    return True

win32gui.EnumWindows(find_window, [])
```

## Step 6: Alternative Solutions

If automatic mirroring still doesn't work, you can:

### Option A: Use Manual Mirror Functions
```python
from screen_mirror_controller import MasterSlaveController

controller = MasterSlaveController(master, slaves)
controller.start()

# Manually trigger mirroring
controller.manual_mirror_tap(500, 1000)
controller.manual_mirror_swipe(500, 1500, 500, 500)
controller.manual_mirror_key("KEYCODE_HOME")
```

### Option B: Use ADB Commands Directly
Create a script that sends the same command to all slaves:
```python
import subprocess

slaves = ["192.168.1.101:5555", "192.168.1.102:5555"]
for slave in slaves:
    subprocess.run(['adb', '-s', slave, 'shell', 'input tap 500 1000'])
```

### Option C: Use scrcpy with Control Server
Use scrcpy's built-in control server (requires scrcpy 2.0+):
```bash
scrcpy -s MASTER_IP:5555 --control-port=8886
```
Then connect to the control port to intercept events.

## Still Not Working?

1. **Check console output** - Look for error messages
2. **Run diagnostic scripts** - `py test_mirroring.py` and `py simple_mirror_test.py`
3. **Verify each step** - Don't skip any setup steps
4. **Check device permissions** - Some devices require additional permissions
5. **Try with fewer devices** - Test with 2-3 devices first

## Quick Checklist

- [ ] All devices connected via WiFi: `adb devices`
- [ ] Dependencies installed: `pip list | findstr pynput`
- [ ] scrcpy window is open and visible
- [ ] Slave devices respond to direct ADB commands
- [ ] Debug output shows click detection
- [ ] No firewall blocking ADB connections
- [ ] All devices on same WiFi network
- [ ] USB Debugging enabled on all devices

