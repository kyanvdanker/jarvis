import numpy as np
import trimesh
from vispy import app, scene
import vision.camera_control

canvas = None
view = None
mesh_visual = None
viewer_running = False

def start_viewer():
    global canvas, view, mesh_visual, viewer_running
    vision.camera_control.viewer_open = True


    if viewer_running:
        return  # already open

    viewer_running = True

    def _run():
        global canvas, view, mesh_visual
        canvas = scene.SceneCanvas(keys='interactive', size=(900, 700), show=True, title="Jarvis CAD Viewer")
        view = canvas.central_widget.add_view()
        view.camera = scene.cameras.TurntableCamera(fov=45, distance=3)

        mesh_visual = scene.visuals.Mesh(vertices=np.zeros((3, 3)), faces=np.zeros((1, 3), dtype=int))
        view.add(mesh_visual)

        grid = scene.visuals.GridLines(color=(0.5, 0.5, 0.5, 1))
        view.add(grid)

        app.run()

    import threading
    threading.Thread(target=_run, daemon=True).start()


def close_viewer():
    global canvas, viewer_running
    if canvas is not None:
        canvas.close()
    viewer_running = False


def load_stl_into_viewer(stl_path):
    """Replace the mesh in the viewer."""
    global mesh_visual

    mesh = trimesh.load(stl_path)
    mesh.apply_translation(-mesh.centroid)
    mesh.apply_scale(1.0 / mesh.scale)

    vertices = np.array(mesh.vertices)
    faces = np.array(mesh.faces)

    mesh_visual.set_data(vertices=vertices, faces=faces)


# -----------------------------
# CAMERA CONTROL FUNCTIONS
# -----------------------------

def rotate_camera(dx=0, dy=0):
    """Rotate camera by dx, dy degrees."""
    if view is None:
        return
    cam = view.camera
    cam.azimuth += dx
    cam.elevation += dy
    view.camera = cam


def zoom_camera(amount):
    """Zoom camera in/out."""
    if view is None:
        return
    cam = view.camera
    cam.distance *= amount
    view.camera = cam


def reset_camera():
    """Reset camera to default."""
    if view is None:
        return
    cam = view.camera
    cam.azimuth = 0
    cam.elevation = 30
    cam.distance = 3
    view.camera = cam

def move_object(dx, dy, dz=0):
    # apply translation to the selected object
    pass

def rotate_object(rx, ry, rz):
    # apply rotation to the selected object
    pass

