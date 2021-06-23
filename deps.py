from typing import Type, TypeVar
from fastapi import FastAPI


T = TypeVar("T")


def inject(app: FastAPI, type_: Type[T], value: T) -> None:
    if not hasattr(app.state, "dependencies"):
        app.state.dependencies = {}

    app.state.dependencies[type_] = value


def get(app: FastAPI, type_: Type[T]) -> T:
    value = app.state.dependencies[type_]
    if not isinstance(value, type_):
        raise ValueError("Uninitialized dependency?!")
    return value
