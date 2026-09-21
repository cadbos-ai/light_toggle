import json, math, torch


from .common import _centroid


class MaskPickByLocation:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "masks":     ("MASK",),
                "anchor_en": ("STRING", {"forceInput": True}),
                "side":      ("STRING", {"forceInput": True}),
                "prior_json":("STRING", {"forceInput": True}),
            },
            "optional": {
                "anchor": ("MASK", {"lazy": True}),
                "scope":  ("STRING", {"forceInput": True}),
                "ambiguous_mode": (["all", "first"], {"default": "all"}),
            },
        }

    RETURN_TYPES = ("MASK", "STRING")
    RETURN_NAMES = ("mask", "status")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    CROP_AREA_RELAX = 2.5

    def _prior_ok(self, cent, area_frac, prior, H, ytop=None, cropped_top=False):
        if not prior:
            return True

        alo, ahi = prior.get("area", [0.0, 1.0])
        if cropped_top:
            ahi = min(1.0, ahi * self.CROP_AREA_RELAX)
        if not (alo <= area_frac <= ahi):
            return False

        if cropped_top:
            return True

        ylo, yhi = prior.get("y", [0.0, 1.0])
        if not (ylo <= cent[1] / max(H, 1) <= yhi):
            return False

        if ytop is not None and "ytop" in prior:
            tlo, thi = prior["ytop"]
            return tlo <= ytop <= thi

        return True

    def check_lazy_status(self, masks, anchor_en, side, prior_json,
                          anchor=None, **kw):
        if int(masks.shape[0]) <= 1:
            return []
        if not anchor_en.strip():
            return []
        return [] if anchor is not None else ["anchor"]

    def run(self, masks, anchor_en, side, prior_json, anchor=None,
            scope="single", ambiguous_mode="all"):
        n = int(masks.shape[0])
        if n == 0:
            return (masks, "empty")

        H, W = int(masks.shape[1]), int(masks.shape[2])
        try:
            prior = json.loads(prior_json) if prior_json.strip() else {}
        except json.JSONDecodeError:
            prior = {}

        cents = [_centroid(masks[i]) for i in range(n)]

        keep, info = [], []
        for i in range(n):
            if cents[i] is None:
                info.append(f"{i}:empty")
                continue

            rows = torch.nonzero(masks[i].sum(dim=1) > 0.5)
            if len(rows) == 0:
                info.append(f"{i}:empty")
                continue

            ytop_px = int(rows.min())
            cropped_top = ytop_px <= 2
            ytop = ytop_px / max(H, 1)
            af = float(masks[i].sum()) / max(H * W, 1)

            ok = self._prior_ok(cents[i], af, prior, H, ytop, cropped_top)
            info.append(f"{i}:y={cents[i][1]/max(H,1):.2f},"
                        f"t={ytop:.2f}{'*' if cropped_top else ''},"
                        f"a={af:.4f},{'ok' if ok else 'rej'}")
            if ok:
                keep.append(i)

        if not keep:
            empty = torch.zeros((1, H, W), device=masks.device, dtype=masks.dtype)
            return (empty, f"prior_reject_all_{n}[{' '.join(info)}]")

        masks = masks[keep]
        cents = [cents[i] for i in keep]
        n_kept = len(keep)

        if n_kept == 1:
            return (masks[:1], f"single_of_{n}")

        if anchor is not None and int(anchor.shape[0]) > 0:
            a = _centroid(anchor[0])
            if a is not None:
                best, bd = None, None
                for i, c in enumerate(cents):
                    if c is None:
                        continue
                    dd = math.hypot(c[0] - a[0], c[1] - a[1])
                    if bd is None or dd < bd:
                        best, bd = i, dd
                if best is not None:
                    return (masks[best:best + 1],
                            f"anchor_{anchor_en}_picked_{best}_of_{n_kept}")

        s = side.strip().lower()
        if s in ("left", "right", "top", "bottom"):
            key = {"left":  lambda c: c[0],  "right":  lambda c: -c[0],
                   "top":   lambda c: c[1],  "bottom": lambda c: -c[1]}[s]
            cand = sorted((key(c), i) for i, c in enumerate(cents) if c is not None)
            if cand:
                i = cand[0][1]
                return (masks[i:i + 1], f"side_{s}_picked_{i}_of_{n_kept}")

        if scope == "all" or ambiguous_mode == "all":
            return (masks, f"all_{n_kept}_of_{n}")
        return (masks[:1], f"ambiguous_{n_kept}_took_0")
