from .common import _centroid


class MaskToPhrase:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "masks":     ("MASK",),
            "object_en": ("STRING", {"forceInput": True}),
            "max_items": ("INT", {"default": 6, "min": 1, "max": 12}),
        }}

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("phrase", "debug")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def _describe(self, cx, cy, af, W, H, name):
        x, y = cx / max(W, 1), cy / max(H, 1)
        vert = ("hanging from the ceiling" if y < 0.30 else
                "on the wall" if y < 0.62 else
                "standing near the floor")
        horiz = ("on the left side of the room" if x < 0.34 else
                 "in the centre of the room" if x < 0.66 else
                 "on the right side of the room")
        size = "large " if af > 0.02 else "small " if af < 0.004 else ""
        return f"the {size}{name} {vert} {horiz}"

    def run(self, masks, object_en, max_items):
        n = int(masks.shape[0])
        if n == 0:
            return (object_en, "empty")

        H, W = int(masks.shape[1]), int(masks.shape[2])
        name = object_en.split(" . ")[0].strip() if " . " in object_en else object_en.strip()
        if not name:
            name = "lighting fixture"

        items, dbg = [], []
        for i in range(min(n, max_items)):
            c = _centroid(masks[i])
            if c is None:
                dbg.append(f"{i}:empty")
                continue
            af = float(masks[i].sum()) / max(W * H, 1)
            items.append(self._describe(c[0], c[1], af, W, H, name))
            dbg.append(f"{i}:x={c[0]/max(W,1):.2f},y={c[1]/max(H,1):.2f},a={af:.4f}")

        if not items:
            return (object_en, "no_centroids " + " ".join(dbg))
        if len(items) == 1:
            return (items[0], " ".join(dbg))
        return (f"all {len(items)} lighting fixtures — " + ", ".join(items),
                " ".join(dbg))
