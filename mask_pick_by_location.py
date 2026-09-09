import json, math, torch


from common import _centroid


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
            },
        }

    RETURN_TYPES = ("MASK", "STRING")
    RETURN_NAMES = ("mask", "status")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def _prior_ok(self, cent, area_frac, prior, H):
        if not prior:
            return True
        ylo, yhi = prior.get("y", [0.0, 1.0])
        alo, ahi = prior.get("area", [0.0, 1.0])
        return (ylo <= cent[1] / max(H, 1) <= yhi) and (alo <= area_frac <= ahi)

    def check_lazy_status(self, masks, anchor_en, side, prior_json, anchor=None):
        if int(masks.shape[0]) <= 1:      # выбирать не из чего
            return []
        if not anchor_en.strip():         # якоря нет — обойдёмся стороной
            return []
        if not prior_json.strip():
            return []
        return [] if anchor is not None else ["anchor"]

    def run(self, masks, anchor_en, side, prior_json, anchor=None):
        n = int(masks.shape[0])
        if n == 0:
            return (masks, "empty")
        if n == 1:
            return (masks[:1], "single")

        cents = [_centroid(masks[i]) for i in range(n)]

        if anchor is not None and int(anchor.shape[0]) > 0:
            a = _centroid(anchor[0])
            if a is not None:
                best, bd = None, None
                for i, c in enumerate(cents):
                    if c is None:
                        continue
                    d = math.hypot(c[0] - a[0], c[1] - a[1])
                    if bd is None or d < bd:
                        best, bd = i, d
                if best is not None:
                    return (masks[best:best + 1],
                            f"anchor_{anchor_en}_picked_{best}_of_{n}")

        H, W = int(masks.shape[1]), int(masks.shape[2])
        try:
            prior = json.loads(prior_json) if prior_json.strip() else {}
        except json.JSONDecodeError:
            prior = {}

        keep = []
        for i in range(n):
            if cents[i] is None:
                continue
            af = float(masks[i].sum()) / max(H * W, 1)
            if self._prior_ok(cents[i], af, prior, H):
                keep.append(i)

        if not keep:
            empty = torch.zeros((1, H, W), device=masks.device, dtype=masks.dtype)
            return (empty, f"prior_reject_all_{n}")

        masks = masks[keep]
        cents = [cents[i] for i in keep]
        n = len(keep)

        s = side.strip().lower()
        if s in ("left", "right", "top", "bottom"):
            key = {"left":  lambda c: c[0],  "right":  lambda c: -c[0],
                   "top":   lambda c: c[1],  "bottom": lambda c: -c[1]}[s]
            cand = sorted((key(c), i) for i, c in enumerate(cents) if c is not None)
            if cand:
                i = cand[0][1]
                return (masks[i:i + 1], f"side_{s}_picked_{i}_of_{n}")

        return (masks[:1], f"ambiguous_{n}_took_0")
