import torch

LUM = (0.2126, 0.7152, 0.0722)


class MaskArea:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask":         ("MASK",),
                "min_fraction": ("FLOAT", {"default": 0.0008, "min": 0.0, "max": 1.0, "step": 0.0001}),
                "max_fraction": ("FLOAT", {"default": 0.15,   "min": 0.0, "max": 1.0, "step": 0.001}),
            },
            "optional": {
                "image":     ("IMAGE",),
                "lit_ratio": ("FLOAT", {"default": 1.8, "min": 1.0, "max": 6.0, "step": 0.05}),
            },
        }

    RETURN_TYPES = ("FLOAT", "INT", "BOOLEAN", "STRING", "FLOAT", "STRING")
    RETURN_NAMES = ("fraction", "pixels", "found", "status", "rel_lum", "state")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def run(self, mask, min_fraction, max_fraction, image=None, lit_ratio=1.8):
        m = (mask[0] > 0.5)
        px = int(m.sum())
        frac = px / max(m.numel(), 1)

        if frac < min_fraction:
            status = "absent"
        elif frac > max_fraction:
            status = "too_large"
        else:
            status = "found"
        found = status == "found"

        rel, state = 0.0, "unknown"
        if image is not None and px > 0:
            w = torch.tensor(LUM, device=image.device, dtype=image.dtype)
            lum = (image[0] * w).sum(-1)
            inside = float(torch.quantile(lum[m.to(lum.device)], 0.95))
            scene = float(torch.quantile(lum.flatten(), 0.95))
            rel = inside / max(scene, 1e-4)
            state = "lit" if rel >= lit_ratio else "unlit"

        return (frac, px, found, status, rel, state)
