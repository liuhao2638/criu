#未使用
# coding:utf-8
import json
import time
import yaml
import os

import pandas as pd


class Config:

    def __init__(self):
        with open("./config.yaml", "r", encoding="utf-8") as f:
            config = yaml.load(f.read(), Loader=yaml.FullLoader)
        self.__dict__["MODE"] = config("mode", default=None)

    def _get_yaml_value(self, *keys, default=None):
        """Safely get nested YAML config value with fallback"""
        config = self.yaml_config
        for key in keys:
            if not isinstance(config, dict):
                return default
            config = config.get(key, default)
        return config


config = Config()
