from ollama_client import call_ollama

def clean_code(output: str):
    lines = output.splitlines()
    cleaned = []

    for line in lines:
        if line.strip().startswith("```"):
            continue

        if line.strip().startswith("import") or line.strip().startswith("def"):
            cleaned.append(line)
            continue

        if cleaned:
            cleaned.append(line)

    return "\n".join(cleaned)

def interpret_command(text: str):
    prompt = f"""
You are an expert CadQuery engineer.

Generate ONLY valid Python code.

STRICT OUTPUT RULES:
- Output ONLY Python code.
- No markdown.
- No backticks.
- No explanations.
- No comments outside the code.
- The FIRST non-empty line MUST be:
  import cadquery as cq
- The code MUST define a function:
  def build():
      return <CadQuery object>

AVAILABLE FUNCTIONS:
You may ONLY generate geometry by calling these helpers from cad_library:

1) cad_library.nozzle_helper(throat_radius, expansion_ratio, casing_inner_diameter)
   - Use this ONLY when the user asks for a nozzle.
   - Do NOT generate nozzle geometry manually.

2) cad_library.gear_helper(teeth, module, thickness, bore, pressure_angle=20)
   - Use this ONLY when the user asks for a gear.
   - Do NOT generate your own gear math.

You also have access to helper functions:

cad_library.gear_helper(teeth, module, thickness, bore, pressure_angle=20)
cad_library.nozzle_helper(throat_radius, expansion_ratio, casing_inner_diameter)
cad_library.motor_casing_helper(inner_diameter, outer_diameter, length, screw_count=6, screw_offset=10)
cad_library.fin_canister_helper(diameter, height, wall_thickness=2, fin_slots=4, slot_width=2)
- cad_library.bulkhead_helper(diameter, thickness=3, hole_count=4, hole_diameter=3, hole_offset=5)
- cad_library.engine_mount_helper(outer_diameter, inner_diameter, thickness=5)
- cad_library.body_tube_helper(outer_diameter, length, wall_thickness=2)
- cad_library.nose_cone_helper(base_diameter, height, thickness=2)

Always use these helpers for the corresponding parts. Do NOT generate your own low-level geometry for gears, nozzles, motor casings, or fin canisters.


GENERAL RULES:
- Do NOT import anything except cadquery as cq and cad_library.
- Do NOT use exec, eval, __import__, or file access.
- Do NOT create classes.
- Do NOT create multiple solids.
- build() MUST return exactly ONE CadQuery solid.

IMPORT RULES:
- You may ONLY use:
  import cadquery as cq
  import cad_library
- DO NOT use "from ... import ..."
- Access helpers ONLY as cad_library.<function>


USER REQUEST:
"{text}"

"""

    raw = call_ollama(prompt)
    print("raw")
    print(raw)
    code = clean_code(raw)
    print("Code")
    print(code)
    return code
