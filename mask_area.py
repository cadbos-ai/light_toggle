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
