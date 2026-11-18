"""Cloth skin from measured flexible-net nodes; never sets a physical pose."""
import numpy as np
from geometry import NX,NY,BODIES
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
  points=[];faces=[]
  def middle(i,j,di,dj):
   name=f'cloth_link_{i}_{j}_{di}_{dj}_0'
   if name in model.index:
    part=BODIES[model.index[name]]
    return model.p(name,[part['shapes'][0]['size'][0]/2,0,0])
   return (model.p(f'mesh_0_{i}_{j}')+model.p(f'mesh_0_{i+di}_{j+dj}'))/2
  for i in range(NX):
   for j in range(NY):
    # Follow actual bent thread midpoints; the panel centre is only a visual
    # interpolation. No rendered vertex commands a material body's position.
    ring=[model.p(f'mesh_0_{i}_{j}'),middle(i,j,1,0),model.p(f'mesh_0_{i+1}_{j}'),middle(i+1,j,0,1),model.p(f'mesh_0_{i+1}_{j+1}'),middle(i,j+1,1,0),model.p(f'mesh_0_{i}_{j+1}'),middle(i,j,0,1)]
    start=len(points);points.extend(ring);points.append(np.mean(ring,axis=0))
    faces.extend((start+k,start+(k+1)%8,start+8) for k in range(8))
  self.drawing.mesh('cloth_skin',np.array(points),faces,(.26,.46,.61))
