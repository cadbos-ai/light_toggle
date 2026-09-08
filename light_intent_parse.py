import json, re


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
        (r"\bвниз|\bна\s+пол|\bна\s+стол",             0),
        (r"\bвправо|\bнаправо",                        90),
        (r"\bвверх|\bна\s+потол",                      180),
        (r"\bвлево|\bналево",                          270),
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

    RETURN_TYPES = ("STRING", "STRING", "STRING", "BOOLEAN",
                    "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("object_en", "action", "scope", "parsed", "status",
                    "summary", "spec_json", "anchor_en", "side")
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

        object_matched = object_en

        anchor_en = self._pick(self.ANCHOR, t, "")
        if anchor_en and anchor_en == object_matched:
            anchor_en = ""    # «зажги свет у окна» — окно и объект, и якорь
        side = self._pick(self.SIDE, t, "")

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
        spec = [{
            "state":     "on" if action == "on" else "off",
            "kelvin":    self._pick(self.KELVIN,    t, 2700),
            "intensity": self._pick(self.INTENSITY, t, 0.85),
            "cone":      self._pick(self.CONE,      t, 360),
            "dir_deg":   self._pick(self.DIR,       t, 0),
            "reach":     0.55,
        }]
        spec_json = json.dumps(spec, ensure_ascii=False)

        return (object_en, action or "unknown", scope, parsed, status, summary, spec_json, anchor_en, side)
