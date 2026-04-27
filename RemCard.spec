# -*- mode: python ; coding: utf-8 -*-

import os
import shutil

block_cipher = None

APP_ROOT = os.path.abspath(SPECPATH)
PROJECT_ROOT = os.path.dirname(APP_ROOT)
DICTIONARIES_TARGET = os.path.join("rem_card", "data", "dictionaries")


def _data_dir(relative_path):
    return (
        os.path.join(APP_ROOT, relative_path),
        os.path.join("rem_card", relative_path),
    )


def _dictionary_json_datas():
    source_dir = os.path.join(APP_ROOT, "data", "dictionaries")
    if not os.path.isdir(source_dir):
        raise RuntimeError(f"Dictionaries directory not found: {source_dir}")

    result = []
    for name in sorted(os.listdir(source_dir)):
        source_path = os.path.join(source_dir, name)
        if os.path.isfile(source_path) and name.lower().endswith(".json"):
            result.append((source_path, DICTIONARIES_TARGET))
    return result

a = Analysis(
    [
        os.path.join(APP_ROOT, 'run_doctor.py'),
        os.path.join(APP_ROOT, 'run_nurse.py'),
        os.path.join(APP_ROOT, 'run_path_setup.py'),
    ],
    pathex=[PROJECT_ROOT, APP_ROOT],
    binaries=[],
	datas=[
		# иконки
		_data_dir('icon'),

		# dictionaries (json): базовый набор попадает в _internal,
		# при запуске приложения недостающие файлы копируются наружу рядом с exe.
		*_dictionary_json_datas(),

		# журнал — только нужное
		_data_dir('Rao_jornal/database'),
		_data_dir('Rao_jornal/assets'),
		_data_dir('Rao_jornal/fonts'),
		_data_dir('Rao_jornal/mkb'),
],
    hiddenimports=['rem_card.Rao_jornal.main'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

def _script_toc(script_name):
    normalized = os.path.normcase(script_name)
    for item in a.scripts:
        candidate = os.path.normcase(os.path.basename(item[1] if len(item) > 1 else item[0]))
        if candidate == normalized:
            return [item]
    raise RuntimeError(f"Entry script not found in Analysis: {script_name}")


doctor_exe = EXE(
    pyz,
    _script_toc('run_doctor.py'),
    [],
    exclude_binaries=True,
    name='RemCardDoctor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=[os.path.join(APP_ROOT, 'icon', 'doctor.ico')],
)

nurse_exe = EXE(
    pyz,
    _script_toc('run_nurse.py'),
    [],
    exclude_binaries=True,
    name='RemCardNurse',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=[os.path.join(APP_ROOT, 'icon', 'nurse.ico')],
)

path_setup_exe = EXE(
    pyz,
    _script_toc('run_path_setup.py'),
    [],
    exclude_binaries=True,
    name='RemCardPathSetup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=[os.path.join(APP_ROOT, 'icon', 'remcardicon.ico')],
)

coll = COLLECT(
    doctor_exe,
    nurse_exe,
    path_setup_exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Prog',
)

# === POST BUILD ===

print("===> Post-build: Moving files to target directory <===")

build_root = os.path.dirname(globals().get('WARNFILE', os.path.join(PROJECT_ROOT, 'build', 'RemCard', 'warn-RemCard.txt')))
dist_root = globals().get('DISTPATH', os.path.join(APP_ROOT, 'dist'))
dist_dir = os.path.join(dist_root, 'Prog')
target_dir = os.path.abspath(os.path.join(PROJECT_ROOT, 'Baza_rao3_jurnal', 'Prog'))

if os.path.exists(dist_dir):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    print(f"Moving contents of {dist_dir} to {target_dir}...")

    # Убираем старые исполняемые файлы и старую _internal, но сохраняем
    # remcard_data_path.json и локальные logs.
    for stale_exe in ('RemCard.exe', 'RemCardDoctor.exe', 'RemCardNurse.exe', 'RemCardPathSetup.exe'):
        stale_path = os.path.join(target_dir, stale_exe)
        if os.path.exists(stale_path):
            os.remove(stale_path)
    shutil.rmtree(os.path.join(target_dir, '_internal'), ignore_errors=True)

    # копирование с перезаписью
    shutil.copytree(dist_dir, target_dir, dirs_exist_ok=True)

    # очистка
    shutil.rmtree(os.path.dirname(build_root), ignore_errors=True)
    shutil.rmtree(dist_root, ignore_errors=True)
    shutil.rmtree(os.path.join(APP_ROOT, '__pycache__'), ignore_errors=True)

    print(f"===> Success! The applications are ready in {target_dir} <===")
else:
    print("Error: dist folder not found")
