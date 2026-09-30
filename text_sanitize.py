import re


class TextSanitize:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "text": ("STRING", {"forceInput": True}),
            "max_len": ("INT", {"default": 300, "min": 16, "max": 2000}),
        }}

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("text", "report")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    PREAMBLE = [
        r"^\s*(sure|certainly|here\s+is|here's|translation|translated)\b[^\n:]*:\s*",
        r"^\s*(перевод|вот\s+перевод)\b[^\n:]*:\s*",
    ]

    def run(self, text, max_len):
        t = text or ""
        notes = []

        if "<think>" in t or "</think>" in t:
            t = re.sub(r"<think>.*?</think>", " ", t, flags=re.S)
            t = re.sub(r"^.*?</think>", " ", t, flags=re.S)
            t = t.replace("<think>", " ")
            notes.append("think_stripped")

        for p in self.PREAMBLE:
            new = re.sub(p, "", t, flags=re.I)
            if new != t:
                notes.append("preamble_stripped")
                t = new

        t = re.sub(r"^\s*[\"'«](.*)[\"'»]\s*$", r"\1", t.strip(), flags=re.S)
        t = re.sub(r"\s+", " ", t).strip()

        if len(t) > max_len:
            t = t[:max_len].rsplit(" ", 1)[0]
            notes.append(f"truncated_{max_len}")

        return (t, ",".join(notes) or "clean")
