class LightTemplatePick:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "action":    ("STRING", {"forceInput": True}),
                "mode":      ("STRING", {"forceInput": True}),
                "tpl_lit":   ("STRING", {"forceInput": True}),
                "tpl_off":   ("STRING", {"forceInput": True}),
                "tpl_plain": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "tpl_daylight": ("STRING", {"forceInput": True}),
                "tpl_ambient":  ("STRING", {"forceInput": True}),
                "tpl_off_many": ("STRING", {"forceInput": True}),
                "count":        ("INT",    {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("template", "mode")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def run(self, action, mode, tpl_lit, tpl_off, tpl_plain,
            tpl_daylight=None, tpl_ambient=None,
            tpl_off_many=None, count=1):
        if action == "daylight" and tpl_daylight is not None:
            return (tpl_daylight, "scene_daylight")
        if action == "ambient" and tpl_ambient is not None:
            return (tpl_ambient, "scene_ambient")
        if mode == "off" and tpl_off_many is not None and (count or 1) > 1:
            return (tpl_off_many, f"off_many_{count}")
        tpl = {"lit": tpl_lit, "off": tpl_off}.get(mode, tpl_plain)
        return (tpl, f"{mode}_{action}")
