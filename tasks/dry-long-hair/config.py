"""Explicit coarse bundle/airflow parameters, not a calibrated fibre model."""
TOP=.7475
HEAD=(.43,0.,1.045)
HEAD_RADIUS=.065
LOCKS=16
SEGMENTS=10
LENGTH=.025
RADIUS=.0038
DRY_MASS_PER_SEGMENT=.00020
WATER_PER_PATCH=.000010
PATCHES_PER_SEGMENT=4
AIR_TEMPERATURE=55.
HEATER_LIMIT=800.
MAX_TEMPERATURE=50.
DRY_FRACTION=.10
DRYER_START=(.23,-.16,TOP+.117)
SWITCH_START=(DRYER_START[0]-.037,DRYER_START[1],DRYER_START[2]-.055)
SWITCH_TRAVEL=.004

def root(k):
 import math
 # Back and side hair, with an unobstructed face at negative x.
 a=-2.12+4.24*k/(LOCKS-1)
 return (HEAD[0]+.068*math.cos(a),.068*math.sin(a),HEAD[2]+.025)
def segment(k,j):
 x,y,z=root(k);return (x,y,z-LENGTH*(j+.5))
