#!/usr/bin/env python3
import os
import time
import subprocess
import sys
import shutil

WATCH_DIR = os.path.expanduser("~/Linux_Back_Ups")
REMOTE_TARGET = "gdrive:Linux Back_Ups"
RCLONE_BIN = shutil.which("rclone") or os.path.expanduser("~/.local/bin/rclone")

os.makedirs(WATCH_DIR, exist_ok=True)

def get_dir_state():
    state = {}
    try:
        for root, _, files in os.walk(WATCH_DIR):
            for f in files:
                filepath = os.path.join(root, f)
                try:
                    stat = os.stat(filepath)
                    state[filepath] = (stat.st_mtime, stat.st_size)
                except OSError:
                    pass
    except Exception:
        pass
    return state

def notify(title, message, urgency="low"):
    try:
        subprocess.run(["notify-send", "-a", "Google Drive", "-u", urgency, title, message], check=False)
    except Exception:
        pass

def sync():
    try:
        if not shutil.which("rclone") and not os.path.exists(RCLONE_BIN):
            print("[Google Drive] rclone binary not found!")
            notify("Google Drive Backup Error", "rclone is not installed. Please install rclone.", "critical")
            return

        res = subprocess.run([
            RCLONE_BIN, "copy",
            WATCH_DIR, REMOTE_TARGET,
            "--transfers=4",
            "--checkers=8",
            "--fast-list"
        ], capture_output=True, text=True)
        if res.returncode == 0:
            print("[Google Drive] Backup successful.")
            notify("Google Drive Backup", "Files uploaded successfully to 'Linux Back_Ups'.")
        else:
            print(f"[Google Drive] Sync error: {res.stderr}")
    except Exception as e:
        print(f"[Google Drive] Error: {e}")

def main():
    print(f"Starting Google Drive Backup Watcher on {WATCH_DIR} -> {REMOTE_TARGET}")
    last_state = get_dir_state()
    if last_state:
        sync()

    while True:
        try:
            time.sleep(5)
            current_state = get_dir_state()
            if current_state != last_state:
                time.sleep(3)
                current_state = get_dir_state()
                last_state = current_state
                print("[Google Drive] Change detected! Uploading...")
                sync()
        except KeyboardInterrupt:
            break
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    main()
