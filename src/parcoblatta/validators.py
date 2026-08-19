from typing import TypeVar

T = TypeVar("T")


def ensure_list(value: T | list[T] | tuple[T] | set[T]) -> list[T]:
  """ wrap or convert value to a list. """
  if not isinstance(value, (list, tuple, set)):
      return [value]
  return list(value)
