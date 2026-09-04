from .nodes import LightIntentParse, MaskArea


NODE_CLASS_MAPPINGS = {
  "LightIntentParse": LightIntentParse,
  "MaskArea": MaskArea,
}

NODE_DISPLAY_NAME_MAPPINGS = {
  "LightIntentParse": "Light Intent Parse",
  "MaskArea": "Mask Area",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
