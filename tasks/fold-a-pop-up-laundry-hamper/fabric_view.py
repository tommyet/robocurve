"""Cloth skin from measured flexible-net nodes; never sets a physical pose."""
import numpy as np
from geometry import NX,NY
class FabricView:
 def __init__(self,drawing):
  from pxr import UsdGeom
  self.drawing=drawing;self.native=[]
  for prim in drawing.stage.Traverse():
   if prim.GetName().startswith(('mesh_','cloth_link_')) and '/materials/' in str(prim.GetPath()):
    geom=UsdGeom.Imageable(prim)
    if geom:geom.GetVisibilityAttr().Set('invisible');self.native.append(geom)
 def update(self,model):
  from pxr import UsdGeom
  if model.failed:
   for geom in self.native:geom.GetVisibilityAttr().Set('inherited')
   if 'cloth_skin' in self.drawing.meshes:UsdGeom.Imageable(self.drawing.meshes['cloth_skin'].GetPrim()).GetVisibilityAttr().Set('invisible')
   return
  points=np.array([model.p(f'mesh_0_{i}_{j}') for i in range(NX+1) for j in range(NY+1)])
  faces=[]
  for i in range(NX):
   for j in range(NY):
    a=i*(NY+1)+j;b=(i+1)*(NY+1)+j;faces.extend([(a,b,a+1),(a+1,b,b+1)])
  self.drawing.mesh('cloth_skin',points,faces,(.26,.46,.61))
