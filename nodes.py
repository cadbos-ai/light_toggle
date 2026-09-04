import re


class LightIntentParse:
    ACTION_OFF = [r"\bвыключ", r"\bвыкл\b", r"\bпогас", r"\bпогаш",
                  r"\bпотуш", r"\bтуш", r"\bвыруб", r"\bгаси\b", r"\bубер"]
    ACTION_ON  = [r"\bзажг", r"\bзажеч", r"\bвключ", r"\bвруб",
                  r"\bзапуст", r"\bдобав\w*\s+свет"]
    SCOPE_ALL  = [r"\bвс[еяю]\b", r"\bвесь\b", r"\bвсех\b", r"\bполностью\b"]

    OBJECTS = [
        (r"\bлюстр",                 "chandelier"),
        (r"\bподвес",                "pendant lamp"),
        (r"\bбра\b",                 "wall sconce"),
        (r"\bторшер",                "floor lamp"),
        (r"\bнастольн\w*\s+ламп",    "table lamp"),
        (r"\bспот",                  "spotlight"),
        (r"\bгирлянд",               "string lights"),
        (r"\bподсветк",              "led strip"),
        (r"\bлампоч",                "light bulb"),
        (r"\bламп",                  "lamp"),
        (r"\bсветильник",            "lighting fixture"),
        (r"\bокн|\bокош",            "window"),
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "instruction": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "fallback_object": ("STRING", {"default": "lighting fixture"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "BOOLEAN", "STRING", "STRING")
    RETURN_NAMES = ("object_en", "action", "scope", "parsed", "status", "summary")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def run(self, instruction, fallback_object="lighting fixture"):
        t = instruction.lower().replace("ё", "е").strip()

        # порядок важен: OFF проверяется первым, но \b и так разводит
        # "выключи" и "включи" — внутри "выключи" границы слова перед "включ" нет
        if any(re.search(p, t) for p in self.ACTION_OFF):
            action = "off"
        elif any(re.search(p, t) for p in self.ACTION_ON):
            action = "on"
        else:
            action = ""

        scope = "all" if any(re.search(p, t) for p in self.SCOPE_ALL) else "single"

        object_en = ""
        for pat, en in self.OBJECTS:
            if re.search(pat, t):
                object_en = en
                break

        problems = []
        if not action:
            problems.append("no_action")
        if not object_en and scope != "all":
            problems.append("no_object")

        if not object_en:
            object_en = fallback_object

        parsed = len(problems) == 0
        status = "ok" if parsed else "+".join(problems)
        summary = f"object={object_en} | action={action or '-'} | scope={scope} | {status}"

        return (object_en, action or "unknown", scope, parsed, status, summary)

class MaskArea:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "mask": ("MASK",),
            "min_fraction": ("FLOAT", {"default": 0.0008, "min": 0.0, "max": 1.0, "step": 0.0001}),
            "max_fraction": ("FLOAT", {"default": 0.15,   "min": 0.0, "max": 1.0, "step": 0.001}),
        }}
    RETURN_TYPES = ("FLOAT", "INT", "BOOLEAN", "STRING")
    RETURN_NAMES = ("fraction", "pixels", "found", "status")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def run(self, mask, min_fraction, max_fraction):
        m = (mask[0] > 0.5).float()
        px = int(m.sum().item())
        frac = px / max(m.numel(), 1)
        if frac < min_fraction:
            return (frac, px, False, "absent")
        if frac > max_fraction:
            return (frac, px, False, "too_large")
        return (frac, px, True, "found")
