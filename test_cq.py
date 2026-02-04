import cadquery as cq

result = cq.Workplane("XY").circle(10).extrude(20)
result.val().exportStl("test.stl")

print("CadQuery OK")
