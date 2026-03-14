import os
import sys
import time
import winreg
import threading

import keyboard
import pyperclip
import zhconv
import pystray
from PIL import Image, ImageDraw, ImageFont

APP_NAME = "ChineseConverter"
STARTUP_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

# start.vbs 路徑（用於無視窗背景啟動）
VBS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "start.vbs")


# ── 簡繁轉換 ────────────────────────────────────────────────

def detect_and_convert(text: str) -> tuple[str, str]:
    print(f"DETECT Original: {text}")
    as_simplified = zhconv.convert(text, "zh-hans")
    print(f"DETECT Simplified: {as_simplified}")
    if as_simplified != text:
        return as_simplified, "繁→簡"
    as_traditional = zhconv.convert(text, "zh-hant")
    print(f"DETECT Traditional: {as_traditional}")
    if as_traditional != text:
        return as_traditional, "簡→繁"
    return text, "無變化"


def on_hotkey():
    try:
        print("DETECT Triggered")
        original_clipboard = pyperclip.paste()
        print(f"DETECT Clipboard: {original_clipboard}")
    except Exception:
        original_clipboard = ""

    keyboard.send("ctrl+c")
    time.sleep(0.3)

    try:
        selected_text = pyperclip.paste()
        print(f"DETECT Selected: {selected_text}")
    except Exception:
        return

    if not selected_text or selected_text == original_clipboard:
        print("DETECT No change detected.")
        return

    converted, direction = detect_and_convert(selected_text)
    print(f"DETECT Converted: {converted}, Direction: {direction}")
    if converted != selected_text:
        pyperclip.copy(converted)
        keyboard.send("ctrl+v")
        time.sleep(0.5)
    pyperclip.copy(original_clipboard)


# ── 開機自動啟動 ────────────────────────────────────────────

def is_autostart_enabled() -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False


def set_autostart(enable: bool):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_KEY, 0, winreg.KEY_ALL_ACCESS)
    if enable:
        # 用 wscript 執行 vbs，完全無視窗
        cmd = f'wscript.exe "{VBS_PATH}"'
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
    else:
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass
    winreg.CloseKey(key)


# ── 系統匣圖示 ──────────────────────────────────────────────

def create_icon_image() -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 藍色圓形底
    draw.ellipse([2, 2, 62, 62], fill=(52, 120, 246))
    # 嘗試載入中文字體，失敗則用預設
    font = None
    for font_path in [
        r"C:\Windows\Fonts\msjh.ttc",   # 微軟正黑體
        r"C:\Windows\Fonts\simsun.ttc",  # 新細明體
        r"C:\Windows\Fonts\msyh.ttc",   # 微軟雅黑
    ]:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, 26)
                break
            except Exception:
                continue

    text = "繁"
    if font:
        draw.text((32, 32), text, fill="white", anchor="mm", font=font)
    else:
        draw.text((20, 20), text, fill="white")
    return img


def build_tray_menu(icon: pystray.Icon):
    def toggle_autostart(icon, item):
        current = is_autostart_enabled()
        set_autostart(not current)
        # 重新建立選單以更新勾選狀態
        icon.menu = pystray.Menu(
            pystray.MenuItem(
                "開機自動啟動",
                toggle_autostart,
                checked=lambda item: is_autostart_enabled(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", lambda icon, item: icon.stop()),
        )

    return pystray.Menu(
        pystray.MenuItem(
            "開機自動啟動",
            toggle_autostart,
            checked=lambda item: is_autostart_enabled(),
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", lambda icon, item: icon.stop()),
    )


# ── 主程式 ──────────────────────────────────────────────────

def keyboard_loop():
    keyboard.add_hotkey(
        "ctrl+alt+q",
        lambda: threading.Thread(target=on_hotkey, daemon=True).start(),
        suppress=True,
    )
    keyboard.wait()


def main():
    # 熱鍵監聽跑在背景執行緒
    t = threading.Thread(target=keyboard_loop, daemon=True)
    t.start()

    # pystray 必須在主執行緒執行（Windows 限制）
    img = create_icon_image()
    icon = pystray.Icon(APP_NAME, img, "中文簡繁轉換\nCtrl+Alt+Q")
    icon.menu = build_tray_menu(icon)
    icon.run()  # 阻塞直到使用者點「退出」


if __name__ == "__main__":
    main()
