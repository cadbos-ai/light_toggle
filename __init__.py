from .nodes import LightGate, LightImageBranch, LightIntentParse, LightLayerBuild, LightSpecMerge, MaskArea


NODE_CLASS_MAPPINGS = {
  "LightIntentParse": LightIntentParse,
  "MaskArea": MaskArea,
  "LightGate": LightGate,
  "LightImageBranch": LightImageBranch,
  "LightLayerBuild": LightLayerBuild,
  "LightSpecMerge": LightSpecMerge,
}

NODE_DISPLAY_NAME_MAPPINGS = {
  "LightIntentParse": "Light Intent Parse",
  "MaskArea": "Mask Area",
  "LightGate": "Light Gate",
  "LightImageBranch": "Light Image Branch",
  "LightLayerBuild": "Light Layer Build",
  "LightSpecMerge": "Light Spec Merge",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
