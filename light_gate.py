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
                "found":            ("BOOLEAN", {"forceInput": True, "lazy": True}),
                "mask_status":      ("STRING",  {"forceInput": True, "lazy": True}),
                "prefix_root":      ("STRING",  {"default": "lt"}),
                "run_tag":          ("STRING",  {"forceInput": True}),
                "action":           ("STRING",  {"forceInput": True}),
                "fixture_state":    ("STRING",  {"forceInput": True, "lazy": True}),
                "verified":         ("BOOLEAN", {"forceInput": True, "lazy": True}),
            },
        }

    RETURN_TYPES = ("BOOLEAN", "STRING", "STRING")
    RETURN_NAMES = ("proceed", "status", "filename_prefix")
    FUNCTION = "run"
    CATEGORY = "light-toggle"

    SCENE_ACTIONS = ("daylight", "ambient")

    def _short_circuit(self, parsed, action=""):
        return (not parsed) or (action in self.SCENE_ACTIONS)

    def check_lazy_status(self, parsed, intent_status, scope,
                          found=None, mask_status=None,
                          prefix_root="lt", run_tag="",
                          action="", fixture_state=None, verified=None, **kw):
        if self._short_circuit(parsed, action):
            return []
        need = []
        if found is None:
            need.append("found")
        if mask_status is None:
            need.append("mask_status")
        if fixture_state is None:
            need.append("fixture_state")
        if need:
            return need
        if found and scope != "all" and verified is None:
            return ["verified"]
        return []

    def run(self, parsed, intent_status, scope,
            found=None, mask_status=None, prefix_root="lt", run_tag="",
            action="", fixture_state=None, verified=None, **kw):
        if not parsed:
            proceed, status = False, f"reject_intent_{intent_status}"
        elif action in self.SCENE_ACTIONS:
            proceed, status = True, f"ok_{action}"
        elif found is None:
            proceed, status = False, "reject_no_detector"
        elif not found:
            proceed, status = False, f"reject_{mask_status or 'absent'}"
        elif scope != "all" and verified is False:
            proceed, status = False, "reject_verify"
        elif action == "on" and fixture_state == "lit":
            proceed, status = False, "reject_already_on"
        elif action == "off" and fixture_state == "unlit":
            proceed, status = False, "reject_already_off"
        elif scope == "all":
            proceed, status = True, "ok_all"
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
