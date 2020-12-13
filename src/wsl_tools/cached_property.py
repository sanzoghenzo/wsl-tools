"""Cached property for Python < 3.8."""
from __future__ import annotations

import inspect
from typing import Any
from typing import Callable
from typing import Generic
from typing import TypeVar

_T = TypeVar("_T")
_S = TypeVar("_S")


class cached_property(Generic[_T]):  # noqa: N801
    """
    A property that is only computed once per instance and then replaces itself
    with an ordinary attribute.

    Deleting the attribute resets the property.
    Source: https://github.com/pydanny/cached-property
    """  # noqa

    def __init__(self, func: Callable[[Any], _T]) -> None:
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__
        self.__signature__ = inspect.signature(func)
        self.func = func

    def __get__(self, obj: _S, cls: Any) -> _T:
        """Return the cached object or compute its value."""
        if obj is None:
            return self  # type: ignore

        value = obj.__dict__[self.__name__] = self.func(obj)
        return value
