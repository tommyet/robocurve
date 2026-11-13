"""Inactive candidate ordinary peg rests, for a separate native reset probe.

Each stepped wooden block supports a closed peg through contact alone. The
outer20 mm of its handles overhang so a real finger can approach underneath.
These are not fixtures or constraints on the peg; they are not in task.py yet.
"""
from scene import TABLE


def peg_positions():
    return {('Left' if sign>0 else 'Right'):(.25,sign*.28,TABLE+.051) for sign in (-1,1)}


def geometry():
    solids={}
    for side,pos in peg_positions().items():
        x,y,_=pos
        # Jaw underside is6.5 mm below the hinge, handle underside11 mm.
        solids[side+'JawRest']=dict(kind='box',size=(.035,.016,.0435),
                                  center=(x+.0175,y,TABLE+.0435/2))
        solids[side+'HandleRest']=dict(kind='box',size=(.015,.016,.039),
                                     center=(x-.0075,y,TABLE+.039/2))
    return solids


def author(stage):
    from native_cloth import author_box
    for name,solid in geometry().items():
        author_box(stage,'/World/PegRests/'+name,solid['size'],solid['center'],(.59,.39,.22))
