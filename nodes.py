import re, json, math, torch


class LightIntentParse:
    ACTION_OFF = [r"\bвыключ", r"\bвыкл\b", r"\bпогас", r"\bпогаш",
                  r"\bпотуш", r"\bтуш", r"\bвыруб", r"\bгаси\b", r"\bубер"]
    ACTION_ON  = [r"\bзажг", r"\bзажеч", r"\bвключ", r"\bвруб",
                  r"\bзапуст", r"\bдобав\w*\s+свет"]
    SCOPE_ALL  = [r"\bвс[еяю]\b", r"\bвесь\b", r"\bвсех\b", r"\bполностью\b"]

    OBJECTS = [
        (r"\bлюстр",                 "chandelier"),
        (r"\bподвес",                "pendant lamp"),
        (r"\bбра\b",                 "wall sconce"),
        (r"\bторшер",                "floor lamp"),
        (r"\bнастольн\w*\s+ламп",    "table lamp"),
        (r"\bспот",                  "spotlight"),
        (r"\bгирлянд",               "string lights"),
        (r"\bподсветк",              "led strip"),
        (r"\bлампоч",                "light bulb"),
        (r"\bламп",                  "lamp"),
        (r"\bсветильник",            "lighting fixture"),
        (r"\bокн|\bокош",            "window"),
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "instruction": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "fallback_object": ("STRING", {"default": "lighting fixture"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "BOOLEAN", "STRING", "STRING")
    RETURN_NAMES = ("object_en", "action", "scope", "parsed", "status", "summary")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def run(self, instruction, fallback_object="lighting fixture"):
        t = instruction.lower().replace("ё", "е").strip()

        # порядок важен: OFF проверяется первым, но \b и так разводит
        # "выключи" и "включи" — внутри "выключи" границы слова перед "включ" нет
        if any(re.search(p, t) for p in self.ACTION_OFF):
            action = "off"
        elif any(re.search(p, t) for p in self.ACTION_ON):
            action = "on"
        else:
            action = ""

        scope = "all" if any(re.search(p, t) for p in self.SCOPE_ALL) else "single"

        object_en = ""
        for pat, en in self.OBJECTS:
            if re.search(pat, t):
                object_en = en
                break

        problems = []
        if not action:
            problems.append("no_action")
        if not object_en and scope != "all":
            problems.append("no_object")

        if not object_en:
            object_en = fallback_object

        parsed = len(problems) == 0
        status = "ok" if parsed else "+".join(problems)
        summary = f"object={object_en} | action={action or '-'} | scope={scope} | {status}"

        return (object_en, action or "unknown", scope, parsed, status, summary)


class MaskArea:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "mask": ("MASK",),
            "min_fraction": ("FLOAT", {"default": 0.0008, "min": 0.0, "max": 1.0, "step": 0.0001}),
            "max_fraction": ("FLOAT", {"default": 0.15,   "min": 0.0, "max": 1.0, "step": 0.001}),
        }}
    RETURN_TYPES = ("FLOAT", "INT", "BOOLEAN", "STRING")
    RETURN_NAMES = ("fraction", "pixels", "found", "status")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def run(self, mask, min_fraction, max_fraction):
        m = (mask[0] > 0.5).float()
        px = int(m.sum().item())
        frac = px / max(m.numel(), 1)
        if frac < min_fraction:
            return (frac, px, False, "absent")
        if frac > max_fraction:
            return (frac, px, False, "too_large")
        return (frac, px, True, "found")


def _slug(s, maxlen=72):
    s = "".join(c if c.isalnum() or c in "_-+." else "_" for c in str(s))
    s = s.strip("._")
    return s[:maxlen] or "x"


