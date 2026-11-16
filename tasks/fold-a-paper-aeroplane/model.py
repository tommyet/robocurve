import numpy as np
from paper import Paper
from common import TABLE

class Model:
 def __init__(self):
  self.paper=Paper();self.events=self.paper.grips.events;self.time=0.;self.release=0.
 def update(self,hands,dt=.05):
  self.time+=dt;self.paper.step(hands,dt);self.release=self.release+dt if not self.paper.grips.held else 0.
 def measure(self):return dict(failed=self.paper.failed,maximum_stretch=self.paper.max_strain,crease_stencils=int(np.sum(abs(self.paper.rest_angle)>.35)),released_seconds=self.release)
 def score(self):return 0. # Development only; scorer follows validated geometry.
 def state(self):return self.paper.state()
 def draw(self,d):
  d.mesh('paper_front',self.paper.p,self.paper.faces,(.62,.78,.92))
  d.mesh('paper_back',self.paper.p,[tuple(reversed(f)) for f in self.paper.faces],(.95,.95,.93))
  d.meshes['paper_front'].GetDoubleSidedAttr().Set(False)
  d.meshes['paper_back'].GetDoubleSidedAttr().Set(False)
