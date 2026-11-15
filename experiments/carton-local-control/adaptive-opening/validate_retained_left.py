"""Complete idle-arm/task checks at retained nodes; no search expansion."""
import sys
sys.dont_write_bytecode = True
import time
import json
from pathlib import Path
from planner import Planner, ROOT, READY
from yam_arena.constants import FINGER_OPEN

report = json.loads((ROOT/'planner-report.json').read_text())
p = Planner()
p.started = time.monotonic()-report['elapsed_wall_s']
p.ik_count = report['ik_attempts']
p.full_count = report['full_geometry_certificates']
rows = []
for node in report['retained_nodes']:
    _, _, _, obs = p.state(node['angle_deg'], node['heading_deg'])
    checks = []
    for fingers in ([-.003, -.003], [-node['contact']['common_opening_m']]*2):
        other = p.model.parts('right', node['q'], fingers)
        check = p.full('left', READY, [FINGER_OPEN]*2, obs, other)
        checks.append(check)
    rows.append(dict(angle_deg=node['angle_deg'], heading_deg=node['heading_deg'],
                     idle_left_vs_current_task_and_open_loaded_right=checks))
    if not all(c['safe'] for c in checks):
        break
out = dict(scope='POSTVALIDATION_ONLY_NO_ADDITIONAL_SEARCH; full315idleLEFT against moving north panel and allcurrent task OBBs/table/actualright315open+loaded',
           passed=all(all(c['safe'] for c in r['idle_left_vs_current_task_and_open_loaded_right']) for r in rows)
                  and len(rows)==len(report['retained_nodes']),
           retained_nodes_checked=len(rows), combined_ik=p.ik_count,
           combined_full_geometry=p.full_count,
           combined_measured_execution_wall_s=time.monotonic()-p.started,
           records=rows)
(ROOT/'retained-left-validation.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in out.items()if k!='records'},indent=2))
