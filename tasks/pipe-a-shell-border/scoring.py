"""Draft physical judging measures, computed from the final deposited surface.

No model events, commanded nozzle poses or intended shell centres earn credit.
The corresponding ruler/photo checks are documented in JUDGING.md. Thresholds
are provisional until a physical reference and an actual robot demo exist.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np


def _peaks(values, *, minimum, spacing, prominence):
    """Position-independent peaks; plateaus collapse to their centre."""
    a=np.asarray(values,float)
    candidates=[]
    i=1
    while i<len(a)-1:
        j=i
        while j+1<len(a) and abs(a[j+1]-a[i])<1e-10:j+=1
        if a[i]>=minimum and a[i]>a[i-1] and j+1<len(a) and a[j]>a[j+1]:
            k=(i+j)//2
            window=a[max(0,k-spacing):min(len(a),k+spacing+1)]
            if a[k]-float(window.min())>=prominence:candidates.append(k)
        i=max(i+1,j+1)
    chosen=[]
    for k in sorted(candidates,key=lambda k:a[k],reverse=True):
        if all(abs(k-j)>=spacing for j in chosen):chosen.append(k)
    return sorted(chosen)


def assess(x,y,volume,*,dx,emitted_m3,lost_m3=0.,airborne_m3=0.,damage_depth_m=0.,
           completed=False,tools_clear=False,other_tool_contact=False,_reverse_checked=False):
    try:x,y,volume=(np.asarray(a,float) for a in (x,y,volume))
    except (ValueError,TypeError):return {"score":0.,"reason":"invalid numeric surface data"}
    numbers=(dx,emitted_m3,lost_m3,airborne_m3,damage_depth_m)
    if (not all(type(v) in (float,int) and np.isfinite(v) and v>=0 for v in numbers)
            or not all(type(v) is bool for v in (completed,tools_clear,other_tool_contact))
            or x.ndim!=1 or y.ndim!=1 or len(x)<3 or len(y)<3 or dx<=0):
        return {"score":0.,"reason":"invalid grid or judgment types"}
    if (volume.shape!=(len(x),len(y)) or not all(np.isfinite(a).all() for a in (x,y,volume))
            or np.any(volume<0) or not np.allclose(np.diff(x),dx,rtol=1e-7,atol=1e-10)
            or not np.allclose(np.diff(y),dx,rtol=1e-7,atol=1e-10)):
        return {"score":0.,"reason":"invalid or incomplete material telemetry"}
    h=volume/dx**2
    X,Y=np.meshgrid(x,y,indexing="ij")
    target=(np.abs(X-.235)<=.009)&(Y>=-.047)&(Y<=.047)
    spill_area=float(((h>=.0005)&~target).sum()*dx**2)
    result={"score":0.,"status":"draft rubric; not submission evidence",
            "valid_shells":0,"shells":[],"spill_area_mm2":spill_area*1e6,
            "damage_mm":damage_depth_m*1e3}
    if not completed or damage_depth_m>.001 or spill_area>20e-6 or lost_m3>1e-9 or other_tool_contact:
        result["reason"]="incomplete evidence, cake/tool damage, spill, or unobserved lost material"
        return result
    cross=np.abs(x-.235)<=.009
    active=(y>=-.047)&(y<=.047)
    if cross.sum()<3 or active.sum()<3:
        return {"score":0.,"reason":"material grid does not resolve the marked strip"}
    yy=y[active];a=h[cross][:,active]
    profile=a.max(axis=0)
    width=(a>=.0005).sum(axis=0)*dx
    # Find shapes from the actual final surface, without fixed shell centres.
    heads=_peaks(width,minimum=.006,spacing=max(1,round(.009/dx)),prominence=.002)
    covered_by_valid_shell=np.zeros(len(yy),dtype=bool)
    for n,k in enumerate(heads):
        stop=heads[n+1] if n+1<len(heads) else len(yy)-1
        lower=k+max(1,round(.004/dx));upper=min(stop,k+round(.022/dx))
        if lower>=upper:continue
        candidates=np.arange(lower,upper+1)
        candidates=candidates[profile[candidates]>=.0005]
        if not len(candidates):continue
        tail=int(candidates[np.argmin(width[candidates])])
        head_h,head_w=float(profile[k]),float(width[k])
        tail_h,tail_w=float(profile[tail]),float(width[tail])
        transverse=a[:,k]
        ridges=_peaks(transverse,minimum=.001,spacing=max(1,round(.0015/dx)),prominence=.0003)
        tapered=(.0025<=head_h<=.008 and .006<=head_w<=.016 and
                 .0005<=tail_h<=min(.003,.65*head_h) and .001<=tail_w<=.65*head_w)
        ridged=len(ridges)>=2
        # Locate the leading rise in the measured footprint. Union the observed
        # intervals so adjacent shapes cannot double-count the same length.
        previous=np.arange(max(0,k-round(.006/dx)),k+1)
        narrow=previous[width[previous]<=.65*head_w]
        beginning=int(narrow[-1]) if len(narrow) else k
        length=float(yy[tail]-yy[beginning]) if tapered else 0.
        if tapered:covered_by_valid_shell[beginning:tail+1]=True
        result["shells"].append({"valid":bool(tapered),"visible_ridges":bool(ridged),
                                  "head_y_mm":float(yy[k]*1e3),"head_height_mm":head_h*1e3,
                                  "head_width_mm":head_w*1e3,"tail_height_mm":tail_h*1e3,
                                  "tail_width_mm":tail_w*1e3,"length_mm":length*1e3})
    count=sum(s["valid"] for s in result["shells"])
    valid_length=float(covered_by_valid_shell.sum()*dx)
    result["valid_shells"]=count
    result["valid_decorated_length_mm"]=valid_length*1e3
    covered=(a>=.0005).any(axis=0)[(yy>=-.043)&(yy<=.043)]
    longest=run=0
    for c in covered:
        run=0 if c else run+1;longest=max(longest,run)
    result["largest_gap_mm"]=longest*dx*1e3
    result["score"]=(.75 if valid_length>=.060 else .5 if valid_length>=.040 else
                       .25 if valid_length>=.020 else 0.)
    full=(valid_length>=.080 and count>=5 and longest*dx<=.002 and tools_clear
          and airborne_m3<=1e-9 and all(s["visible_ridges"] for s in result["shells"] if s["valid"]))
    if full:result["score"]=1.
    result["reason"]="final material shape; ridge preservation and released, continuous finish required for full score"
    if not _reverse_checked:
        # The instruction permits either piping direction. Mirror the measured
        # surface around Y=0; neither its placement nor quality changes.
        reversed_result=assess(x,-y[::-1],volume[:,::-1],dx=dx,emitted_m3=emitted_m3,
                               lost_m3=lost_m3,airborne_m3=airborne_m3,damage_depth_m=damage_depth_m,
                               completed=completed,tools_clear=tools_clear,other_tool_contact=other_tool_contact,
                               _reverse_checked=True)
        if reversed_result['score']>result['score']:
            reversed_result['piping_direction']='-Y'
            return reversed_result
    result['piping_direction']='+Y'
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("state",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    with np.load(a.state,allow_pickle=False) as s:
        r=assess(s["x"],s["y"],s["volume"],dx=float(s["dx"]),
                 emitted_m3=float(s["emitted_m3"]),lost_m3=float(s["lost_m3"]),
                 airborne_m3=float(s["airborne_m3"]),damage_depth_m=float(s["damage_depth_m"]))
    data=json.dumps(r,indent=2)+"\n"
    if a.out:a.out.write_text(data)
    else:print(data,end="")


if __name__=="__main__":main()
