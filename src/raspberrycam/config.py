import logging
from dataclasses import dataclass
from typing import Optional

import yaml


@dataclass
class Config:
    site: str
    lon: float
    lat: float
    catchment: str
    direction: str
    interval: int
    iot_auth: bool
    private_key: Optional[str] = ""
    public_key: Optional[str] = ""
    endpoint: Optional[str] = ""
    role_name: Optional[str] = ""
    device_id: Optional[str] = ""


class ConfigurationError(Exception):
    pass


def load_config(config_file: Optional[str] = "config.yaml") -> dict:
    try:
        with open(config_file, "r") as conf_file:
            config = yaml.safe_load(conf_file.read())
    except FileNotFoundError as err:
        logging.error(f"Configuration file not found at {config_file}")
        # TODO decide whether to exit or assume defaults, for now:
        raise ConfigurationError(err)

    try:
        return Config(**config)

    except TypeError as err:
        logging.error(f"{config_file} did not contain all the information it needs")
        logging.error(err)
        raise ConfigurationError(err)
