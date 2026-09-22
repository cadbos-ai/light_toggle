import torch


class MaskBBoxCrop:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "image":   ("IMAGE",),
            "masks":   ("MASK",),
            "padding": ("FLOAT", {"default": 0.35, "min": 0.0, "max": 2.0, "step": 0.05}),
        }}

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("crop", "report")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def run(self, image, masks, padding):
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
        return (img[y0:y1, x0:x1, :].unsqueeze(0), f"box=({x0},{y0},{x1},{y1})")
    