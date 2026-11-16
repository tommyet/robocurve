"""Conservative Brev wall-clock ledger and independent stop watchdog.

Arm immediately BEFORE requesting start. Count boot, setup, idle, runs and
shutdown latency; report provider STOPPED separately from a stop request.
The watchdog runs on this laptop, which must stay awake and online.
"""
import argparse,datetime,fcntl,json,os,re,shutil,subprocess,sys,time
from pathlib import Path


def utc(seconds):return datetime.datetime.fromtimestamp(seconds,datetime.timezone.utc).isoformat()
def append(folder,kind,**fields):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
 with (folder/'events.jsonl').open('a') as stream:
  fcntl.flock(stream,fcntl.LOCK_EX);stream.write(json.dumps(dict(event=kind,utc=utc(time.time()),**fields))+'\n');stream.flush();os.fsync(stream.fileno())
def status(config,now=None):
 now=time.time() if now is None else now
 return dict(instance=config['instance'],started_utc=utc(config['start_epoch']),deadline_utc=utc(config['deadline_epoch']),stop_request_due_utc=utc(config['stop_epoch']),elapsed_minutes=max(0.,(now-config['start_epoch'])/60),remaining_minutes=max(0.,(config['deadline_epoch']-now)/60),stop_due=now>=config['stop_epoch'],billing='Conservative start-request-to-provider-STOPPED wall time; not a provider invoice')
def is_stopped(output,instance):
 clean=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',output)
 return any(instance in line.split() and re.search(r'\bSTOPPED\b',line) for line in clean.splitlines())
def call(command):
 try:
  r=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=45)
  return r.returncode,r.stdout[-6000:]
 except subprocess.TimeoutExpired:return 124,'CLI timed out after45s'
 except OSError as error:return 127,str(error)
def watch(folder):
 folder=Path(folder);config=json.loads((folder/'window.json').read_text());brev=config['brev'];lock=(folder/'watch.lock').open('w')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise SystemExit('watchdog already active')
 append(folder,'watchdog_started',pid=os.getpid())
 while True:
  state=status(config);(folder/'status.json').write_text(json.dumps(state,indent=2)+'\n')
  if state['stop_due'] or (folder/'STOP_NOW').exists():
   code,output=call([brev,'stop',config['instance']]);append(folder,'stop_requested',returncode=code,output=output)
   code,output=call([brev,'ls']);append(folder,'provider_check',returncode=code,output=output)
   if code==0 and is_stopped(output,config['instance']):
    ended=time.time();state.update(provider_state='STOPPED',stopped_utc=utc(ended),total_window_minutes=(ended-config['start_epoch'])/60);(folder/'status.json').write_text(json.dumps(state,indent=2)+'\n');append(folder,'provider_stopped',total_window_minutes=state['total_window_minutes']);return
  time.sleep(15)
def arm(folder,instance,minutes,buffer_minutes):
 folder=Path(folder)
 if not 0<buffer_minutes<minutes<=120:raise ValueError('budget must be<=120min with a positive shutdown buffer')
 folder.mkdir(parents=True,exist_ok=False);start=time.time();brev=shutil.which('brev')
 if not brev:raise RuntimeError('brev CLI missing')
 config=dict(instance=instance,brev=brev,start_epoch=start,deadline_epoch=start+60*minutes,stop_epoch=start+60*(minutes-buffer_minutes),minutes=minutes,shutdown_buffer_minutes=buffer_minutes)
 (folder/'window.json').write_text(json.dumps(config,indent=2)+'\n');append(folder,'window_armed',**status(config))
 with (folder/'watchdog.log').open('w') as log:child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'watch','--ledger',str(folder.resolve())],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 (folder/'watchdog.pid').write_text(str(child.pid)+'\n')
 awake=shutil.which('caffeinate')
 if sys.platform=='darwin' and awake:
  subprocess.Popen([awake,'-dimsu','-w',str(child.pid)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
 return status(config)
def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 a=sub.add_parser('arm');a.add_argument('--instance',required=True);a.add_argument('--minutes',type=float,default=120);a.add_argument('--shutdown-buffer-minutes',type=float,default=10);a.add_argument('--ledger',type=Path,required=True)
 for name in ('watch','status','stop','event'):
  q=sub.add_parser(name);q.add_argument('--ledger',type=Path,required=True)
  if name=='event':q.add_argument('name');q.add_argument('--detail',default='')
 args=p.parse_args()
 if args.command=='arm':print(json.dumps(arm(args.ledger,args.instance,args.minutes,args.shutdown_buffer_minutes),indent=2))
 elif args.command=='watch':watch(args.ledger)
 elif args.command=='stop':(args.ledger/'STOP_NOW').touch();append(args.ledger,'early_stop_requested')
 elif args.command=='event':append(args.ledger,args.name,detail=args.detail)
 else:
  config=json.loads((args.ledger/'window.json').read_text());stored=args.ledger/'status.json';state=json.loads(stored.read_text()) if stored.exists() else {}
  print(json.dumps(state if state.get('provider_state')=='STOPPED' else status(config),indent=2))
if __name__=='__main__':main()
