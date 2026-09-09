import json, re


class LightIntentParse:
    ALL_FIXTURES = ("chandelier . pendant lamp . wall sconce . "
                    "floor lamp . table lamp . ceiling light")
    PRIOR_ANY = {"y": [0.0, 1.0], "area": [0.0008, 0.12]}

    ACTION_OFF = [r"\bвыключ", r"\bвыкл\b", r"\bпогас", r"\bпогаш",
                  r"\bпотуш", r"\bтуш", r"\bвыруб", r"\bгаси\b", r"\bубер"]
    ACTION_ON  = [r"\bзажг", r"\bзажеч", r"\bвключ", r"\bвруб",
                  r"\bзапуст", r"\bдобав\w*\s+свет"]
    SCOPE_ALL  = [r"\bвс[еяю]\b", r"\bвесь\b", r"\bвсех\b", r"\bполностью\b"]

    OBJECTS = [
        (r"\bлюстр",              "chandelier",       {"y": [0.00, 0.45], "area": [0.004, 0.10]}),
        (r"\bподвес",             "pendant lamp",     {"y": [0.00, 0.55], "area": [0.002, 0.06]}),
        (r"\bбра\b",              "wall sconce",      {"y": [0.10, 0.70], "area": [0.001, 0.04]}),
        (r"\bторшер",             "floor lamp",       {"y": [0.25, 1.00], "area": [0.002, 0.08]}),
        (r"\bнастольн\w*\s+ламп", "table lamp",       {"y": [0.30, 0.95], "area": [0.001, 0.05]}),
        (r"\bспот",               "spotlight",        {"y": [0.00, 0.35], "area": [0.0005, 0.02]}),
        (r"\bгирлянд",            "string lights",    {"y": [0.00, 1.00], "area": [0.001, 0.15]}),
        (r"\bподсветк",           "led strip",        {"y": [0.00, 1.00], "area": [0.001, 0.10]}),
        (r"\bлампоч",             "light bulb",       {"y": [0.00, 0.90], "area": [0.0003, 0.02]}),
        (r"\bламп",               "lamp",             {"y": [0.00, 1.00], "area": [0.001, 0.10]}),
        (r"\bсвет(?!ильник)|\bосвещен", "ceiling light", {"y": [0.00, 0.60], "area": [0.001, 0.12]}),
        (r"\bсветильник",         "lighting fixture", {"y": [0.00, 1.00], "area": [0.001, 0.12]}),
        (r"\bокн|\bокош",         "window",           {"y": [0.00, 0.90], "area": [0.005, 0.30]}),
    ]
    KELVIN = [
        (r"\bзакат|\bзолот\w*\s+час|\bсвеч",           2200),
        (r"\bочень\s+тепл|\bянтарн",                   2400),
        (r"\bтепл|\bуютн",                             2700),
        (r"\bнейтральн|\bестествен",                   4000),
        (r"\bхолодн|\bбел\w*\s+свет",                  5500),
        (r"\bдневн",                                   6500),
    ]
    INTENSITY = [
        (r"\bеле|\bчуть|\bслаб|\bприглуш|\bтускл",     0.35),
        (r"\bмягк|\bнеярк",                            0.6),
        (r"\bярк|\bсильн|\bпоярч",                     1.25),
        (r"\bочень\s+ярк|\bмаксимальн",                1.6),
    ]
    CONE = [
        (r"\bузк|\bточечн|\bнаправлен",                60),
        (r"\bширок",                                   120),
        (r"\bво\s+все\s+сторон|\bравномерн|\bрассеян", 360),
    ]
    DIR = [
        (r"\bвниз\b|\bкниз",                    0),
        (r"\bвправо\b|\bнаправо\b",             90),
        (r"\bвверх\b|\bкверх|\bв\s+потолок\b",  180),
        (r"\bвлево\b|\bналево\b",               270),
    ]
    ANCHOR = [
        (r"\bкроват",                          "bed"),
        (r"\bдиван",                           "sofa"),
        (r"\bкресл",                           "armchair"),
        (r"\bобеден\w*\s+стол|\bстол(?!ешн)",  "dining table"),
        (r"\bзеркал",                          "mirror"),
        (r"\bкамин",                           "fireplace"),
        (r"\bтумб|\bкомод",                    "chest of drawers"),
        (r"\bлестниц",                         "staircase"),
        (r"\bокн|\bокош",                      "window"),
    ]
    SIDE = [
        (r"\bслев|\bлев\w*\s+(бра|светильник|ламп|торшер)",  "left"),
        (r"\bсправ|\bправ\w*\s+(бра|светильник|ламп|торшер)", "right"),
        (r"\bсверху|\bверхн",                                 "top"),
        (r"\bснизу|\bнижн",                                   "bottom"),
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

    @staticmethod
    def _pick(table, text, default):
        for pat, val in table:
            if re.search(pat, text):
                return val
        return default

    RETURN_TYPES = ("STRING", "STRING", "STRING", "BOOLEAN", "STRING",
                    "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("object_en", "action", "scope", "parsed", "status",
                    "summary", "spec_json", "anchor_en", "side", "prior_json")
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

        # --- объект + приор -------------------------------------------------
        object_matched = ""
        prior = {}
        for pat, en, pr in self.OBJECTS:
            if re.search(pat, t):
                object_matched, prior = en, dict(pr)
                break

        # --- проблемы разбора -----------------------------------------------
        problems = []
        if not action:
            problems.append("no_action")
        if not object_matched and scope != "all":
            problems.append("no_object")

        # --- режим «все светильники» ----------------------------------------
        if scope == "all":
            object_en = self.ALL_FIXTURES
            prior = dict(self.PRIOR_ANY)
            problems = [p for p in problems if p != "no_object"]
        else:
            object_en = object_matched or fallback_object
            if not object_matched:
                prior = dict(self.PRIOR_ANY)

        # --- якорь и сторона -------------------------------------------------
        anchor_en = self._pick(self.ANCHOR, t, "")
        if anchor_en and anchor_en == object_matched:
            anchor_en = ""
        side = self._pick(self.SIDE, t, "")

        # --- спецификация ----------------------------------------------------
        spec = [{
            "state":     "on" if action == "on" else "off",
            "kelvin":    self._pick(self.KELVIN,    t, 2700),
            "intensity": self._pick(self.INTENSITY, t, 0.85),
            "cone":      self._pick(self.CONE,      t, 360),
            "dir_deg":   self._pick(self.DIR,       t, 0),
            "reach":     0.35,
        }]
        spec_json = json.dumps(spec, ensure_ascii=False)
        prior_json = json.dumps(prior, ensure_ascii=False)

        # --- итог -------------------------------------------------------------
        parsed = len(problems) == 0
        status = "ok" if parsed else "+".join(problems)
        summary = (f"object={object_en} | action={action or '-'} | scope={scope} | "
                   f"anchor={anchor_en or '-'} | side={side or '-'} | "
                   f"prior={prior_json} | {status}")

        return (object_en, action or "unknown", scope, parsed,
                status, summary, spec_json, anchor_en, side, prior_json)
