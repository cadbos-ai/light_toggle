import torch


def _centroid(mask):
    """mask: [H,W] float. Возвращает (cx, cy) или None."""
    s = mask.sum()
    if s < 1e-6:
        return None
    H, W = mask.shape
    ys = torch.arange(H, device=mask.device, dtype=mask.dtype).view(H, 1)
    xs = torch.arange(W, device=mask.device, dtype=mask.dtype).view(1, W)
    cx = float((mask * xs).sum() / s)
    cy = float((mask * ys).sum() / s)
    return cx, cy
