from .light_gate import LightGate
from .light_image_branch import LightImageBranch
from .light_intent_parse import LightIntentParse
from .light_layer_build import LightLayerBuild
from .light_mask_select import LightMaskSelect
from .light_spec_merge import LightSpecMerge
from .light_tempate_pick import LightTemplatePick
from .mask_area import MaskArea
from .mask_pick_by_location import MaskPickByLocation


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
