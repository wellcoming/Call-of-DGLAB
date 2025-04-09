import asyncio
from asyncio import Future

import dearpygui.dearpygui as dpg
from pydglab_ws.enums import RetCode

from ..config import load_config, save_config
from ..dglab import DGLabController
from ..utils import RESOURCE_PATH, get_local_ip, get_loop, generate_qrcode, ROOT_PATH


def _update_qrcode():
    text = DGLabController.INSTANCE.client.get_qrcode(f"ws://{dpg.get_value("address")}:{dpg.get_value("port")}")
    print(text)
    data = generate_qrcode(text)
    dpg.set_value("bind_qrcode_texture", data)


def _on_app_connected(task):
    try:
        result = task.result()
    except Exception as e:
        print(f"Bind failed: {e}")
        get_loop().create_task(DGLabController.INSTANCE.client.bind()).add_done_callback(_on_app_connected)
        return
    print("connected")
    dpg.configure_item("binding_group", show=False)
    dpg.configure_item("control_group", show=True)
    dpg.configure_item(
        "status_text",
        default_value="App connected",
        color=(0, 255, 0)
    )


def _on_server_started(future):
    try:
        future.result()  # 获取协程结果
    except Exception as e:
        dpg.configure_item("status_text",
                           default_value=f"Server start failed - {e}",
                           color=(255, 0, 0))
        return
    dpg.configure_item("status_text",
                       default_value="Waiting for binding",
                       color=(186, 215, 0))
    _update_qrcode()
    dpg.configure_item("binding_group", show=True)
    get_loop().create_task(DGLabController.INSTANCE.client.bind()).add_done_callback(_on_app_connected)


def _server_switch_callback(sender="server_switch", app_data=False):
    dpg.configure_item(
        item=sender,
        label="Server on" if app_data else "Server off",
    )
    if not app_data:
        dpg.configure_item("binding_group", show=False)
        dpg.configure_item("control_group", show=False)
        dpg.configure_item("status_text",
                           default_value="Stopped",
                           color=(100, 100, 100)
                           )

        asyncio.run_coroutine_threadsafe(DGLabController.INSTANCE.stop(), get_loop())
    else:
        dpg.configure_item("status_text",
                           default_value="Server is starting...",
                           color=(231, 143, 7)
                           )

        future: Future = asyncio.run_coroutine_threadsafe(
            DGLabController.INSTANCE.start("0.0.0.0", dpg.get_value("port")), get_loop())
        future.add_done_callback(_on_server_started)


def on_test():
    loop = get_loop()
    for i in range(1000):
        asyncio.run_coroutine_threadsafe(
            DGLabController.INSTANCE.trigger_death(),
            loop
        )


def stop_server():
    dpg.set_value("server_switch", False)
    _server_switch_callback()


def setup():
    with dpg.window(tag="main_window"):
        with dpg.texture_registry():
            dpg.add_dynamic_texture(300, 300, generate_qrcode("你个干净的白客"), tag="bind_qrcode_texture")

        dpg.add_checkbox(
            tag="server_switch",
            callback=_server_switch_callback,
        )
        with dpg.group(horizontal=True):
            dpg.add_text("Status:")
            dpg.add_text("???", tag="status_text")
        with dpg.group(horizontal=True):
            dpg.add_input_text(
                tag="address",
                label=":",
                width=200,
                scientific=True,
                default_value=get_local_ip(),
                hint="ip/domain",
                callback=stop_server
            )
            dpg.add_input_int(
                tag="port",
                label="Address",
                width=50,
                min_value=0,
                max_value=65535,
                default_value=5678,
                step=0, step_fast=0,
                callback=stop_server
            )

        dpg.add_separator()

        with dpg.group(tag="binding_group"):
            with dpg.group(horizontal=True):
                dpg.add_loading_indicator(style=1, color=(255, 255, 255))
                with dpg.group():
                    dpg.add_text("Shoujo Kitou Chuu...")
                    dpg.add_text("Waiting for your snail-paced hand speed. Are you even trying?")

            dpg.add_text("QR code")
            dpg.add_image("bind_qrcode_texture", label="QR code")

        with dpg.group(tag="control_group"):
            with dpg.group(horizontal=True):
                dpg.add_progress_bar(tag="channel_a", overlay="0/0")
                dpg.add_text("A")
            with dpg.group(horizontal=True):
                dpg.add_progress_bar(tag="channel_b", overlay="0/0")
                dpg.add_text("B")
            with dpg.group(horizontal=True):
                dpg.add_progress_bar(tag="health_bar", overlay="0%")
                dpg.add_text("HP")
            with dpg.group(horizontal=True):
                dpg.add_text("Dead:")
                dpg.add_text("False", color=(255, 0, 0))

            dpg.add_button(label="Don't touch!", tag="test_button", callback=on_test)

        dpg.add_separator()

        with dpg.tree_node(label="Config", default_open=True):
            with dpg.group(tag="config_container"):
                dpg.add_slider_intx(label="(A/B) Min Strength", tag="min_strength", max_value=200, size=2,
                                    default_value=[40, 40])
                dpg.add_slider_doublex(label="(A/B) Decrease cooldown", tag="decrease_cooldown", max_value=60, size=2,
                                       default_value=[5, 5])
                dpg.add_slider_doublex(label="(A/B) Decrease Speed", tag="decrease_speed", max_value=10, size=2,
                                       default_value=[1, 1])
                dpg.add_slider_doublex(label="(A/B) Hurt Penalty", tag="hurt_penalty", max_value=100, size=2,
                                       default_value=[20, 20])
                dpg.add_slider_doublex(label="(A/B) Death Penalty", tag="death_penalty", max_value=100, size=2,
                                       default_value=[20, 20])
                dpg.add_slider_doublex(label="(A/B) Hurt Speed", tag="hurt_speed", max_value=1, size=2,
                                       default_value=[0.2, 0.2])
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                dpg.add_button(label=" Save Config ", callback=lambda: save_config())
                dpg.add_button(label=" Load Config ", callback=lambda: load_config())

    _server_switch_callback()
    try:
        load_config()
    except FileNotFoundError:
        save_config()
    # ???


def setup_viewport():
    dpg.create_viewport(
        title="Call of DGLAB",
        small_icon=str(RESOURCE_PATH / "logo.ico"),
        large_icon=str(RESOURCE_PATH / "logo.ico"),
        width=600,
        height=800
    )
    dpg.show_viewport()
    # dpg.maximize_viewport()
    dpg.set_primary_window("main_window", True)
