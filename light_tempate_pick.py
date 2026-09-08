class LightTemplatePick:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "action":    ("STRING", {"forceInput": True}),
            "applied":   ("INT",    {"forceInput": True}),
            "tpl_lit":   ("STRING", {"forceInput": True}),
            "tpl_plain": ("STRING", {"forceInput": True}),
        }}

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("template", "mode")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def run(self, action, applied, tpl_lit, tpl_plain):
        if applied > 0:
            return (tpl_lit, f"lit_{action}")
        return (tpl_plain, f"plain_{action}")
