import torch


class MaskBatchMerge:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"iou_dedup": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 1.0, "step": 0.05})},
            "optional": {f"masks_{i}": ("MASK",) for i in range(1, 5)},
        }

    RETURN_TYPES = ("MASK", "STRING")
    RETURN_NAMES = ("masks", "report")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def run(self, iou_dedup, **kw):
        parts, shape, ref = [], None, None
        for k in sorted(kw):
            m = kw[k]
            if m is None or int(m.shape[0]) == 0:
                continue
            if shape is None:
                shape = (int(m.shape[1]), int(m.shape[2]))
                ref = m
            for i in range(int(m.shape[0])):
                if float(m[i].sum()) > 0:
                    parts.append(m[i])

        if not parts:
            if shape is None:
                return (torch.zeros((1, 1, 1)), "empty_no_input")
            H, W = shape
            return (torch.zeros((1, H, W), device=ref.device, dtype=ref.dtype),
                    "empty_all_zero")

        keep = []
        for c in parts:
            cb = c > 0.5
            dup = False
            for k in keep:
                kb = k > 0.5
                union = float((cb | kb).sum())
                if union > 0 and float((cb & kb).sum()) / union >= iou_dedup:
                    dup = True
                    break
            if not dup:
                keep.append(c)

        return (torch.stack(keep, 0), f"merged {len(keep)} of {len(parts)}")
