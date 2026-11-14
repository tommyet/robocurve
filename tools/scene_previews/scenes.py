"""Unscored layout previews. These fixed proxies do not implement task mechanics."""
import math
from yam_arena.task_file import Box, Cylinder, Sphere
T=.7475
SCENE='station'
OBJECTS=[]
def box(name,p,s,c):OBJECTS.append(Box(name,pos=p,size=s,color=c))
def ball(name,p,r,c):OBJECTS.append(Sphere(name,pos=p,radius=r,color=c))
def cylinder(name,p,r,h,c):OBJECTS.append(Cylinder(name,pos=p,radius=r,height=h,color=c))
def success(objects):return False
def score(objects):return 0.

def build(kind):
    OBJECTS.clear()
    box('mat',(.32,0,T+.001),(.56,.60,.002),(.24,.27,.30))
    brown=(.59,.37,.18)
    if kind=='ethernet':
        # 4 columns x 2 rows; dark sockets, six neighbours, one service plug.
        box('panel',(.46,0,T+.13),(.028,.16,.105),(.72,.75,.79))
        for row in range(2):
            for col in range(4):
                i=row*4+col;y=(col-1.5)*.032;z=T+.11+row*.035
                box(f'port_{i}',(.442,y,z),(.012,.017,.014),(.025,.03,.035))
                if i==6:continue
                color=(1.,.39,.03) if i==1 else ((.05,.30,.85) if i%2 else (.09,.60,.34))
                box(f'plug_{i}',(.421,y,z),(.026,.012,.009),(.76,.83,.85))
                box(f'clip_{i}',(.417,y,z+.007),(.020,.005,.002),(.85,.91,.92))
                # Render-visible crowded cable paths; no flexible dynamics claim.
                for j in range(0):
                    u=j/14
                    x=.398-.19*u; yy=y+.018*math.sin(u*math.pi*2+i);zz=z-.075*u
                    ball(f'cable_{i}_{j}',(x,yy,zz),.0032,color)
        box('target_mark',(.438,.016,T+.167),(.004,.025,.004),(1.,.8,.05))
    elif kind=='hair':
        cylinder('bust_mount',(.43,0,T+.055),.055,.11,(.35,.38,.41))
        ball('head',(.43,0,T+.27),.074,(.78,.59,.46))
        ball('nose',(.354,0,T+.27),.012,(.78,.59,.46))
        # Long separate surface and inner locks, represented by fixed beads.
        for k in range(0):
            a=2*math.pi*k/22
            for j in range(20):
                u=j/19;r=.061+.017*u
                x=.445+r*math.cos(a);y=r*math.sin(a)
                z=T+.318-.245*u
                ball(f'lock_{k}_{j}',(x,y,z),.0065,(.075+.014*(k%3),.032,.014))
        # Dryer laid on its side: rectangular motor/nozzle and handle proxies.
        box('dryer_body',(.25,-.16,T+.035),(.095,.058,.055),(.85,.06,.20))
        box('dryer_nozzle',(.315,-.16,T+.035),(.045,.036,.030),(.18,.19,.21))
        box('dryer_handle',(.225,-.205,T+.025),(.030,.075,.035),(.85,.06,.20))
        box('dryer_switch',(.222,-.21,T+.045),(.015,.022,.004),(.035,.04,.05))
    else:
        cx=.34;cy=.02;L=.22;W=.18;H=.10;b=.003
        box('bottom',(cx,cy,T+.005),(L,W,b),brown)
        for sign in [-1,1]:
            tag='n' if sign==1 else 's'
            box('wall_'+tag,(cx,cy+sign*W/2,T+H/2),(L,b,H),brown)
            box('wall_'+('e' if sign==1 else 'w'),(cx+sign*L/2,cy,T+H/2),(b,W,H),brown)
            # Open flaps laid outward; layout preview only, no hinges here.
            box('flap_'+tag,(cx,cy+sign*(W/2+.043),T+H),(L,.083,b),brown)
            box('flap_'+('e' if sign==1 else 'w'),(cx+sign*(L/2+.043),cy,T+H),(.083,W,b),brown)
        if kind=='carton-breakdown':
            box('bottom_tape',(cx,cy,T+.002),(L,.048,.001),(.77,.63,.36))
            for sign in [-1,1]:
                box('tape_wrap_'+str(sign).replace('-','m'),(cx+sign*(L/2+.002),cy,T+.022),(.001,.048,.044),(.77,.63,.36))
            box('cutter_handle',(.22,-.21,T+.018),(.095,.027,.028),(1.,.36,.02))
            box('cutter_blade',(.278,-.21,T+.018),(.025,.015,.001),(.73,.76,.80))
        else:
            box('item_a',(cx-.04,cy,T+.029),(.065,.055,.05),(.12,.41,.85))
            box('item_b',(cx+.04,cy,T+.025),(.055,.065,.042),(.91,.29,.14))
            # Real roll form factor: original procedural annular mesh in runner.
            cylinder('tape_roll_proxy',(.18,-.19,T+.024),.05,.048,(.76,.59,.28))
            box('scissors_handle',(.38,-.22,T+.014),(.08,.035,.02),(.85,.12,.10))
            box('scissors_blade',(.435,-.22,T+.014),(.045,.014,.002),(.72,.76,.80))
    return OBJECTS
