import ctypes
import os
import socket
import sys


def _show_native_warning(title: str, message: str):
    try:
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
    except Exception:
        print(f"{title}: {message}")


def _acquire_journal_lock():
    from rem_card.app.paths import get_role_lock_path
    from rem_card.app.role_session_lock import RoleSessionLock

    lock = RoleSessionLock(
        lock_path=get_role_lock_path("jornal"),
        role="jornal",
        owner_id=f"{socket.gethostname()}:{os.getpid()}:jornal_startup",
        stale_timeout_sec=60.0,
        heartbeat_sec=8.0,
    )
    if lock.acquire():
        return lock

    holder = lock.describe_holder()
    _show_native_warning("Роль занята", f"Журнал уже открыт на другом ПК.\n\n{holder}")
    return None


def run_jornal():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtNetwork import QLocalServer, QLocalSocket
    from PySide6.QtCore import Qt, QTimer

    server_name = "rem_card_single_instance_server_jornal"
    socket_client = QLocalSocket()
    socket_client.connectToServer(server_name)
    if socket_client.waitForConnected(500):
        socket_client.write(b"SHOW")
        if socket_client.waitForBytesWritten(500):
            sys.exit(0)

    QLocalServer.removeServer(server_name)

    role_lock = _acquire_journal_lock()
    if role_lock is None:
        sys.exit(0)

    app = QApplication.instance() or QApplication(sys.argv)
    db_manager = None
    main_window = None
    exit_code = 1
    try:
        from PySide6.QtGui import QIcon
        from rem_card.Rao_jornal.ui.main_window import MainWindow
        from rem_card.Rao_jornal.database.db_manager import DBManager
        from rem_card.Rao_jornal.services.patient_service import PatientService
        from rem_card.Rao_jornal.config.settings import FONTS_DIR, ICONS_DIR, ASSETS_DIR

        server = QLocalServer()
        server.listen(server_name)

        def _load_fonts_deferred():
            from PySide6.QtGui import QFontDatabase, QFont

            font_dir = os.path.join(FONTS_DIR, "static")
            fonts_to_load = [
                "IBMPlexSans-Regular.ttf",
                "IBMPlexSans-Medium.ttf",
                "IBMPlexSans-SemiBold.ttf",
                "IBMPlexSans-Bold.ttf",
            ]

            loaded_family = None
            for font_file in fonts_to_load:
                path = os.path.join(font_dir, font_file)
                if not os.path.exists(path):
                    continue
                font_id = QFontDatabase.addApplicationFont(path)
                if font_id != -1 and not loaded_family:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    if families:
                        loaded_family = families[0]

            if loaded_family:
                global_font = QFont(loaded_family, 11)
                global_font.setStyleStrategy(QFont.PreferAntialias | QFont.PreferQuality)
                app.setFont(global_font)
                app.setStyleSheet(f"* {{ font-family: '{loaded_family}'; }}")

        db_manager = DBManager()
        patient_service = PatientService(db_manager)
        main_window = MainWindow(db_manager, patient_service)

        icon_path = os.path.join(ASSETS_DIR, "icons", "app_icon.ico")
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            app.setWindowIcon(app_icon)
            main_window.setWindowIcon(app_icon)
        else:
            alt_icon_path = os.path.join(ICONS_DIR, "remcardicon.ico")
            if os.path.exists(alt_icon_path):
                app_icon = QIcon(alt_icon_path)
                app.setWindowIcon(app_icon)
                main_window.setWindowIcon(app_icon)

        def on_new_connection():
            client = server.nextPendingConnection()
            if client.waitForReadyRead(500):
                data = client.readAll().data().decode("utf-8")
                if data == "SHOW":
                    if main_window.isMinimized():
                        main_window.showNormal()
                    main_window.setWindowState(main_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                    main_window.activateWindow()
                    main_window.raise_()
            client.disconnectFromServer()

        server.newConnection.connect(on_new_connection)

        main_window.show()
        QTimer.singleShot(0, _load_fonts_deferred)
        exit_code = app.exec()
    finally:
        from PySide6.QtCore import QThread, QTimer

        if main_window:
            for child in main_window.findChildren(QThread):
                if child.isRunning():
                    child.quit()
                    child.wait(500)
            for child in main_window.findChildren(QTimer):
                child.stop()

        try:
            if db_manager:
                db_manager.close_connection()
        except Exception:
            pass
        try:
            role_lock.release()
        except Exception:
            pass

    sys.exit(exit_code)


if __name__ == "__main__":
    run_jornal()
