from PyInstaller.utils.hooks import collect_all, collect_submodules

ursina_datas, ursina_binaries, ursina_hiddenimports = collect_all('ursina')
panda_datas, panda_binaries, panda_hiddenimports = collect_all('panda3d')
hiddenimports = sorted(set(ursina_hiddenimports + panda_hiddenimports + collect_submodules('ursina') + collect_submodules('panda3d')))

a = Analysis(['run.py'], pathex=['.'], binaries=ursina_binaries + panda_binaries, datas=ursina_datas + panda_datas, hiddenimports=hiddenimports, hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='MyGame', debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=True)
