import json


class LightSpecMerge:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "base":     ("STRING", {"forceInput": True}),
            "override": ("STRING", {"forceInput": True}),
        }}

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("spec", "source")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def run(self, base, override):
        ov = override.strip()
        if not ov:
            return (base, "instruction")
        try:
            parsed = json.loads(ov)
        except json.JSONDecodeError:
            return (base, "override_invalid_fallback_instruction")
        if isinstance(parsed, dict):
            parsed = [parsed]

        try:
            b = json.loads(base)
        except json.JSONDecodeError:
            b = []
        if isinstance(b, dict):
            b = [b]

        merged = []
        for i, item in enumerate(parsed):
            base_i = dict(b[i]) if i < len(b) and isinstance(b[i], dict) else {}
            base_i.update(item if isinstance(item, dict) else {})
            merged.append(base_i)
        return (json.dumps(merged, ensure_ascii=False), "client")
