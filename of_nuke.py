"""OpenFlares - Nuke side (Nuke 14+, Python 3). Import-safe: building the menu is done by menu.py."""
import os
import re

import nuke

import of_core

VERSION = "0.2.0"
MIN_MAJOR = 14          # only the MAJOR version matters; minor/patch releases are never checked

_HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
KERNEL_FLARE = _HERE + "/Kernels/OF_Flare.blink"
KERNEL_STREAK = _HERE + "/Kernels/OF_AnamorphicStreak.blink"
BUNDLED_PRESETS = _HERE + "/" + of_core.PRESET_DIR_NAME
USER_PRESETS = os.path.join(os.path.expanduser("~"), ".nuke", "OpenFlares_Presets").replace("\\", "/")
DEFAULT_PRESET = "01_anamorphic_blue.json"
INNER = "OF_Blink"      # name of the BlinkScript node inside the gizmo


def check_nuke_version():
    """Warn (never block) on an older major version. Minor/patch versions are ignored on purpose."""
    major = getattr(nuke, "NUKE_VERSION_MAJOR", None)
    if isinstance(major, int) and major < MIN_MAJOR:
        nuke.warning("OpenFlares %s targets Nuke %d+; found Nuke %d. It may not load correctly."
                     % (VERSION, MIN_MAJOR, major))


# --------------------------------------------------------------------------- knob helpers
def _set_knob(node, name, value):
    knob = node.knob(name)
    if knob is None:
        return False
    if isinstance(value, (list, tuple)):
        for i, x in enumerate(value):
            knob.setValue(float(x), i)
    elif isinstance(value, bool):
        knob.setValue(value)
    elif isinstance(value, int):
        knob.setValue(int(value))
    else:
        knob.setValue(float(value))
    return True


def _get_knob(node, name):
    knob = node.knob(name)
    if knob is None:
        return None
    try:
        n = knob.arraySize()
    except Exception:
        n = 1
    if n and n > 1:
        return [knob.value(i) for i in range(n)]
    return knob.value()


def _is_flare(node):
    return node is not None and node.Class() == "Group" and node.knob("of_marker") is not None


def inner_blink(group):
    return nuke.toNode(group.fullName() + "." + INNER)


def _selected_flare():
    try:
        node = nuke.selectedNode()
    except ValueError:
        node = None
    if not _is_flare(node):
        nuke.message("Select an OpenFlares node first.")
        return None
    return node


# --------------------------------------------------------------------------- gizmo construction
def _add(group, knob):
    group.addKnob(knob)
    return knob


def _link(group, blink, name):
    lk = nuke.Link_Knob(name, of_core.label(name))
    try:
        lk.makeLink(blink.fullName(), name)
    except Exception:
        lk.setLink(blink.fullName() + "." + name)
    return _add(group, lk)


def _preset_names():
    return [n for n, _ in of_core.list_presets(BUNDLED_PRESETS, USER_PRESETS)]


def _build_ui(group, blink):
    fmt = nuke.root().format()

    # ---- Flare tab (light position is a real XY knob on the gizmo so the viewer handle works)
    _add(group, nuke.Tab_Knob("tab_flare", "Flare"))
    xy = _add(group, nuke.XY_Knob("lightPos", "Light Position"))
    xy.setValue(fmt.width() * 0.7, 0)
    xy.setValue(fmt.height() * 0.7, 1)
    blink["lightPos"].setExpression("parent.lightPos.x", 0)
    blink["lightPos"].setExpression("parent.lightPos.y", 1)

    for title, groups in [(t, g) for t, g in of_core.ui_tabs()]:
        if title != "Flare":
            _add(group, nuke.Tab_Knob("tab_" + re.sub(r"\W+", "_", title).lower(), title))
        for gtitle, names in groups:
            if gtitle:
                _add(group, nuke.Text_Knob("hdr_" + re.sub(r"\W+", "_", gtitle).lower(), "<b>%s</b>" % gtitle, ""))
            for name in names:
                _link(group, blink, name)
        if title == "Flare":
            _link(group, blink, "flareOnly")
        if title == "Animation":
            off = _add(group, nuke.Double_Knob("anim_offset", "Animation Time Offset"))
            off.setValue(0.0)
            blink["animTime"].setExpression("frame + parent.anim_offset")
        if title == "Textures":
            _add(group, nuke.Text_Knob(
                "tex_help", "",
                "dirt input: dust / scratches / grain, lit by the glow.\n"
                "aperture input: custom ghost shape (white on black). Set a ghost's Shape to 3."))

    # ---- Presets tab
    _add(group, nuke.Tab_Knob("tab_presets", "Presets"))
    _add(group, nuke.Enumeration_Knob("preset_choice", "Preset", _preset_names()))
    _add(group, nuke.PyScript_Knob("apply_btn", "Apply Preset", "import of_nuke; of_nuke.apply_choice(nuke.thisNode())"))
    _add(group, nuke.PyScript_Knob("save_btn", "Save Current Look as Preset...", "import of_nuke; of_nuke.save_preset(nuke.thisNode())"))
    _add(group, nuke.PyScript_Knob("reload_btn", "Reload Preset List", "import of_nuke; of_nuke.reload_choices(nuke.thisNode())"))
    _add(group, nuke.Text_Knob("of_marker", "OpenFlares v%s" % VERSION, ""))


