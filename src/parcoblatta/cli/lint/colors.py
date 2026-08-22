
class ANSIColor:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'


class NoColor(ANSIColor):
    """No-op color codes for plain text output."""
    RED = ''
    CYAN = ''
    GRAY = ''
    YELLOW = ''
    RESET = ''
