"""
Setup script to install required dependencies for input mirroring
"""
import subprocess
import sys

def install_package(package):
    """Install a Python package"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ Failed to install {package}")
        return False

def main():
    print("=" * 60)
    print("  Installing Dependencies for Input Mirroring")
    print("=" * 60)
    print()
    
    packages = [
        "pynput==1.7.6",
        "pywin32==306"
    ]
    
    print("This will install:")
    for pkg in packages:
        print(f"  - {pkg}")
    print()
    
    input("Press Enter to continue or Ctrl+C to cancel...")
    print()
    
    success_count = 0
    for package in packages:
        print(f"Installing {package}...")
        if install_package(package):
            success_count += 1
        print()
    
    print("=" * 60)
    if success_count == len(packages):
        print("✓ All dependencies installed successfully!")
        print("\nYou can now run: py main.py")
    else:
        print(f"⚠ Some packages failed to install ({success_count}/{len(packages)})")
        print("You may need to install them manually:")
        print("  pip install pynput pywin32")
    print("=" * 60)

if __name__ == "__main__":
    main()


