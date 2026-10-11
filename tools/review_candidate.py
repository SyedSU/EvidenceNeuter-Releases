"""Read-only workflow verification before protected publication."""
import json,os,re,subprocess
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from distribution import validate_candidate,verify
from public_assets import verify_public_assets

def reviewed_json(path):
 p=Path(path)
 if not path or p.is_absolute() or '..' in p.parts or not p.is_file() or p.suffix!='.json' or not p.resolve().is_relative_to(Path.cwd().resolve()):raise SystemExit('Invalid reviewed metadata path')
 return json.loads(p.read_text())
def public_key(name,required=True):
 value=os.environ.get(name,'')
 if not value:
  if required:raise SystemExit('Reviewed production trust prerequisite absent: '+name)
  return None
 return serialization.load_pem_public_key(value.encode())
commit=os.environ['COMMIT'];tag=os.environ['TAG']
if not re.fullmatch('[a-f0-9]{40}',commit) or subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()!=commit:raise SystemExit('Reviewed source commit mismatch')
if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,100}',tag):raise SystemExit('Invalid reviewed metadata tag')
kind=os.environ['KIND'];hub_file=os.environ.get('HUB_FILE','');genesis_file=os.environ.get('GENESIS_FILE','')
envelope=reviewed_json(os.environ['FILE']);catalog_key=public_key('PUBLIC_KEY')
public_activation=kind=='catalog' and verify(envelope,catalog_key,kind)['publicDownloads']
hub_envelope=reviewed_json(hub_file) if hub_file else None
genesis_envelope=reviewed_json(genesis_file) if genesis_file else None
hub_key=public_key('HUB_PUBLIC_KEY',public_activation)
genesis_key=public_key('GENESIS_PUBLIC_KEY',public_activation)
data=validate_candidate(envelope,catalog_key,kind,json.loads(Path('catalog/source-lock.json').read_text()),
 hub_envelope,genesis_envelope,{'hub':os.environ.get('HUB_URL',''),'genesis':os.environ.get('GENESIS_URL','')},
 hub_key,genesis_key,os.environ.get('PUBLISHER_PIN'))
if public_activation:
 print(json.dumps(verify_public_assets(data,hub_envelope,genesis_envelope,hub_key,genesis_key),indent=2))
 # Revalidate catalog and complete signed bundle after downloads, before upload.
 validate_candidate(envelope,catalog_key,kind,json.loads(Path('catalog/source-lock.json').read_text()),
  hub_envelope,genesis_envelope,{'hub':os.environ.get('HUB_URL',''),'genesis':os.environ.get('GENESIS_URL','')},
  hub_key,genesis_key,os.environ.get('PUBLISHER_PIN'))
