"""Read-only workflow verification before protected publication."""
import json,os,re,subprocess
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from distribution import verify
commit=os.environ['COMMIT'];tag=os.environ['TAG'];path=Path(os.environ['FILE'])
if not re.fullmatch('[a-f0-9]{40}',commit) or subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()!=commit:raise SystemExit('Reviewed source commit mismatch')
if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,100}',tag) or path.is_absolute() or '..' in path.parts or not path.is_file() or path.suffix!='.json':raise SystemExit('Invalid reviewed metadata path/tag')
key=os.environ.get('PUBLIC_KEY','')
if not key:raise SystemExit('Production trust prerequisite absent')
verify(json.loads(path.read_text()),serialization.load_pem_public_key(key.encode()),os.environ['KIND'])
