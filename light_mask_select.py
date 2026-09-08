class LightMaskSelect:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"prefer_client": ("BOOLEAN", {"forceInput": True})},
            "optional": {
                "client_mask":   ("MASK",   {"lazy": True}),
                "detected_mask": ("MASK",   {"lazy": True}),
                "detected_note": ("STRING", {"lazy": True}),
            },
        }

    RETURN_TYPES = ("MASK", "STRING")
    RETURN_NAMES = ("mask", "source_note")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def check_lazy_status(self, prefer_client, client_mask=None,
                          detected_mask=None, detected_note=None):
        if prefer_client:
            return [] if client_mask is not None else ["client_mask"]
        need = []
        if detected_mask is None:
            need.append("detected_mask")
        if detected_note is None:
            need.append("detected_note")
        return need

    def run(self, prefer_client, client_mask=None,
            detected_mask=None, detected_note=None):
        if prefer_client and client_mask is not None:
            return (client_mask, "client")
        return (detected_mask, f"detector:{detected_note or '-'}")
