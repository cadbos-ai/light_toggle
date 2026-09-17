import re, sys, json
sys.path.insert(0, ".")
from light_intent_parse import LightIntentParse as P

CASES = [
    # фраза                              action      object_en          прочее
    ("зажги люстру",                      "on",       "chandelier",      {}),
    ("выключи люстру",                    "off",      "chandelier",      {}),
    ("погаси бра над кроватью",           "off",      "wall sconce",     {"anchor": "bed"}),
    ("гасить свет в комнате",             "off",      "ceiling light",   {}),
    ("выключи все светильники",           "off",      None,              {"scope": "all"}),
    ("включи верхний свет",               "on",       "ceiling light",   {"side": ""}),
    ("свети очень ярко",                  None,       None,              {"intensity": 1.6}),
    ("зажги люстру во все стороны",       "on",       "chandelier",      {"scope": "single", "cone": 360}),
    ("сделай светлее",                    "ambient",  "",                {}),
    ("фоновый свет поярче",               "ambient",  "",                {"has_phrase": True}),
    ("общее освещение потеплее",          "ambient",  "",                {"has_phrase": True}),
    ("помягче свет в комнате",            "ambient",  "",                {"has_phrase": True}),
    ("за окном закат",                    "daylight", "",                {"has_phrase": True}),
    ("сделай ночь за окном",              "daylight", "",                {"has_phrase": True}),
    ("пасмурно на улице",                 "daylight", "",                {"has_phrase": True}),
    ("убери свечение люстры",             "off",      "chandelier",      {"kelvin_not": 2200}),
    ("сделай поярче",                     None,       None,              {}),
]

node = P()
fails = 0
for phrase, exp_action, exp_obj, extra in CASES:
    out = node.run(phrase)
    names = dict(zip(P.RETURN_NAMES, out))
    bad = []
    if exp_action and names["action"] != exp_action:
        bad.append(f"action={names['action']} ожид {exp_action}")
    if exp_obj is not None and names["object_en"] != exp_obj:
        bad.append(f"object={names['object_en']!r} ожид {exp_obj!r}")
    if extra.get("scope") and names["scope"] != extra["scope"]:
        bad.append(f"scope={names['scope']} ожид {extra['scope']}")
    if extra.get("has_phrase") and not names.get("scene_phrase"):
        bad.append("scene_phrase пуст")
    if "intensity" in extra:
        got = json.loads(names["spec_json"] or "[]")
        got = got[0]["intensity"] if got else None
        if got != extra["intensity"]:
            bad.append(f"intensity={got} ожид {extra['intensity']}")
    if "kelvin_not" in extra:
        got = json.loads(names["spec_json"] or "[]")
        got = got[0]["kelvin"] if got else None
        if got == extra["kelvin_not"]:
            bad.append(f"kelvin={got} — ложное срабатывание")
    if bad:
        fails += 1
        print(f"FAIL  {phrase!r}\n      " + "; ".join(bad))

print(f"\n{len(CASES) - fails}/{len(CASES)} прошло")
sys.exit(1 if fails else 0)
