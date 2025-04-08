import asyncio
import socket
import threading
import time
from asyncio import AbstractEventLoop
from pathlib import Path
from typing import Optional

import qrcode

ROOT_PATH = Path(__file__).resolve().parent.parent
RESOURCE_PATH = ROOT_PATH / "resource"


def get_local_ip():
    """
    获取本地 IP 地址。
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 连接到一个外部地址
        s.connect(('8.8.8.8', 80))
        # 获取本地 IP 地址
        local_ip = s.getsockname()[0]
        return local_ip
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return None
    finally:
        s.close()


_main_loop: Optional[AbstractEventLoop] = None
_loop_lock = threading.Lock()


def init_main_loop():
    global _main_loop
    with _loop_lock:
        if _main_loop is None:
            _main_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_main_loop)
    return _main_loop


def get_loop() -> AbstractEventLoop:
    with _loop_lock:
        return _main_loop


def generate_qrcode(text, size=300):
    t = time.perf_counter()

    # 生成二维码PIL图像
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=1,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.convert("RGBA").resize((size, size))

    data = []
    pixels = img.getdata()
    for pixel in pixels:
        # 白色二维码 (255,255,255,255)
        # 透明背景 (0,0,0,0)
        r, g, b, a = pixel
        data.extend([
            r / 255,  # R
            g / 255,  # G
            b / 255,  # B
            a / 255  # A
        ])

    return data

