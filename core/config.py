from __future__ import annotations
from json import loads as json_loads
from typing import Any, TypeVar
from pathlib import Path
from os.path import dirname, exists as path_exists
from json import loads as json_loads, dumps as json_dumps, JSONEncoder


class ConfigEncoder(JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, object):
            return obj.__dict__
        else:
            return super().default(obj)


class Config:
    def __init__(self, values: dict[Any, Any]) -> None:
        pass


ConfT = TypeVar("ConfT", bound=Config)


def create_config_path(file_path: str) -> str:
    dir_path = Path(dirname(file_path))
    dir_path.mkdir(parents=True, exist_ok=True)
    return file_path


def read_config(file_path: str, config_class: type[ConfT]) -> ConfT:
    create_config_path(file_path)

    if path_exists(file_path):
        with open(file_path, "r") as f:
            json = json_loads(f.read())
            obj = config_class(json)
            return obj
    else:
        obj = config_class({})
        write_config(file_path, obj)
        return obj


def write_config(file_path: str, config: ConfT) -> None:
    create_config_path(file_path)

    with open(file_path, "w") as f:
        f.write(
            json_dumps(config.__dict__, sort_keys=True, indent=4, cls=ConfigEncoder)
        )
