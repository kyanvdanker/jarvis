import cadquery as cq
import math
from cq_gears import SpurGear

# --- Nozzle helper ---
def nozzle_helper(
    throat_radius,
    expansion_ratio,
    casing_inner_diameter,
    casing_length=None
):
    if throat_radius <= 0:
        raise ValueError("throat_radius must be > 0")
    if expansion_ratio <= 1:
        raise ValueError("expansion_ratio must be > 1")
    if casing_inner_diameter <= 2 * throat_radius:
        raise ValueError("casing_inner_diameter too small for throat")

    throat_length = 20.0
    angle_deg = 15.0
    angle_rad = math.radians(angle_deg)

    exit_radius = throat_radius * math.sqrt(expansion_ratio)
    diverge_length = (exit_radius - throat_radius) / math.tan(angle_rad)
    total_length = throat_length + diverge_length
    casing_length = casing_length or total_length
    if casing_length < total_length:
        raise ValueError("casing_length shorter than nozzle")

    casing_radius = casing_inner_diameter / 2
    casing = cq.Workplane("XY").circle(casing_radius).extrude(casing_length)

    # Nozzle void
    profile = (
        cq.Workplane("XZ")
        .moveTo(throat_radius, 0)
        .lineTo(throat_radius, throat_length)
        .lineTo(exit_radius, total_length)
        .lineTo(0, total_length)
        .lineTo(0, 0)
        .close()
    )
    nozzle_void = profile.revolve(360)

    return casing.cut(nozzle_void).clean()


# --- Gear helper ---
def gear_helper(teeth, module, thickness, bore, pressure_angle=20):
    if teeth < 4:
        raise ValueError("teeth must be >= 4")
    if module <= 0 or thickness <= 0:
        raise ValueError("module and thickness must be > 0")
    return SpurGear(
        module=module,
        teeth_number=teeth,
        width=thickness,
        bore_d=bore,
        pressure_angle=pressure_angle
    ).build()


# --- Motor casing helper ---
def motor_casing_helper(
    inner_diameter,
    outer_diameter,
    length,
    screw_count=6,
    screw_offset=10
):
    if inner_diameter <= 0 or outer_diameter <= inner_diameter:
        raise ValueError("Outer diameter must be > inner diameter")
    if length <= 2 * screw_offset:
        raise ValueError("Length too short for screw offsets")
    if screw_count < 1:
        raise ValueError("At least one screw required")

    # main tube
    tube = cq.Workplane("XY").circle(outer_diameter/2).extrude(length)
    inner_void = cq.Workplane("XY").circle(inner_diameter/2).extrude(length)
    casing = tube.cut(inner_void)

    # add screw holes on both ends
    angles = [i * 360 / screw_count for i in range(screw_count)]
    for z in [screw_offset, length - screw_offset]:
        for angle in angles:
            casing = casing.faces(">Z" if z == length - screw_offset else "<Z") \
                .workplane(centerOption="CenterOfBoundBox") \
                .polarArray(outer_diameter/2 - 2, screw_count, 360) \
                .circle(1.5).cutThruAll()  # hole diameter 3mm

    return casing.clean()


# --- Fin canister helper ---
def fin_canister_helper(
    diameter,
    height,
    wall_thickness=2,
    fin_slots=4,
    slot_width=2
):
    if diameter <= 0 or height <= 0:
        raise ValueError("Diameter and height must be > 0")
    if wall_thickness <= 0 or fin_slots < 1:
        raise ValueError("Wall thickness >0 and at least 1 fin slot")

    # outer tube
    tube = cq.Workplane("XY").circle(diameter/2).extrude(height)
    inner = cq.Workplane("XY").circle(diameter/2 - wall_thickness).extrude(height)
    canister = tube.cut(inner)

    # fin slots
    for i in range(fin_slots):
        angle = i * 360 / fin_slots
        slot = (
            cq.Workplane("XY")
            .rect(slot_width, diameter)
            .extrude(height + 2)
            .rotate((0,0,0), (0,0,1), angle)
        )
        canister = canister.cut(slot)

    return canister.clean()

def bulkhead_helper(
    diameter,
    thickness=3,
    hole_count=4,
    hole_diameter=3,
    hole_offset=5
):
    if diameter <= 0 or thickness <= 0:
        raise ValueError("Diameter and thickness must be >0")
    
    disc = cq.Workplane("XY").circle(diameter/2).extrude(thickness)
    
    # holes
    for i in range(hole_count):
        angle = i * 360 / hole_count
        disc = disc.faces(">Z").workplane(centerOption="CenterOfBoundBox") \
            .polarArray(diameter/2 - hole_offset, hole_count, 360) \
            .circle(hole_diameter/2).cutThruAll()
    
    return disc.clean()

def engine_mount_helper(
    outer_diameter,
    inner_diameter,
    thickness=5
):
    if outer_diameter <= inner_diameter or thickness <= 0:
        raise ValueError("Invalid diameters or thickness")
    
    ring = cq.Workplane("XY").circle(outer_diameter/2).extrude(thickness)
    inner_void = cq.Workplane("XY").circle(inner_diameter/2).extrude(thickness)
    
    return ring.cut(inner_void).clean()

def body_tube_helper(
    outer_diameter,
    length,
    wall_thickness=2
):
    if outer_diameter <= wall_thickness * 2 or length <= 0:
        raise ValueError("Invalid dimensions")
    
    tube = cq.Workplane("XY").circle(outer_diameter/2).extrude(length)
    inner = cq.Workplane("XY").circle((outer_diameter - 2*wall_thickness)/2).extrude(length)
    
    return tube.cut(inner).clean()

def nose_cone_helper(
    base_diameter,
    height,
    thickness=2
):
    if base_diameter <= 0 or height <= 0:
        raise ValueError("Invalid dimensions")
    
    outer = cq.Workplane("XY").circle(base_diameter/2).cone(height, base_diameter/2, 0)
    inner = cq.Workplane("XY").circle((base_diameter - 2*thickness)/2).cone(height, (base_diameter - 2*thickness)/2, 0)
    
    return outer.cut(inner).clean()
