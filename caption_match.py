class CaptionMatch:
    POSITIVE = {
        "chandelier":    ["chandelier"],
        "pendant lamp":  ["pendant", "hanging lamp", "hanging light", "chandelier"],
        "wall sconce":   ["sconce", "wall lamp", "wall light"],
        "table lamp":    ["table lamp", "desk lamp", "bedside lamp", "lamp"],
        "floor lamp":    ["floor lamp", "standing lamp", "lamp"],
        "ceiling light": ["ceiling light", "ceiling lamp", "downlight", "spotlight", "recessed"],
    }
    NEGATIVE = {
        "chandelier":    ["lamp", "sconce", "spotlight", "lampshade"],
        "pendant lamp":  ["table lamp", "floor lamp", "desk lamp", "sconce"],
        "wall sconce":   ["chandelier", "table lamp", "floor lamp", "desk lamp"],
        "table lamp":    ["chandelier", "sconce", "ceiling"],
        "floor lamp":    ["chandelier", "sconce", "ceiling"],
        "ceiling light": ["table lamp", "floor lamp", "desk lamp", "sconce"],
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "text":      ("STRING", {"forceInput": True}),
            "object_en": ("STRING", {"forceInput": True}),
        }}

    RETURN_TYPES = ("BOOLEAN", "STRING")
    RETURN_NAMES = ("match", "status")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def run(self, text, object_en):
        t = text.strip().lower()
        obj = object_en.strip().lower()
        pos = self.POSITIVE.get(obj)
        if pos is None:
            return (True, f"verify_skip:{obj}")
        if any(w in t for w in pos):
            return (True, f"verify_match:{t[:60]}")
        if any(w in t for w in self.NEGATIVE.get(obj, [])):
            return (False, f"verify_conflict:{t[:60]}")
        return (True, f"verify_unclear:{t[:60]}")
