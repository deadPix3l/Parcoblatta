"""Demo file intentionally containing violations for every bundled lint query."""


def mutable_default(items=[], options={}):
    """Triggers mutable-default twice."""
    items.append(options)
    return items


def debug_print(value):
    """Triggers print-debug."""
    print("debug:", value)


def dynamic_execution(source):
    """Triggers dynamic-exec twice."""
    eval(source)
    exec(source)


def runtime_assert(value):
    """Triggers assert-statement."""
    assert value is not None
    return value


def bare_exception_handler():
    """Triggers bare-except."""
    try:
        dynamic_execution("1 + 1")
    except:
        print("swallowed")
