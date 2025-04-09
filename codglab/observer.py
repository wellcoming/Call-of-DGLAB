import asyncio
import time
import mss
import numpy as np
import cv2
import dearpygui.dearpygui as dpg
from PIL import Image
from codglab.dglab import DGLabController

HEALTH_BAR_REGION = {
    "1080p": {'left': 29, 'top': 1036, 'width': 368, 'height': 9},
    "1440p": {'left': 40, 'top': 1381, 'width': 489, 'height': 14}
}

FILLED_COLOR_BGR = np.array([206, 203, 206], dtype=np.uint8)
COLOR_TOLERANCE = 0
LOWER_COLOR = np.clip(FILLED_COLOR_BGR - COLOR_TOLERANCE, 0, 255).astype(np.uint8)
UPPER_COLOR = np.clip(FILLED_COLOR_BGR + COLOR_TOLERANCE, 0, 255).astype(np.uint8)
COLUMN_FILL_THRESHOLD = 0.9


def qshow(img, title="Quick View"):
    """用 OpenCV 快速显示 NumPy 图像数组 (彩色或灰度)"""
    cv2.imshow(title, img)
    cv2.waitKey(0)  # 等待按键，0表示无限等待
    cv2.destroyWindow(title)  # 只关闭这个窗口


def get_health(image: np.ndarray):
    mask = cv2.inRange(image, LOWER_COLOR, UPPER_COLOR)
    ratio = np.sum(mask // 255, axis=0) / mask.shape[0]
    indices = np.where(ratio >= COLUMN_FILL_THRESHOLD)[0]

    if indices.size == 0:
        return 0
    else:
        health = (indices[-1] + 1) / mask.shape[1]
        return health


async def detect_loop():
    health = 0
    dead = True

    with mss.mss() as sct:
        while True:
            t = time.time()

            sct_img = sct.grab(HEALTH_BAR_REGION[dpg.get_value("resolution")])
            img_array = np.frombuffer(sct_img.rgb, dtype=np.uint8).reshape((sct_img.height, sct_img.width, 3))
            h = get_health(img_array)
            dpg.configure_item("health_bar", default_value=h, overlay=f"{h:.2%}")

            if abs(health - h) > 0.05:
                await DGLabController.INSTANCE.trigger_hurt(health - h)
                health = h

            if health > 0:
                dead = False

            if health <= 0 and not dead:
                await DGLabController.INSTANCE.trigger_death()
                dead = True

            await DGLabController.INSTANCE.update()
            await asyncio.sleep(max(0.1 - time.time() + t, 0))


if __name__ == "__main__":
    # with mss.mss() as sct:
    #     time.sleep(5)
    #     sct_img = sct.grab(HEALTH_BAR_REGION)
    #     img_array = np.frombuffer(sct_img.rgb, dtype=np.uint8).reshape((sct_img.height, sct_img.width, 3))
    #     print(get_health(img_array))
    img = Image.open(r"C:\Users\coming\Desktop\11114123423.png")
    box = (
        HEALTH_BAR_REGION['left'],
        HEALTH_BAR_REGION['top'],
        HEALTH_BAR_REGION['left'] + HEALTH_BAR_REGION['width'],  # right = left + width
        HEALTH_BAR_REGION['top'] + HEALTH_BAR_REGION['height']  # lower = top + height
    )
    cropped_image = img.crop(box)
    cropped_image.save("health_bar_cropped.png")
