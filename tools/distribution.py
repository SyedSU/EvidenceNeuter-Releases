"""Canonical fail-closed distribution validation; signing is offline, never publishing."""
import argparse,base64,datetime,hashlib,json,re,zipfile
from pathlib import Path
from urllib.parse import urlsplit
import jsonschema
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import padding
ROOT=Path(__file__).resolve().parents[1]
IDS=['genesis','lab','bot','academy','flow','council']
GATES=['trustConfigured','signedArtifactsPublished','windowsAcceptancePassed','licensesApproved','authenticodeVerified']
def schema(data,name):
 try:jsonschema.Draft202012Validator(json.loads((ROOT/'schemas'/f'{name}.schema.json').read_text()),format_checker=jsonschema.FormatChecker()).validate(data)
 except jsonschema.ValidationError as e:raise ValueError(e.message) from e

def release_url(value):
 u=urlsplit(value)
 if u.scheme!='https' or u.netloc!='github.com' or u.query or u.fragment or not re.fullmatch(r'/SyedSU/EvidenceNeuter-Releases/releases/download/[^/]+/[^/]+',u.path):raise ValueError('Unapproved release URL')
def freshness(data,minimum_sequence=0):
 if datetime.datetime.fromisoformat(data['expires'].replace('Z','+00:00'))<=datetime.datetime.now(datetime.timezone.utc) or data['sequence']<minimum_sequence:raise ValueError('Expired or replayed metadata')
def validate_catalog(data,authenticated=False,minimum_sequence=0):
 schema(data,'catalog');freshness(data,minimum_sequence)
 if [x['id'] for x in data['products']]!=IDS or data['infrastructure']['id']!='hub':raise ValueError('Stable identity set mismatch')
 entries=[data['infrastructure']]+data['products']
 for e in entries:
  for image in e['screenshots']:
   u=image['url']
   if u.startswith('/') and not u.startswith('//') and not any(x in u.split('/') for x in ['..','.']):pass
   else:release_url(u)
  if e['release']:
   if e['release']['download']:release_url(e['release']['download']['url'])
   if e['id']=='genesis' and e['release']['download'] is not None:raise ValueError('Genesis requires signed component manifest')
   release_url(e['release']['manifestUrl'])
   if any(e[k]!=e['release'][k] for k in ['version','sourceCommit']):raise ValueError('Release provenance mismatch')
  if e['availability']=='available' and (not e['version'] or not e['sourceCommit'] or not e['release']):raise ValueError('Incomplete available entry')
 if data['publicDownloads']:
  g=data['releaseGate']
  if not authenticated or g['status']!='approved' or g['reasons'] or not all(g[x] for x in GATES):raise ValueError('Download gate blocked')
  for e in entries[:2]:
   if e['availability']!='available' or not e['licenseNotices']:raise ValueError('Incomplete public entry')
  if not data['infrastructure']['release']['download']:raise ValueError('Hub download facts required')
  for c in data['products'][0]['components'].values():
   if not c or not c['version'] or not c['sourceCommit'] or not c['licenseNotices']:raise ValueError('Missing component provenance')
 return data

def safe_path(value):
 if len(value)>180 or '\\' in value or value.startswith('/') or any(not s or s in ['.','..'] or s.endswith(('.', ' ')) or re.search(r'[<>:"|?*\x00-\x1f]',s) or re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)',s,re.I) for s in value.split('/')):raise ValueError('Unsafe package path')
def validate_manifest(data,minimum_sequence=0):
 schema(data,'genesis-manifest');freshness(data,minimum_sequence)
 if data['saveSchema']==4 and tuple(map(int,data['minimumHubVersion'].split('.')))<(0,3,0):raise ValueError('Save schema4 requires Hub0.3.0')
 if sorted(p['kind'] for p in data['packages'])!=['game','model','runtime']:raise ValueError('Components mismatch')
 seen=set();total=0
 for p in data['packages']:
  release_url(p['url'])
  for f in p['files']:
   safe_path(f['path']);path=({'game':'','runtime':'brain/','model':'model/'}[p['kind']]+f['path']).lower()
   if path in seen or p['kind']=='game' and (path.startswith(('brain/','model/')) or path=='release.json'):raise ValueError('Overlapping package path')
   seen.add(path);total+=f['size']
 if total>8589934592 or not {'evidencegenesis.exe','brain/llama-server.exe','model/genesis.gguf'}<=seen:raise ValueError('Incomplete/oversized release')
 return data

