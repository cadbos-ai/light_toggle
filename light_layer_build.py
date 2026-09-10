from .common import _centroid


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
    dist = torch.sqrt(dx * dx + dy * dy)
    radial = _falloff(dist, max(diag * reach, 1e-6), falloff)

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


LUM = (0.2126, 0.7152, 0.0722)

def _emitter(m, lin, lo=0.35, hi=0.75):
    """Внутри маски выделяет самосветящиеся пиксели по относительной яркости."""
    w = torch.tensor(LUM, device=lin.device, dtype=lin.dtype)
    lum = (lin * w).sum(-1)
    sel = m > 0.5
    if int(sel.sum()) == 0:
        return m * 0
    peak = float(torch.quantile(lum[sel], 0.98))
    if peak < 1e-4:
        return m * 0
    t = (lum / peak).clamp(0, 1)
    return ((t - lo) / max(hi - lo, 1e-3)).clamp(0, 1) * m


DEFAULTS = {
    "state": "on", "kelvin": 2700, "intensity": 0.85,
    "cone": 360, "dir_deg": 0, "reach": 0.35,
    "falloff": 3.0, "softness": 0.35,
    "bulb_gain": 0.9, "bulb_blur": 0.015,
}


DIFFUSE_SCALE  = 0.55   # во сколько конус умножает освещённость поверхностей
EMISSIVE_SCALE = 0.70   # аддитивное свечение тела светильника
OFF_CONE       = 0.75   # засветка вокруг
OFF_EMITTER    = 12.0   # сами лампочки — гасим жёстко
OFF_BODY       = 0.6    # корпус — только темнеет вместе с комнатой
OFF_TINT       = 0.5
OFF_REACH_MUL  = 1.7    # выключение гасит шире, чем включение освещает
OFF_FALLOFF    = 1.8
KNEE           = 0.75   # порог мягкой компрессии светов


def _falloff(dist, reach_px, k):
    """Обратный квадрат с конечным радиусом."""
    rn = dist / max(reach_px, 1e-6)
    inv = 1.0 / (1.0 + (rn * k) ** 2)
    cut = (1.0 - rn).clamp(0, 1) ** 0.5
    return inv * cut


def _knee(x, knee=KNEE):
    """Мягкое сжатие светов вместо clamp — белых пятен не возникает."""
    over = (x - knee).clamp(min=0.0)
    return torch.where(x > knee, knee + over / (1.0 + over / (1.0 - knee)), x)


class LightLayerBuild:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "masks": ("MASK",),
                "spec":  ("STRING", {"forceInput": True}),
                "start_at_step_lit":   ("INT", {"default": 5, "min": 0, "max": 20}),
                "start_at_step_off":   ("INT", {"default": 3, "min": 0, "max": 20}),
                "start_at_step_plain": ("INT", {"default": 0, "min": 0, "max": 20}),
            }
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "MASK", "INT", "STRING", "INT", "STRING")
    RETURN_NAMES = ("prelit", "lightmap", "affected",
                    "start_at_step", "report", "applied", "mode")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def run(self, image, masks, spec,
            start_at_step_lit, start_at_step_off, start_at_step_plain):
        img = image[0]                                  # [H,W,3]
        H, W, _ = img.shape
        dev, dt = img.device, img.dtype

        try:
            entries = json.loads(spec) if spec.strip() else []
        except json.JSONDecodeError as e:
            entries, spec_err = [], f"bad_json:{e.msg}"
        else:
            spec_err = ""
        if isinstance(entries, dict):
            entries = [entries]

        # одна запись раскатывается на все найденные маски (режим "все светильники")
        n_masks = int(masks.shape[0])
        if entries and n_masks > len(entries):
            entries = entries + [entries[-1]] * (n_masks - len(entries))

        diffuse  = torch.zeros(H, W, 3, device=dev, dtype=dt)
        emissive = torch.zeros(H, W, 3, device=dev, dtype=dt)
        dim      = torch.zeros(H, W, 3, device=dev, dtype=dt)
        affected = torch.zeros(H, W, device=dev, dtype=dt)

        notes = []
        applied_on = 0
        applied_off = 0

        lin = _srgb_to_linear(img)

        for i, raw in enumerate(entries):
            p = dict(DEFAULTS)
            p.update(raw if isinstance(raw, dict) else {})

            if i >= n_masks:
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
            inten = float(p["intensity"])

            if p["state"] == "on":
                diffuse  += cone.unsqueeze(-1) * rgb * inten * DIFFUSE_SCALE
                emissive += bulb.unsqueeze(-1) * rgb * inten * EMISSIVE_SCALE
                applied_on += 1
                notes.append(f"{i}:on_{int(p['kelvin'])}K_{int(p['cone'])}deg")
                bulb_used = bulb
            else:
                rgb_off = 1.0 - OFF_TINT * (1.0 - rgb)
                cone_off = _cone(H, W, cx, cy, p["dir_deg"], p["cone"],
                                 p["reach"] * OFF_REACH_MUL, OFF_FALLOFF,
                                 p["softness"], dev, dt)
                emit = _emitter(m, lin)
                body = (m - emit).clamp(0, 1)
                dim += (cone_off * OFF_CONE
                        + emit * OFF_EMITTER
                        + body * OFF_BODY).unsqueeze(-1) * rgb_off * inten
                applied_off += 1
                notes.append(f"{i}:off_e{float(emit.mean()):.3f}")
                bulb_used = emit

            affected = torch.maximum(affected, (cone + bulb_used).clamp(0, 1))

        lit = lin * (1.0 + diffuse) + emissive
        lit = lit / (1.0 + dim)
        prelit = _linear_to_srgb(_knee(lit.clamp(min=0.0))).clamp(0, 1)

        if applied_on > 0:
            mode, start = "lit", start_at_step_lit
        elif applied_off > 0:
            mode, start = "off", start_at_step_off
        else:
            mode, start = "plain", start_at_step_plain

        peak = float((diffuse + emissive).max())
        peak_dim = float(dim.max())
        report = (f"mode={mode} on={applied_on} off={applied_off} "
                  f"peak={peak:.3f} dim={peak_dim:.2f} start_at_step={start} "
                  + (spec_err + " " if spec_err else "")
                  + " ".join(notes))

        return (prelit.unsqueeze(0),
                (diffuse + emissive).clamp(0, 1).unsqueeze(0),
                affected.unsqueeze(0),
                start,
                report,
                applied_on + applied_off,
                mode)