# --------------------------------------------------------------------------- actions
def apply_preset(group, preset):
    """Write every kernel parameter of `preset` onto the gizmo's BlinkScript node."""
    blink = inner_blink(group)
    missing = [n for n, v in of_core.preset_to_params(preset).items() if not _set_knob(blink, n, v)]
    if missing:
        nuke.warning("OpenFlares: knobs not found: %s" % ", ".join(missing[:8]))
    return missing


def create_flare(preset_path=None):
    try:
        sel = nuke.selectedNodes()
    except Exception:
        sel = []
    source = sel[0] if sel else None

    group = nuke.nodes.Group(name="OF_Flare")
    group.begin()
    try:
        i_src = nuke.nodes.Input(name="src")
        i_dirt = nuke.nodes.Input(name="dirt")
        i_ap = nuke.nodes.Input(name="aperture")
        blink = nuke.nodes.BlinkScript(name=INNER)
        blink.setInput(0, i_src)
        blink.setInput(1, i_dirt)
        blink.setInput(2, i_ap)
        blink["kernelSourceFile"].setValue(KERNEL_FLARE)
        blink["recompile"].execute()
        blink["animTime"].setExpression("frame")
        nuke.nodes.Output(name="Output1").setInput(0, blink)
    finally:
        group.end()

    _build_ui(group, blink)
    path = preset_path or (BUNDLED_PRESETS + "/" + DEFAULT_PRESET)
    if os.path.exists(path):
        apply_preset(group, of_core.load_preset(path))
    if source is not None:
        group.setInput(0, source)
        group.setXYpos(source.xpos(), source.ypos() + 90)
    group.showControlPanel()
    return group


def create_flare_with_textures():
    """New flare; asks for an optional dirt texture and an optional custom ghost aperture."""
    dirt_path = nuke.getFilename("Dust / scratch / grain texture for the 'dirt' input (Cancel to skip)")
    ap_path = nuke.getFilename("Custom ghost shape for the 'aperture' input, white on black (Cancel to skip)")
    group = create_flare()
    if dirt_path:
        rd = nuke.nodes.Read(file=dirt_path)
        rd.setXYpos(group.xpos() - 160, group.ypos() - 60)
        group.setInput(1, rd)
        blink = inner_blink(group)
        if not _get_knob(blink, "dirt_amount"):
            _set_knob(blink, "dirt_amount", 0.5)
    if ap_path:
        rd = nuke.nodes.Read(file=ap_path)
        rd.setXYpos(group.xpos() - 80, group.ypos() - 60)
        group.setInput(2, rd)
        blink = inner_blink(group)
        for i in range(1, of_core.N_GHOST + 1):
            if (_get_knob(blink, "ghost%d_intensity" % i) or 0) > 0:
                _set_knob(blink, "ghost%d_shape" % i, 3)
    return group


def apply_choice(group):
    name = group["preset_choice"].value()
    for n, path in of_core.list_presets(BUNDLED_PRESETS, USER_PRESETS):
        if n == name:
            apply_preset(group, of_core.load_preset(path))
            return
    nuke.warning("OpenFlares: preset '%s' not found" % name)


def reload_choices(group):
    group["preset_choice"].setValues(_preset_names())


def apply_preset_to_selected(preset_path):
    node = _selected_flare()
    if node is not None:
        apply_preset(node, of_core.load_preset(preset_path))


def save_preset(group=None):
    group = group or _selected_flare()
    if group is None:
        return
    name = nuke.getInput("Preset name:", "My Flare")
    if not name:
        return
    blink = inner_blink(group)
    values = {n: _get_knob(blink, n) for n in of_core.all_param_names()}
    values = {k: v for k, v in values.items() if v is not None}
    preset = of_core.params_to_preset(values, name)
    filename = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_") or "preset"
    path = of_core.save_preset(preset, USER_PRESETS, filename + ".json")
    nuke.tprint("OpenFlares: saved %s" % path)
    reload_choices(group)
    build_menu()


def create_streak_from_source():
    node = nuke.createNode("BlinkScript", inpanel=False)
    node["kernelSourceFile"].setValue(KERNEL_STREAK)
    node["recompile"].execute()
    node.setName("OF_AnamorphicStreak")
    node.showControlPanel()
    return node


# --------------------------------------------------------------------------- menu
def build_menu():
    root = nuke.menu("Nodes").addMenu("OpenFlares")
    root.clearMenu()
    root.addCommand("New Flare", create_flare)
    root.addCommand("New Flare with Textures...", create_flare_with_textures)
    presets = of_core.list_presets(BUNDLED_PRESETS, USER_PRESETS)

    new_menu = root.addMenu("New Flare from Preset")
    apply_menu = root.addMenu("Apply Preset to Selected Flare")
    for name, path in presets:
        new_menu.addCommand(name, lambda p=path: create_flare(p))
        apply_menu.addCommand(name, lambda p=path: apply_preset_to_selected(p))

    root.addSeparator()
    root.addCommand("Save Selected Flare as Preset...", save_preset)
    root.addCommand("Anamorphic Streak (from source brightness)", create_streak_from_source)
