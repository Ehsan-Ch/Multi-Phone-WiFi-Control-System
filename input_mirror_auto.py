import subprocess
import sys
import time
import threading
from screen_mirror_controller import ScreenMirrorController

def monitor_scrcpy_and_mirror(master_device: str, slave_devices: list):
    """Monitor scrcpy window and mirror actions"""
    controller = ScreenMirrorController(master_device, slave_devices)
    
    print("Input mirroring system ready!")
    print("This script will mirror actions from master to slaves.")
    print("Note: Full automatic mirroring requires scrcpy control API.")
    print("For now, use manual mirror functions or control via ADB commands.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: py input_mirror_auto.py MASTER_DEVICE SLAVE_DEVICES")
        print("Example: py input_mirror_auto.py 192.168.1.100:5555 192.168.1.101:5555,192.168.1.102:5555")
        sys.exit(1)
    
    master = sys.argv[1]
    slaves = sys.argv[2].split(',')
    
    monitor_scrcpy_and_mirror(master, slaves)


