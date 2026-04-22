import argparse
import ctypes
import os
import socket
import sys
from typing import Optional


def _show_native_warning(title: str, message: str):
    try:
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
    except Exception:
        print(f"{title}: {message}")


def _acquire_initial_role_lock(role: Optional[str]):
    if role not in ("doctor", "nurse"):
        return None

    from rem_card.app.paths import get_role_lock_path
    from rem_card.app.role_session_lock import RoleSessionLock

    owner_id = f"{socket.gethostname()}:{os.getpid()}:rem_card_startup"
    lock = RoleSessionLock(
        lock_path=get_role_lock_path(role),
        role=role,
        owner_id=owner_id,
        stale_timeout_sec=60.0,
        heartbeat_sec=8.0,
    )
    if lock.acquire():
        return lock

    role_name = "Врач" if role == "doctor" else "Медсестра"
    holder = lock.describe_holder()
    _show_native_warning(
        "Роль занята",
        f"Роль \"{role_name}\" уже открыта на другом ПК.\n\n{holder}",
    )
    return None


def _shutdown_window_resources(window, logger):
    if not window:
        return
    container = getattr(window, "container", None)
    if not container:
        return

    data_service = getattr(container, "data_service", None)
    if data_service:
        try:
            data_service.shutdown()
        except Exception as exc:
            logger.warning("DataService shutdown failed: %s", exc)

    db_manager = getattr(container, "db_manager", None)
    if db_manager:
        try:
            db_manager.close()
        except Exception as exc:
            logger.warning("DB manager close failed: %s", exc)


def main():
    try:
        _main_impl()
    except Exception:
        import traceback

        crash_path = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "crash.txt")
        try:
            with open(crash_path, "w", encoding="utf-8") as fh:
                fh.write(traceback.format_exc())
        except Exception:
            pass
        sys.exit(1)


def _main_impl():
    parser = argparse.ArgumentParser(description="РЕМКАРТА v2.0")
    parser.add_argument("--role", choices=["doctor", "nurse"], help="Начальная роль пользователя")
    args, _unknown = parser.parse_known_args()

    from PySide6.QtNetwork import QLocalSocket, QLocalServer
    from PySide6.QtWidgets import QApplication, QSplashScreen
    from PySide6.QtGui import QPixmap
    from PySide6.QtCore import Qt

    role_suffix = args.role if args.role else "default"
    server_name = f"rem_card_single_instance_server_{role_suffix}"

    socket_client = QLocalSocket()
    socket_client.connectToServer(server_name)

    if socket_client.waitForConnected(500):
        socket_client.write(b"SHOW")
        if socket_client.waitForBytesWritten(500):
            print(f"Приложение с ролью '{role_suffix}' уже запущено. Окно будет развернуто.")
            sys.exit(0)

    QLocalServer.removeServer(server_name)

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)

    role_lock = _acquire_initial_role_lock(args.role)
    if args.role in ("doctor", "nurse") and role_lock is None:
        sys.exit(0)

    app = QApplication(sys.argv)
    window = None
    logger = None
    exit_code = 1
    try:
        from rem_card.app.paths import get_icon_dir

        icon_path = os.path.join(get_icon_dir(), "remcardicon.ico")
        splash_pix = QPixmap(icon_path).scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        splash.show()
        app.processEvents()

        from rem_card.app.logger import log_exception, logger as _logger, init_crash_handler
        from rem_card.app.bootstrap import bootstrap
        from rem_card.ui.main_window import MainWindow
        from rem_card.ui.styles.theme import GLOBAL_STYLE

        logger = _logger
        sys.excepthook = log_exception
        init_crash_handler()
        app.setStyleSheet(GLOBAL_STYLE)

        server = QLocalServer()
        server.listen(server_name)

        window = MainWindow(
            container=None,
            role=args.role,
            role_session_lock=role_lock,
            role_key=args.role if role_lock else None,
        )

        container = bootstrap()
        window.container = container
        logger.info("Bootstrap completed")

        splash.finish(window)
        window.show()

        def on_new_connection():
            client = server.nextPendingConnection()
            if client.waitForReadyRead(500):
                data = client.readAll().data().decode("utf-8")
                if data == "SHOW":
                    if window.isMinimized():
                        window.showNormal()
                    window.setWindowState(window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                    window.activateWindow()
                    window.raise_()
            client.disconnectFromServer()

        server.newConnection.connect(on_new_connection)

        exit_code = app.exec()
        logger.info("Application exiting with code %s", exit_code)
    except Exception as exc:
        if logger:
            logger.critical("Critical error during startup/runtime: %s", exc, exc_info=True)
        else:
            print(f"Critical startup error: {exc}")
        exit_code = 1
    finally:
        if window and logger:
            _shutdown_window_resources(window, logger)
        try:
            if window and hasattr(window, "release_role_lock"):
                window.release_role_lock()
            elif role_lock:
                role_lock.release()
        except Exception:
            pass

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
