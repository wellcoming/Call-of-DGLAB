import asyncio
import time
from typing import Optional

import dearpygui.dearpygui as dpg
from pydglab_ws import DGLabClient, Channel, StrengthOperationType, RetCode, DGLabWSServer
from pydglab_ws.models import StrengthData

from codglab.exception import ServerNotStartException
from codglab.pulses import get_hurt_pulse


class DGLabController:
    INSTANCE: "DGLabController" = None

    def __init__(self):
        self.server: Optional[DGLabWSServer] = None
        self.client: Optional[DGLabClient] = None

        self.base = [0, 0]
        self.cur = [0, 0]
        self.last_update = -1
        self.last_hurt = -1
        self.dead = False

        self.max_strength = [40, 40]

    async def start(self, host: str = "0.0.0.0", port: int = 5678):
        """显式启动服务器"""
        if self.server is not None:
            raise RuntimeError("Server is already running")

        # 手动创建服务器实例
        self.server = DGLabWSServer(host, port, 60)

        # 手动调用 __aenter__
        await self.server.__aenter__()

        # 创建客户端
        self.client = self.server.new_local_client()
        asyncio.create_task(self.message_handler())

    async def stop(self):
        """显式停止服务器"""
        if self.server is None:
            return

        # 手动调用 __aexit__（参数使用默认值）
        await self.server.__aexit__(None, None, None)

        # 清理资源
        await self._cleanup()

    async def _cleanup(self):
        self.server = None
        self.client = None

    def check_start(self):
        if self.client is None or self.server is None:
            raise ServerNotStartException("DGLab Server haven't start.")

    async def message_handler(self):
        """处理来自客户端的消息"""
        self.check_start()
        print()
        async for msg in self.client.data_generator(RetCode, StrengthData):
            print(msg)
            match msg:
                case RetCode.CLIENT_DISCONNECTED:
                    print("设备断开")
                    await self.stop()
                    # await self.client.rebind()
                case msg if isinstance(msg, StrengthData):
                    self.max_strength[0] = msg.a_limit
                    self.max_strength[1] = msg.b_limit
                    # if all(s < 70 for s in self.max_strength):
                    #     self.too_low_max_strength()

    @staticmethod
    def too_low_max_strength():
        with dpg.popup(modal=True):
            dpg.add_text("tiaozhemediqiaobuqisheine")

    async def trigger_hurt(self, h):
        print(f"Hurt:{h}")
        if h <= 0: return
        self.last_hurt = time.time()
        self.cur = [1, 1]
        self.base[0] += h * dpg.get_value("hurt_penalty")[0]
        self.base[1] += h * dpg.get_value("hurt_penalty")[1]

    async def trigger_death(self):
        print(f"Dead")
        self.last_hurt = time.time()
        self.cur = [1, 1]
        self.base[0] += dpg.get_value("death_penalty")[0]
        self.base[1] += dpg.get_value("death_penalty")[1]

    async def update(self):
        if not self.client:
            return
        else:
            await self.client.ensure_bind()
        t = time.time()
        dt = t - self.last_update

        for i in range(2):

            if self.last_hurt + dpg.get_value("decrease_cooldown")[i] < time.time():
                self.base[i] = max(
                    dpg.get_value("min_strength")[i],
                    self.base[i] - dt * dpg.get_value("decrease_speed")[i]
                )

            self.cur[i] = max(self.cur[i] - dt * dpg.get_value("hurt_speed")[i], 0)
            real = min(self.cur[i] * self.base[i], self.max_strength[i])

            print(f"update base{self.base} cur{self.cur} real{real}")

            if self.cur[i] > 0:
                asyncio.create_task(
                    self.client.set_strength(Channel(i + 1), StrengthOperationType.SET_TO, int(real))
                )
                asyncio.create_task(self.client.add_pulses(Channel(i + 1), get_hurt_pulse(self.cur[i])))

            # UI
            dpg.configure_item("channel_" + "ab"[i], default_value=real / self.max_strength[i] if self.max_strength[i]!=0 else 0,
                               overlay=f"{float(real):.2}/{self.max_strength[i]}")

        self.last_update = time.time()
