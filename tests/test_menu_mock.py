"""Exercises of_nuke.py / menu.py against a fake `nuke` module (no real Nuke here), and cross-checks every
knob name used by the gizmo against the parameters actually declared in Kernels/OF_Flare.blink."""
import json, os, re, sys, tempfile, types
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import of_core

# ---- parameters declared by the real kernel source
src = open(os.path.join(ROOT, "Kernels", "OF_Flare.blink"), encoding="utf-8").read()
decl = src[src.index("param:"):src.index("void define()")]
KERNEL = {}
for m in re.finditer(r"^\s*(float3|float2|float|int|bool)\s+(\w+);", decl, re.M):
    KERNEL[m.group(2)] = {"float3": 3, "float2": 2}.get(m.group(1), 1)
core_names = set(of_core.all_param_names())
assert core_names | {"lightPos", "animTime", "flareOnly"} == set(KERNEL), (
    "kernel/core mismatch", sorted((core_names | {"lightPos", "animTime", "flareOnly"}) ^ set(KERNEL)))
for n, v in of_core.preset_to_params({}).items():       # value shape must match the kernel type
    assert KERNEL[n] == (len(v) if isinstance(v, list) else 1), (n, v, KERNEL[n])
print("kernel declares %d params; core/UI names match, vector sizes match" % len(KERNEL))

# ---- fake nuke
class Knob:
    def __init__(self, name, n=1): self.name = name; self.vals = [0.0] * n; self.expr = {}; self.target = None; self.values = []
    def setValue(self, v, i=0):
        if isinstance(v, list): self.vals = list(v)
        else: self.vals[i] = v
    def value(self, i=0):
        return self.values[self.vals[0]] if self.values else self.vals[i]
    def arraySize(self): return len(self.vals)
    def execute(self): pass
    def setExpression(self, e, i=0): self.expr[i] = e
    def makeLink(self, node, knob): self.target = (node, knob)
    def setValues(self, v): self.values = list(v)

class Node:
    def __init__(self, cls, name=None, **kw):
        self.cls = cls; self._name = name or cls; self.k = {}; self.inputs = {}; self.children = {}; self.parent = None
        self.xy = (0, 0); self.kw = kw
        if cls == "BlinkScript":
            self.k = {n: Knob(n, s) for n, s in KERNEL.items()}
            for extra in ("kernelSourceFile", "recompile"): self.k[extra] = Knob(extra)
    def Class(self): return self.cls
    def name(self): return self._name
    def setName(self, n): self._name = n
    def fullName(self): return (self.parent.fullName() + "." if self.parent else "") + self._name
    def knob(self, n): return self.k.get(n)
    def __getitem__(self, n): return self.k[n]
    def addKnob(self, kn): self.k[kn.name] = kn
    def setInput(self, i, n): self.inputs[i] = n
    def begin(self): ctx.append(self)
    def end(self): ctx.pop()
    def setXYpos(self, x, y): self.xy = (x, y)
    def xpos(self): return self.xy[0]
    def ypos(self): return self.xy[1]
    def showControlPanel(self): pass
ctx = []
ALL = {}
def make(cls, **kw):
    n = Node(cls, **kw)
    if ctx: n.parent = ctx[-1]; ctx[-1].children[n._name] = n
    ALL[n.fullName()] = n
    return n
class Nodes:
    def __getattr__(self, cls): return lambda **kw: make(cls, **kw)

def knob_factory(label_idx=1):
    def f(name, label="", *a):
        kn = Knob(name, {"XY_Knob": 2}.get(f.cls, 1)); kn.label = label; kn.cls = f.cls; kn.extra = a; return kn
    return f
nuke = types.ModuleType("nuke")
for cls in ("Tab_Knob", "XY_Knob", "Text_Knob", "Double_Knob", "Enumeration_Knob", "PyScript_Knob", "Link_Knob"):
    def mk(cls=cls):
        def f(name, label="", *a):
            kn = Knob(name, 2 if cls == "XY_Knob" else 1); kn.label = label; kn.cls = cls
            if cls == "Enumeration_Knob": kn.setValues(a[0] if a else []); kn.vals = [0]
            return kn
        return f
    setattr(nuke, cls, mk())
nuke.nodes = Nodes()
nuke.toNode = lambda full: ALL.get(full)
class Menu:
    def __init__(self): self.items = {}
    def addMenu(self, n): return self.items.setdefault(n, Menu())
    def addCommand(self, n, f=None): self.items[n] = f
    def addSeparator(self): pass
    def clearMenu(self): self.items.clear()
