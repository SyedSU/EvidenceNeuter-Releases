"""Truthful unsigned RC evidence; no private keys or release mutation."""
import json,subprocess
from pathlib import Path
lock=json.loads(Path('catalog/source-lock.json').read_text())
print(json.dumps({'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'catalogAuthenticated':False,'publicDownloads':False,'releaseArtifactsProduced':False,'sourceLockComplete':all(e.get('sourceCommit') for e in lock.values()),'blockers':['Production RSA trust and signer absent','Authenticode publisher trust absent','Signed package manifests and public releases absent','Genuine Windows acceptance absent'],'scope':'Contract review evidence only; no installer/model/gameplay acceptance claim'},indent=2))
