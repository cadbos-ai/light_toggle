from common import _centroid


import json, math, torch


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

    RETURN_TYPES = ("IMAGE", "IMAGE", "MASK", "INT", "STRING", "INT")
    RETURN_NAMES = ("prelit", "lightmap", "affected",
                    "start_at_step", "report", "applied")
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
                report,
                applied)
