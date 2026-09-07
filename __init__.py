from .nodes import LightGate, LightImageBranch, LightIntentParse, MaskArea


NODE_CLASS_MAPPINGS = {
  "LightIntentParse": LightIntentParse,
  "MaskArea": MaskArea,
  "LightGate": LightGate,
  "LightImageBranch": LightImageBranch,
}

NODE_DISPLAY_NAME_MAPPINGS = {
  "LightIntentParse": "Light Intent Parse",
  "MaskArea": "Mask Area",
  "LightGate": "Light Gate",
  "LightImageBranch": "Light Image Branch",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
