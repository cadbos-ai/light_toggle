import math


from common import _centroid


class MaskPickByLocation:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "masks":     ("MASK",),
                "anchor_en": ("STRING", {"forceInput": True}),
                "side":      ("STRING", {"forceInput": True}),
            },
            "optional": {
                "anchor": ("MASK", {"lazy": True}),
            },
        }

    RETURN_TYPES = ("MASK", "STRING")
    RETURN_NAMES = ("mask", "status")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def check_lazy_status(self, masks, anchor_en, side, anchor=None):
        if int(masks.shape[0]) <= 1:      # выбирать не из чего
            return []
        if not anchor_en.strip():         # якоря нет — обойдёмся стороной
            return []
        return [] if anchor is not None else ["anchor"]

    def run(self, masks, anchor_en, side, anchor=None):
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

        s = side.strip().lower()
        if s in ("left", "right", "top", "bottom"):
            key = {"left":  lambda c: c[0],  "right":  lambda c: -c[0],
                   "top":   lambda c: c[1],  "bottom": lambda c: -c[1]}[s]
            cand = sorted((key(c), i) for i, c in enumerate(cents) if c is not None)
            if cand:
                i = cand[0][1]
                return (masks[i:i + 1], f"side_{s}_picked_{i}_of_{n}")

        return (masks[:1], f"ambiguous_{n}_took_0")
