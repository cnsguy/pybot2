from __future__ import annotations
from typing import Any, TypeVar
from pathlib import Path
from os.path import dirname, exists as path_exists
from json import loads as json_loads, dumps as json_dumps, JSONEncoder
from pydantic import BaseModel


class ConfigEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, set):
            return list(o)
        else:
            return super().default(o)


class Config(BaseModel):
    pass


def create_config_path(file_path: str) -> str:
    dir_path = Path(dirname(file_path))
    dir_path.mkdir(parents=True, exist_ok=True)
    return file_path


ConfT = TypeVar("ConfT", bound=Config)


def read_config(file_path: str, config_class: type[ConfT]) -> ConfT:
    create_config_path(file_path)

    if path_exists(file_path):
        with open(file_path, "r") as f:
            json = json_loads(f.read())
            obj = config_class.model_validate(json)
            return obj
    else:
        obj = config_class.model_validate({})
        write_config(file_path, obj)
        return obj


def dump_config(config: Config) -> str:
    return json_dumps(config.__dict__, sort_keys=True, indent=4, cls=ConfigEncoder)


def write_config(file_path: str, config: Config) -> None:
    create_config_path(file_path)

    with open(file_path, "w") as f:
        f.write(dump_config(config))
