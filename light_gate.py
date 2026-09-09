def _slug(s, maxlen=72):
    s = "".join(c if c.isalnum() or c in "_-+." else "_" for c in str(s))
    s = s.strip("._")
    return s[:maxlen] or "x"


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
                "run_tag":     ("STRING",  {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("BOOLEAN", "STRING", "STRING")
    RETURN_NAMES = ("proceed", "status", "filename_prefix")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    def _short_circuit(self, parsed, scope):
        return not parsed

    def check_lazy_status(self, parsed, intent_status, scope,
                          found=None, mask_status=None,
                          prefix_root="lt", run_tag=""):
        if self._short_circuit(parsed, scope):
            return []
        need = []
        if found is None:
            need.append("found")
        if mask_status is None:
            need.append("mask_status")
        return need

    def run(self, parsed, intent_status, scope,
            found=None, mask_status=None, prefix_root="lt", run_tag=""):
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

        bucket = "reject" if status.startswith("reject") else "ok"
        prefix = "/".join([
            _slug(prefix_root),
            bucket,
            _slug(status),
            _slug(run_tag or "run"),
        ])
        return (proceed, status, prefix)
