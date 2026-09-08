from .nodes import LightGate, LightImageBranch, LightIntentParse, LightLayerBuild, LightMaskSelect, LightSpecMerge, LightTemplatePick, MaskArea, MaskPickByLocation


NODE_CLASS_MAPPINGS = {
  "LightIntentParse": LightIntentParse,
  "MaskArea": MaskArea,
  "LightGate": LightGate,
  "LightImageBranch": LightImageBranch,
  "LightLayerBuild": LightLayerBuild,
  "LightSpecMerge": LightSpecMerge,
  "LightMaskSelect": LightMaskSelect,
  "MaskPickByLocation": MaskPickByLocation,
  "LightTemplatePick": LightTemplatePick,
}

NODE_DISPLAY_NAME_MAPPINGS = {
  "LightIntentParse": "Light Intent Parse",
  "MaskArea": "Mask Area",
  "LightGate": "Light Gate",
  "LightImageBranch": "Light Image Branch",
  "LightLayerBuild": "Light Layer Build",
  "LightSpecMerge": "Light Spec Merge",
  "LightMaskSelect": "Light Mask Select",
  "MaskPickByLocation": "Mask Pick By Location",
  "LightTemplatePick": "Light Template Pick",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
