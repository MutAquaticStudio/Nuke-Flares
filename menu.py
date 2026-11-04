"""OpenFlares menu entry point. Nuke runs this file once the plugin folder is on the plugin path:
    nuke.pluginAddPath("/path/to/OpenFlares")   # in ~/.nuke/init.py
All the logic lives in of_nuke.py (importable without side effects)."""
import of_nuke

of_nuke.check_nuke_version()
of_nuke.build_menu()
