CAD_COMPONENTS_KEYWORDS = {
    "motor_casing": ["motor", "motor casing", "casing"],
    "nozzle": ["nozzle"],
    "fin_canister": ["fin canister", "fin tube", "fin holder"],
    "bulkhead": ["bulkhead", "disc", "plate"],
    "engine_mount": ["engine mount", "mount"],
    "body_tube": ["body tube", "tube", "rocket tube"],
    "nose_cone": ["nose cone", "cone", "nose"]
}

def detect_cad_component(text: str):
    t = text.lower()
    for comp, keywords in CAD_COMPONENTS_KEYWORDS.items():
        for kw in keywords:
            if kw in t:
                return comp
    return None

def wants_creation(text: str) -> bool:
    t = text.lower()
    return any(word in t for word in [
         "make", "generate", "build", "design"
    ])