class LightGate:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "parsed":        ("BOOLEAN", {"forceInput": True}),
                "intent_status": ("STRING",  {"forceInput": True}),
                "scope":         ("STRING",  {"forceInput": True}),
            },
            "optional": {
                "found":       ("BOOLEAN", {"forceInput": True, "lazy": True}),
                "mask_status": ("STRING",  {"forceInput": True, "lazy": True}),
                "prefix_root": ("STRING",  {"default": "lt"}),
                "run_tag":     ("STRING",  {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("BOOLEAN", "STRING", "STRING")
    RETURN_NAMES = ("proceed", "status", "filename_prefix")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def _short_circuit(self, parsed, scope):
        return (not parsed) or scope == "all"

    def check_lazy_status(self, parsed, intent_status, scope,
                          found=None, mask_status=None,
                          prefix_root="lt", run_tag=""):
        if self._short_circuit(parsed, scope):
            return []
        need = []
        if found is None:
            need.append("found")
        if mask_status is None:
            need.append("mask_status")
        return need

    def run(self, parsed, intent_status, scope,
            found=None, mask_status=None, prefix_root="lt", run_tag=""):
        if not parsed:
            proceed, status = False, f"reject_intent_{intent_status}"
        elif scope == "all":
            proceed, status = True, "ok_all"
        elif found is None:
            proceed, status = False, "reject_no_detector"
        elif not found:
            proceed, status = False, f"reject_{mask_status or 'absent'}"
        else:
            proceed, status = True, "ok"

        bucket = "reject" if status.startswith("reject") else "ok"
        prefix = "/".join([
            _slug(prefix_root),
            bucket,
            _slug(status),
            _slug(run_tag or "run"),
        ])
        return (proceed, status, prefix)


class LightImageBranch:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "proceed":  ("BOOLEAN", {"forceInput": True}),
                "on_true":  ("IMAGE", {"lazy": True}),
                "on_false": ("IMAGE", {"lazy": True}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def check_lazy_status(self, proceed, on_true=None, on_false=None):
        if proceed:
            return [] if on_true is not None else ["on_true"]
        return [] if on_false is not None else ["on_false"]

    def run(self, proceed, on_true=None, on_false=None):
        return (on_true if proceed else on_false,)


def _srgb_to_linear(x):
    return torch.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def _linear_to_srgb(x):
    x = x.clamp(min=0.0)
    return torch.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055)


def kelvin_to_rgb(k):
    """Аппроксимация Таннера Хелланда, нормирована по максимальному каналу."""
    t = max(1000.0, min(40000.0, float(k))) / 100.0
    if t <= 66:
        r = 255.0
        g = 99.4708025861 * math.log(t) - 161.1195681661
    else:
        r = 329.698727446 * ((t - 60) ** -0.1332047592)
        g = 288.1221695283 * ((t - 60) ** -0.0755148492)
    if t >= 66:
        b = 255.0
    elif t <= 19:
        b = 0.0
    else:
        b = 138.5177312231 * math.log(t - 10) - 305.0447927307
    rgb = [max(0.0, min(255.0, v)) / 255.0 for v in (r, g, b)]
    m = max(rgb) or 1.0
    return [v / m for v in rgb]


def _centroid(mask):
    """mask: [H,W] float. Возвращает (cx, cy) или None."""
    s = mask.sum()
    if s < 1e-6:
        return None
    H, W = mask.shape
    ys = torch.arange(H, device=mask.device, dtype=mask.dtype).view(H, 1)
    xs = torch.arange(W, device=mask.device, dtype=mask.dtype).view(1, W)
    cx = float((mask * xs).sum() / s)
    cy = float((mask * ys).sum() / s)
    return cx, cy


def _cone(H, W, cx, cy, dir_deg, cone_deg, reach, falloff, softness, device, dtype):
    """dir_deg: 0=вниз, 90=вправо, 180=вверх, 270=влево."""
    ys = torch.arange(H, device=device, dtype=dtype).view(H, 1)
    xs = torch.arange(W, device=device, dtype=dtype).view(1, W)
    dx, dy = xs - cx, ys - cy

    diag = math.hypot(W, H)
    r = torch.sqrt(dx * dx + dy * dy) / max(diag * reach, 1e-6)
    radial = (1.0 - r).clamp(0, 1) ** max(falloff, 1e-3)

    if cone_deg >= 359.0:
        return radial

    theta = torch.atan2(dy, dx)                       # 0 = вправо, растёт вниз
    aim = math.radians(90.0 - dir_deg)                # перевод в ту же систему
    d = torch.remainder(theta - aim + math.pi, 2 * math.pi) - math.pi
    half = math.radians(cone_deg) / 2.0
    edge = max(half * softness, 1e-3)
    ang = ((half + edge - d.abs()) / (2 * edge)).clamp(0, 1)
    return radial * ang


def _blur(x, radius):
    """Разделимое усреднение по боксу, два прохода ≈ гаусс."""
    if radius < 1:
        return x
    k = int(radius) * 2 + 1
    t = x.view(1, 1, *x.shape)
    ker_h = torch.ones(1, 1, 1, k, device=x.device, dtype=x.dtype) / k
    ker_v = torch.ones(1, 1, k, 1, device=x.device, dtype=x.dtype) / k
    for _ in range(2):
        t = torch.nn.functional.conv2d(t, ker_h, padding=(0, k // 2))
        t = torch.nn.functional.conv2d(t, ker_v, padding=(k // 2, 0))
    return t.view(*x.shape)


DEFAULTS = {
    "state": "on", "kelvin": 2700, "intensity": 0.85,
    "cone": 360, "dir_deg": 0, "reach": 0.55,
    "falloff": 2.0, "softness": 0.35, "bulb_gain": 2.0, "bulb_blur": 0.02,
}


class LightLayerBuild:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "masks": ("MASK",),
                "spec":  ("STRING", {"forceInput": True}),
                "start_at_step_lit":   ("INT", {"default": 5, "min": 0, "max": 20}),
                "start_at_step_plain": ("INT", {"default": 0, "min": 0, "max": 20}),
            }
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "MASK", "INT", "STRING")
    RETURN_NAMES = ("prelit", "lightmap", "affected", "start_at_step", "report")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def run(self, image, masks, spec, start_at_step_lit, start_at_step_plain):
        img = image[0]                                  # [H,W,3]
        H, W, _ = img.shape
        dev, dt = img.device, img.dtype

        try:
            entries = json.loads(spec) if spec.strip() else []
        except json.JSONDecodeError as e:
            entries = []
            spec_err = f"bad_json:{e.msg}"
        else:
            spec_err = ""
        if isinstance(entries, dict):
            entries = [entries]

        lightmap = torch.zeros(H, W, 3, device=dev, dtype=dt)
        affected = torch.zeros(H, W, device=dev, dtype=dt)
        notes, applied = [], 0

        for i, raw in enumerate(entries):
            p = dict(DEFAULTS)
            p.update(raw if isinstance(raw, dict) else {})
            if p["state"] != "on":
                notes.append(f"{i}:skip_{p['state']}")
                continue
            if i >= masks.shape[0]:
                notes.append(f"{i}:no_mask")
                continue

            m = masks[i].to(dev).to(dt)
            c = _centroid(m)
            if c is None:
                notes.append(f"{i}:empty_mask")
                continue
            cx, cy = c

            cone = _cone(H, W, cx, cy, p["dir_deg"], p["cone"], p["reach"],
                         p["falloff"], p["softness"], dev, dt)

            bulb = _blur(m, int(max(H, W) * float(p["bulb_blur"]))) * float(p["bulb_gain"])

            rgb = torch.tensor(kelvin_to_rgb(p["kelvin"]), device=dev, dtype=dt)
            contrib = (cone + bulb).unsqueeze(-1) * rgb * float(p["intensity"])

            lightmap += contrib
            affected = torch.maximum(affected, (cone + bulb).clamp(0, 1))
            applied += 1
            notes.append(f"{i}:ok_{int(p['kelvin'])}K_{int(p['cone'])}deg")

        lin = _srgb_to_linear(img)
        prelit = _linear_to_srgb(lin + lightmap).clamp(0, 1)

        start = start_at_step_lit if applied > 0 else start_at_step_plain
        report = f"applied={applied} start_at_step={start} " + \
                 (spec_err + " " if spec_err else "") + " ".join(notes)

        return (prelit.unsqueeze(0),
                lightmap.clamp(0, 1).unsqueeze(0),
                affected.unsqueeze(0),
                start,
                report)
