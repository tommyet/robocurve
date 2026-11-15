import sys
sys.dont_write_bytecode=True
from pathlib import Path
import cProfile,pstats,io,json,time
from baseline_safety import ScoopSafety
from workload import ROOT,selected,tick
m=ScoopSafety();indices=selected();pr=cProfile.Profile();start=time.perf_counter();pr.enable()
for i in indices:tick(m,i)
pr.disable();elapsed=time.perf_counter()-start;pr.dump_stats(str(ROOT/'baseline.prof'));s=io.StringIO();pstats.Stats(pr,stream=s).strip_dirs().sort_stats('cumulative').print_stats(25);(ROOT/'baseline-profile.txt').write_text(s.getvalue());print('INDICES',indices,'ticks',len(indices),'seconds',elapsed,flush=True);print(s.getvalue(),flush=True)
(ROOT/'baseline-profile-summary.json').write_text(json.dumps(dict(ticks=len(indices),checks=2*len(indices),indices=indices,elapsed_s=elapsed),indent=2)+'\n')
