import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    import PySide6.QtOpenGL  # noqa: F401
    import PySide6.QtOpenGLWidgets  # noqa: F401
except ImportError:
    pass

from rem_card.app.main import main


if __name__ == "__main__":
    main(forced_role="doctor")
