"""Continuous cloth skin driven only by the measured native panel poses.

The coarse collision panels and their passive seams are unchanged. The skin
averages adjacent panel corners at shared textile nodes; it does not set any
body pose or cover a broken seam. Failed fabric is shown as its native panels.
"""
import numpy as np
from geometry import BODIES, NX, NY, DX, DY

class FabricView:
    def __init__(self, drawing):
        from pxr import UsdGeom
        self.drawing=drawing;self.native=[];self.failed=False
        self.specs={b['name']:b for b in BODIES}
        for prim in drawing.stage.Traverse():
            if prim.GetName().startswith('mesh_') and '/materials/' in str(prim.GetPath()):
                geom=UsdGeom.Imageable(prim)
                if geom:geom.GetVisibilityAttr().Set('invisible');self.native.append(geom)

    def update(self, model):
        from pxr import UsdGeom
        if model.failed:
            for geom in self.native:geom.GetVisibilityAttr().Set('inherited')
            for name,mesh in self.drawing.meshes.items():
                if name.startswith('cloth_skin_'):UsdGeom.Imageable(mesh).GetVisibilityAttr().Set('invisible')
            self.failed=True;return
        for layer in range(4):
            ny,dy=NY,DY
            nodes=np.zeros((NX+1,ny+1,3));counts=np.zeros((NX+1,ny+1,1))
            for i in range(NX):
                for j in range(ny):
                    name=f'mesh_{layer}_{i}_{j}';width=DX
                    for di in [0,1]:
                        for dj in [0,1]:
                            # Coordinates follow the sewn panel grid.
                            point=model.p(name,[(di-.5)*width,(dj-.5)*dy,0.])
                            nodes[i+di,j+dj]+=point;counts[i+di,j+dj]+=1
            nodes/=counts
            faces=[]
            for i in range(NX):
                for j in range(ny):
                    a=i*(ny+1)+j;b=(i+1)*(ny+1)+j
                    faces.extend([(a,b,a+1),(a+1,b,b+1)])
            self.drawing.mesh('cloth_skin_'+str(layer),nodes.reshape(-1,3),faces,(.26,.46,.61))
