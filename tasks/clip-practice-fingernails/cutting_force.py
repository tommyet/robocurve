"""Published polystyrene cutting curve, with explicit thickness extrapolation.

Approximate plot readings from Ruchirabha, thesis chapter3, Fig3-16:
1mm thick,2mm wide polystyrene cut by an unidentified conventional clipper.
This is blade force, not handle force or a retail-tool calibration.
"""
import numpy as np
DEPTH_MM=np.array([0.,.05,.15,.25,.40,.60,.80,.90,1.0])
FORCE_PER_WIDTH_N_MM=np.array([0.,4.,11.,14.,12.,11.5,11.,2.,0.])

def blade_force(penetration_mm,engaged_width_mm,thickness_mm=1.):
 if thickness_mm<=0 or engaged_width_mm<0:raise ValueError('Invalid material dimensions')
 fraction=float(penetration_mm)/thickness_mm
 if not 0<fraction<1:return 0.
 # Linear thickness scaling is a dimensional approximation, not test data.
 return float(np.interp(fraction,DEPTH_MM,FORCE_PER_WIDTH_N_MM)*engaged_width_mm*thickness_mm)

def lever_input_from_blade(blade_force_n,effort_arm_mm=34.61,load_arm_mm=7.42):
 if min(effort_arm_mm,load_arm_mm)<=0:raise ValueError('Invalid lever dimensions')
 return blade_force_n*load_arm_mm/effort_arm_mm

if __name__=='__main__':
 assert blade_force(.25,2.,1.)==28.
 assert blade_force(0,2.)==blade_force(1.,2.)==0.
 assert np.isclose(lever_input_from_blade(28.),6.,atol=.01)
 print('Published-condition peak:28N at blade; approximately6N at lever before spring resistance.')
 print('Thickness scaling and other tools remain unvalidated.')
