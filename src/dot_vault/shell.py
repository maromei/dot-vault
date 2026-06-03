from __future__ import annotations

import os
import platform


def get_default_shell() -> str:
    """Get the default shell of the user.

    On Windows, it returns the value of the COMSPEC environment variable.
    On POSIX systems, it tries to get the login shell from the password database,
    falling back to the SHELL environment variable or /bin/sh.

    Returns:
        The path to the default shell.
    """
    if platform.system() == "Windows":
        return os.environ.get("COMSPEC", "cmd.exe")

    try:
        import pwd

        return pwd.getpwuid(os.getuid()).pw_shell
    except ImportError, AttributeError, KeyError:
        return os.environ.get("SHELL", "/bin/sh")
