# viewer.py
import cadquery as cq

_current_obj = None
_rotation = [0, 0, 0]  # x, y, z rotation in degrees


def show_object(obj):
    global _current_obj
    _current_obj = obj

    rotated = (
        obj.rotate((0, 0, 0), (1, 0, 0), _rotation[0])
           .rotate((0, 0, 0), (0, 1, 0), _rotation[1])
           .rotate((0, 0, 0), (0, 0, 1), _rotation[2])
    )

    rotated.val().exportStl("output/preview.stl")
    print("Updated preview: output/preview.stl")


def rotate_view(axis, degrees):
    global _rotation

    if axis == "x":
        _rotation[0] += degrees
    elif axis == "y":
        _rotation[1] += degrees
    elif axis == "z":
        _rotation[2] += degrees

    if _current_obj is not None:
        show_object(_current_obj)


def reset_view():
    global _rotation
    _rotation = [0, 0, 0]

    if _current_obj is not None:
        show_object(_current_obj)
