"""Outcome counterexamples, not simulated feasibility evidence."""
from pathlib import Path
import sys,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tasks/pin-a-loose-trouser-hem'))
from model import Model

def threaded(names=('front_6_0','hem_6_0','front_9_0','hem_9_1')):
 m=Model();m.holes={n:np.zeros(3) for n in names}
 for n,x in zip(names,[.010,.013,.026,.029]):m.poses[m.index[n],:3]=m.p('pin_arm',[x,0,0])
 return m
assert Model().score()==0.
m=threaded();assert m.score()==.5
m.latched=True;m.release=3.;assert m.score()==1.
m.broken.add('hole_front_6_0');assert m.score()==0.
m=threaded(('front_2_0','hem_2_0','front_3_0','hem_3_1'));m.latched=True;m.release=3.;assert m.score()==0.
m=threaded()
for n in m.holes:m.poses[m.index[n],:3]+=[0,0,.10]
assert m.score()==0.,'A withdrawn pin must not earn puncture-history credit.'
m=threaded();m.holes={'front_6_0':np.zeros(3)};assert m.score()==.25
print('7 pin-scoring counterexample checks passed; these are not physics trials.')