root_menu = Menu()
nuke.menu = lambda name: root_menu
nuke.warning = lambda m: print("WARN", m)
nuke.tprint = print
nuke.message = lambda m: print("MSG", m)
nuke.getInput = lambda q, d: "My Look Å"
nuke.getFilename = lambda m: "/tex/" + ("dirt.exr" if "dirt" in m else "aperture.png")
class Fmt: width = lambda s: 1920; height = lambda s: 1080
nuke.root = lambda: types.SimpleNamespace(format=lambda: Fmt())
nuke.NUKE_VERSION_MAJOR = 16
sel = {"nodes": []}
nuke.selectedNodes = lambda: sel["nodes"]
def selectedNode():
    if not sel["nodes"]: raise ValueError
    return sel["nodes"][0]
nuke.selectedNode = selectedNode
nuke.thisNode = lambda: sel["nodes"][0]
sys.modules["nuke"] = nuke

tmp = tempfile.mkdtemp()
import menu, of_nuke                                   # menu.py builds the menu on import
of_nuke.USER_PRESETS = tmp
of_nuke.build_menu()
sub = root_menu.items["OpenFlares"]
bundled = len([f for f in os.listdir(os.path.join(ROOT, "Presets")) if f.endswith(".json")])
assert len(sub.items["New Flare from Preset"].items) == bundled
print("menu entries:", list(sub.items), "| bundled presets:", bundled)

# 1. create from every preset; check inner node, links and values
for name, path in of_core.list_presets(of_nuke.BUNDLED_PRESETS):
    ALL.clear(); ctx.clear()
    sub.items["New Flare from Preset"].items[name]()
    g = [n for n in ALL.values() if n.cls == "Group"][0]
    sel["nodes"] = [g]
    blink = of_nuke.inner_blink(g)
    assert blink is not None and blink.cls == "BlinkScript"
    assert blink.inputs == {0: ALL[g.fullName() + ".src"], 1: ALL[g.fullName() + ".dirt"], 2: ALL[g.fullName() + ".aperture"]}
    want = of_core.preset_to_params(of_core.load_preset(path))
    for k, v in want.items():
        got = of_nuke._get_knob(blink, k)
        ok = all(abs(a - b) < 1e-6 for a, b in zip(got, v)) if isinstance(v, list) else abs(got - v) < 1e-6
        assert ok, (name, k, got, v)
print("all %d presets: gizmo created, inner inputs wired, every value read back identical" % bundled)

# 2. UI: every link points at a real inner knob; tabs exist; light handle + animation expressions
links = [k for k in g.k.values() if k.cls == "Link_Knob"]
for l in links:
    assert l.target[0] == blink.fullName() and l.target[1] in KERNEL, l.target
linked = {l.name for l in links}
assert linked == (core_names | {"flareOnly"}), sorted(linked ^ (core_names | {"flareOnly"}))
tabs = [k.label for k in g.k.values() if k.cls == "Tab_Knob"]
print("tabs:", tabs, "| link knobs:", len(links))
assert blink["lightPos"].expr == {0: "parent.lightPos.x", 1: "parent.lightPos.y"}
assert blink["animTime"].expr[0] == "frame + parent.anim_offset"
assert g.k["lightPos"].vals == [1344.0, 756.0]

# 3. customise -> save (via gizmo button) -> reload choices -> apply from dropdown
blink["ghost1_intensity"].setValue(0.5); blink["ghost1_shape"].setValue(3); blink["master"].setValue(1.7)
blink["flicker_amount"].setValue(0.4); blink["spin_streak"].setValue(True)
blink["dirt_amount"].setValue(0.6); blink["dirt_offset"].setValue(0.1, 0)
of_nuke.save_preset(g)
files = os.listdir(tmp); print("saved:", files)
saved = json.load(open(os.path.join(tmp, files[0]), encoding="utf-8"))
assert saved["name"] == "My Look Å" and saved["master"] == 1.7
assert saved["ghosts"][0]["shape"] == "custom" and saved["animation"]["flicker"] == 0.4 and saved["animation"]["spin_streak"] is True
assert saved["dirt"]["amount"] == 0.6 and saved["dirt"]["offset"][0] == 0.1
assert "My Look Å" in g["preset_choice"].values
g["preset_choice"].vals = [g["preset_choice"].values.index("My Look Å")]
blink["master"].setValue(1.0)
of_nuke.apply_choice(g)
assert abs(blink["master"].value() - 1.7) < 1e-9
print("save / reload / apply-from-dropdown round trip OK")

# 4. textures helper wires Reads and switches ghosts to custom
ALL.clear(); ctx.clear(); sel["nodes"] = []
g2 = of_nuke.create_flare_with_textures()
assert g2.inputs[1].kw["file"] == "/tex/dirt.exr" and g2.inputs[2].kw["file"] == "/tex/aperture.png"
b2 = of_nuke.inner_blink(g2)
assert of_nuke._get_knob(b2, "dirt_amount") == 0.5
assert of_nuke._get_knob(b2, "ghost1_shape") == 3 and of_nuke._get_knob(b2, "ghost8_shape") == 0
print("texture helper OK")