def validate_hub(data,minimum_sequence=0):
 schema(data,'hub-manifest');freshness(data,minimum_sequence);release_url(data['installer']['url']);return data

def sign(data,key):
 if key.key_size<3072:raise ValueError('RSA key must be >=3072 bits')
 expires=datetime.datetime.fromisoformat(data['expires'].replace('Z','+00:00'))
 if expires>datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=30):raise ValueError('Signing expiry exceeds30days')
 payload=json.dumps(data,separators=(',',':'),ensure_ascii=False).encode();sig=key.sign(payload,padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=32),hashes.SHA256())
 return {'payload':base64.b64encode(payload).decode(),'signature':base64.b64encode(sig).decode()}
def verify(envelope,key,kind='catalog',minimum_sequence=0):
 try:
  schema(envelope,'signed-envelope')
  if key.key_size<3072:raise ValueError('Weak key')
  payload=base64.b64decode(envelope['payload'],validate=True)
  if len(payload)>2097152:raise ValueError('Metadata oversized')
  key.verify(base64.b64decode(envelope['signature'],validate=True),payload,padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=32),hashes.SHA256())
  data=json.loads(payload)
  return validate_catalog(data,True,minimum_sequence) if kind=='catalog' else (validate_hub(data,minimum_sequence) if kind=='hub' else validate_manifest(data,minimum_sequence))
 except Exception as e:raise ValueError('Invalid signed metadata: '+str(e)) from e

def package(source,output):
 files=[]
 with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(Path(source).rglob('*')):
   if p.is_symlink():raise ValueError('Symlink forbidden')
   if not p.is_file():continue
   name=p.relative_to(source).as_posix();safe_path(name);data=p.read_bytes();info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data)
   files.append({'path':name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 if not files:raise ValueError('Empty package')
 data=Path(output).read_bytes();return {'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'files':files}
def check_lock(lock,product,version,source_commit,save_schema=None):
 e=lock.get(product)
 if not e or e.get('version')!=version or e.get('sourceCommit')!=source_commit or not re.fullmatch('[a-f0-9]{40}',source_commit) or product=='genesis' and e.get('saveSchema')!=save_schema:raise ValueError('Source/version compatibility lock mismatch')
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['validate-catalog','validate-manifest','verify','sign','package']);p.add_argument('input');p.add_argument('--output');p.add_argument('--key');p.add_argument('--lock');p.add_argument('--kind',default='catalog',choices=['catalog','manifest','hub']);a=p.parse_args()
 if a.command=='package':result=package(Path(a.input),Path(a.output))
 else:
  data=json.loads(Path(a.input).read_text())
  if a.command=='validate-catalog':result=validate_catalog(data)
  elif a.command=='validate-manifest':result=validate_manifest(data)
  elif a.command=='verify':result=verify(data,serialization.load_pem_public_key(Path(a.key).read_bytes()),a.kind)
  else:
   if not a.lock:raise ValueError('Signing requires reviewed source/version lock')
   lock=json.loads(Path(a.lock).read_text())
   if a.kind=='catalog':
    for entry in [data['infrastructure']]+data['products']:
     if entry['availability']=='available':check_lock(lock,entry['id'],entry['version'],entry['sourceCommit'],entry.get('saveSchema'))
   else:check_lock(lock,data['product'],data['version'],data['sourceCommit'],data.get('saveSchema'))
   (validate_catalog(data,True) if a.kind=='catalog' else (validate_hub(data) if a.kind=='hub' else validate_manifest(data)));result=sign(data,serialization.load_pem_private_key(Path(a.key).read_bytes(),password=None))
 if a.output and a.command!='package':Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
 else:print(json.dumps(result,indent=2))
if __name__=='__main__':main()
