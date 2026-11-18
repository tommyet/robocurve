"""Synthetic outcome unit checks only; never submitted as physical evidence."""
import importlib,sys,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
SLUGS=['remove-an-avocado-stone','strip-a-kale-leaf','pin-a-loose-trouser-hem','apply-a-temporary-tattoo','fold-a-pop-up-laundry-hamper','peel-a-silicone-baking-cup','mash-cooked-potato','cut-a-cigar-cap']
results=[]
for slug in SLUGS:
 for k in ['model','native_model','geometry','geometry_helpers','common']:sys.modules.pop(k,None)
 sys.path.insert(0,str(ROOT/'tasks'/slug));g=importlib.import_module('geometry');M=importlib.import_module('model').Model
 def fresh():return M()
 def move(m,n,p):m.poses[m.index[n],:3]=p
 def check(m,expected,label):
  actual=m.score();assert actual==expected,(slug,label,actual,expected,m.measure());results.append(dict(task=slug,case=label,score=actual))
 m=fresh();check(m,0.,'untouched initial state')
 if slug=='remove-an-avocado-stone':
  m.broken.add('stone_bond');check(m,0.,'bond break without removal')
  move(m,'stone',m.p('dish')+[0,0,.025]);m.release=3.;check(m,1.,'intact fruit and deposited stone')
  m.broken.add('flesh_bond_0');check(m,0.,'flesh damage invalidates deposit')
 elif slug=='strip-a-kale-leaf':
  m.broken={j['name'] for j in g.JOINTS if j['name'].startswith('attach_')}
  for n in m.names:
   if n.startswith('stalk_'):move(m,n,m.p(n)+[0,.4,0])
  m.release=3.;check(m,1.,'separated intact stalk and retained leaf')
  for n in m.names:
   if n.startswith('leaf_'):move(m,n,m.p(n)-[0,0,1.])
  check(m,0.,'discarded leaf earns no credit')
 elif slug=='pin-a-loose-trouser-hem':
  m.holes={n:np.zeros(3) for n in ['front_6_0','hem_6_0','front_9_0','hem_9_1']}
  for n,x in zip(m.holes,[.010,.013,.026,.029]):move(m,n,m.p('pin_arm',[x,0,0]))
  check(m,.5,'both loose layers retained on the shaft')
  m.latched=True;m.release=3.;check(m,1.,'threaded pin closed and released')
  m.holes['back_4_0']=np.zeros(3);check(m,0.,'back of leg pinned shut')
 elif slug=='apply-a-temporary-tattoo':
  original={n:np.asarray(p) for n,p in g.INK_ORIGINAL.items()}
  for n,p in original.items():m.transferred[n]=np.array([p[0],g.ARM_RADIUS*np.sin(p[1]/g.ARM_RADIUS),g.ARM_RADIUS*np.cos(p[1]/g.ARM_RADIUS)])
  for n in m.names:
   if n.startswith('paper_'):move(m,n,m.p(n)+[0,.2,0])
  m.release=3.;check(m,1.,'intact registered transferred image')
  for n in m.transferred:m.transferred[n][0]+=.10
  check(m,0.,'image outside target')
 elif slug=='fold-a-pop-up-laundry-hamper':
  wire=[n for n in m.names if n.startswith('wire_')];centre=np.mean([m.p(n) for n in wire],axis=0)
  for n in wire:move(m,n,centre+(m.p(n)-centre)*[.35,.35,1.])
  check(m,.5,'compact packet without retaining loop')
  m.broken.add('wire_joint_0_0');check(m,0.,'broken frame cannot pass')
 elif slug=='peel-a-silicone-baking-cup':
  m.broken={'adhesion_'+str(i) for i in range(g.N)}|{'bottom_adhesion'};move(m,'cup_bottom',[.44,0,g.TABLE+.012]);m.release=3.;check(m,1.,'empty intact cup and released muffin')
  m.broken.add('crumb_bond_0');check(m,0.,'broken muffin invalidates peel')
 elif slug=='mash-cooked-potato':
  m.broken={j['name'] for j in g.JOINTS};m.release=3.;check(m,1.,'retained small lumps')
  names=[n for n in m.names if n.startswith('food_')]
  for n in names[:20]:move(m,n,[2,2,0])
  check(m,0.,'over five percent spilled')
 elif slug=='cut-a-cigar-cap':
  m.work[:]=.1;check(m,0.,'cutting work without separated cap')
  m.cut=True;move(m,'cap',m.p('cap')+[.04,0,0]);check(m,.5,'clean separated cap while held')
  m.release=3.;check(m,1.,'clean released cigar')
  m.crush=.0011;check(m,0.,'crushed wrapper invalidates cut')
 # A corrupted saved failure flag must not hide a native integrity break.
 if slug!='mash-cooked-potato':
  m.failed=False;state=m.state();restored=fresh();restored.restore(state)
  if m.integrity_failed():assert restored.failed
 sys.path.pop(0)
print(json.dumps({'kind':'synthetic scoring unit checks, not physics evidence','passed':len(results),'cases':results},indent=2))
