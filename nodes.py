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

class LightGate:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "parsed":        ("BOOLEAN", {"forceInput": True}),
                "intent_status": ("STRING",  {"forceInput": True}),
                "scope":         ("STRING",  {"forceInput": True}),
            },
            "optional": {
                "found":       ("BOOLEAN", {"forceInput": True, "lazy": True}),
                "mask_status": ("STRING",  {"forceInput": True, "lazy": True}),
                "prefix_root": ("STRING",  {"default": "lt"}),
            },
        }

    RETURN_TYPES = ("BOOLEAN", "STRING", "STRING")
    RETURN_NAMES = ("proceed", "status", "filename_prefix")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def _short_circuit(self, parsed, scope):
        # детекция не нужна: либо уже отказ по разбору, либо операция без адресации
        return (not parsed) or scope == "all"

    def check_lazy_status(self, parsed, intent_status, scope,
                          found=None, mask_status=None, prefix_root="lt"):
        if self._short_circuit(parsed, scope):
            return []
        need = []
        if found is None:
            need.append("found")
        if mask_status is None:
            need.append("mask_status")
        return need

    def run(self, parsed, intent_status, scope,
            found=None, mask_status=None, prefix_root="lt"):
        if not parsed:
            proceed, status = False, f"reject_intent_{intent_status}"
        elif scope == "all":
            proceed, status = True, "ok_all"
        elif found is None:
            proceed, status = False, "reject_no_detector"
        elif not found:
            proceed, status = False, f"reject_{mask_status or 'absent'}"
        else:
            proceed, status = True, "ok"

        safe = "".join(c if c.isalnum() or c in "_-+" else "_" for c in status)
        return (proceed, status, f"{prefix_root}/{safe}")

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
