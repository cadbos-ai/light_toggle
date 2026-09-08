class LightImageBranch:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "proceed":  ("BOOLEAN", {"forceInput": True}),
                "on_true":  ("IMAGE", {"lazy": True}),
                "on_false": ("IMAGE", {"lazy": True}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def check_lazy_status(self, proceed, on_true=None, on_false=None):
        if proceed:
            return [] if on_true is not None else ["on_true"]
        return [] if on_false is not None else ["on_false"]

    def run(self, proceed, on_true=None, on_false=None):
        return (on_true if proceed else on_false,)
