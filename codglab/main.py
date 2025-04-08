import asyncio
import threading
from asyncio import get_event_loop
import dearpygui.demo as demo
import dearpygui.dearpygui as dpg
import dearpygui.experimental

from codglab.dglab import DGLabController
from codglab.observer import detect_loop
from codglab.ui import main_window
from codglab.utils import get_loop, init_main_loop


async def stop():
    if DGLabController.INSTANCE:
        await DGLabController.INSTANCE.stop()  # 确保等待停止完成


def ui_main():
    dpg.create_context()
    dpg.setup_dearpygui()

    # UI Logic
    main_window.setup()
    # demo.show_demo()
    main_window.setup_viewport()

    dpg.start_dearpygui()
    dpg.destroy_context()

    # 关闭UI后发送停止信号
    loop = get_loop()
    if loop and not loop.is_closed():
        asyncio.run_coroutine_threadsafe(stop(), loop)
        loop.call_soon_threadsafe(lambda _: loop.stop())  # 更安全的停止方式

    dpg.destroy_context()


def main():
    loop = init_main_loop()

    DGLabController.INSTANCE = DGLabController()
    loop.create_task(detect_loop())

    ui_thread = threading.Thread(target=ui_main, daemon=True)
    ui_thread.start()

    try:
        loop.run_forever()
    finally:
        print("Stopping CODglab")
        loop.run_until_complete(stop())
        # 清理所有异步任务
        tasks = asyncio.all_tasks(loop)
        for task in tasks:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        loop.close()
