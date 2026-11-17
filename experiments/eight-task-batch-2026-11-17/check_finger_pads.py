"""Inspect the actual collision-pad interval at the centre line; CPU only."""
import numpy as np,xml.etree.ElementTree as ET,struct
from pathlib import Path
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
from yam_arena import ASSET_DIR
base=ASSET_DIR;tree=ET.parse(base/'yam_arm.urdf').getroot()
def origin(e):
 a=e.find('origin');return np.array([float(x) for x in a.get('xyz','0 0 0').split()]),Rotation.from_euler('xyz',[float(x) for x in a.get('rpy','0 0 0').split()]).as_matrix()
def vertices(p):
 data=p.read_bytes();n=struct.unpack('<I',data[80:84])[0];return np.array([struct.unpack('<12fH',data[84+50*i:134+50*i])[3:12] for i in range(n)]).reshape(-1,3)
for side in ['left','right']:
 link=tree.find(f"link[@name='tip_{side}']");j=tree.find(f"joint[@name='joint{7 if side=='left' else 8}']");jp,jR=origin(j);hulls=[]
 for e in link.findall('collision'):
  op,oR=origin(e);pts=(vertices(base/e.find('geometry/mesh').get('filename'))@oR.T+op)@jR.T+jp;hulls.append(ConvexHull(pts).equations)
 print(side)
 for z in np.arange(.118,.150,.002):
  intervals=[]
  for eq in hulls:
   n=eq[:,:3];b=eq[:,3]+n[:,2]*z;positive=n[:,0]>1e-8;negative=n[:,0]<-1e-8;zero=~(positive|negative)
   if np.any(b[zero]>1e-7):continue
   lo=np.max(-b[negative]/n[negative,0],initial=-1);hi=np.min(-b[positive]/n[positive,0],initial=1)
   if lo<=hi:intervals.append((lo,hi))
  if intervals:print(round((z-.134)*1000),np.round(np.array(intervals)*1000,2).tolist())
