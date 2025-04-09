from pathlib import Path

import dearpygui.dearpygui as dpg
import json
import os
from dataclasses import dataclass, field, fields, asdict
from typing import List, Any

from codglab.utils import ROOT_PATH, CONFIG_PATH


def load_config(path=CONFIG_PATH):
    data = json.loads(
        Path(path).read_text()
    )
    for k, v in data.items():
        dpg.set_value(k, v)


def save_config(path=CONFIG_PATH):
    # print(path)
    config = {}
    for i in dpg.get_item_children("config_container", slot=1):
        tag = dpg.get_item_alias(i)
        config[tag] = dpg.get_value(tag)
    Path(path).write_text(
        json.dumps(config)
    )
