"""Keep the spare arm clear while the native remover heel supplies support.

The task does not require a hand brace. This candidate preserves every right
arm command and all materials from the complete lever plan, but keeps the
left arm at its normal ready pose. It still needs physical extraction proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from motion_plan import load


def compile_one_hand(source):
    from yam_arena.constants import READY
    plan,actions=load(source)
    result=dict(plan)
    frames=[]
    names={'Approach remover and papers':'Approach the remover',
           'Lower to handle and hold papers':'Lower to the remover handle',
           'Release pressure on the papers':'Hold the extracted staple clear'}
    for f,a in zip(plan['frames'],actions):
        a=a.copy();a[:6]=READY;a[6]=1.
        frames.append(dict(f,stage=names.get(f['stage'],f['stage']),action14=a.tolist()))
    result.update(frames=frames,requested_stage='one_handed_lever_candidate',
        left_arm='Normal READY pose throughout; no paper brace',
        supporting_contact='The native15mm-wide remover heel bears on the sheets beside the crown.',
        base_plan_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest(),
        limitations=['One-handed extraction is unproven; heel contact must supply the opposing load.',
                     'No paper attachment, altered strength or relaxed crossing/continuity guard.'])
    result['source_sha256']=dict(plan['source_sha256'])
    result['source_sha256']['one_hand_plan.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();result=compile_one_hand(a.source);a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(actions=result['action_count'],seconds=result['seconds'])))
