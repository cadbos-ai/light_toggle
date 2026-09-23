import torch


class MaskBBoxCrop:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "image":   ("IMAGE",),
            "masks":   ("MASK",),
            "padding": ("FLOAT", {"default": 0.35, "min": 0.0, "max": 2.0, "step": 0.05}),
            "isolate": ("BOOLEAN", {"default": False}),
        }}

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("crop", "report")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def run(self, image, masks, padding, isolate):
        img = image[0]
        H, W, _ = img.shape
        if int(masks.shape[0]) == 0:
            return (image, "empty")
        m = masks[0] > 0.5
        rows = torch.nonzero(m.sum(dim=1) > 0)
        cols = torch.nonzero(m.sum(dim=0) > 0)
        if len(rows) == 0 or len(cols) == 0:
            return (image, "empty")
        y0, y1 = int(rows.min()), int(rows.max()) + 1
        x0, x1 = int(cols.min()), int(cols.max()) + 1
        py, px = int((y1 - y0) * padding), int((x1 - x0) * padding)
        y0, y1 = max(0, y0 - py), min(H, y1 + py)
        x0, x1 = max(0, x0 - px), min(W, x1 + px)
        crop = img[y0:y1, x0:x1, :]
        if isolate:
            mk = masks[0][y0:y1, x0:x1].to(crop.device).to(crop.dtype)
            k = max(3, int(max(crop.shape[0], crop.shape[1]) * 0.03)) | 1
            mk = torch.nn.functional.max_pool2d(mk[None, None], k, stride=1, padding=k // 2)[0, 0]
            crop = crop * mk.unsqueeze(-1) + 0.5 * (1 - mk.unsqueeze(-1))

        frac = ((x1 - x0) * (y1 - y0)) / max(W * H, 1)
        return (crop.unsqueeze(0), f"box=({x0},{y0},{x1},{y1}) frac={frac:.2f}")
