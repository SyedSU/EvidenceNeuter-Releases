"""Cross-check actual optional consumer checkouts; never writes to them."""
import argparse,json,re
from pathlib import Path
from distribution import ROOT,validate_catalog

def check_consumers(website=None,hub=None,genesis=None):
 canonical=json.loads((ROOT/'catalog/development.json').read_text());validate_catalog(canonical)
 schema=json.loads((ROOT/'schemas/catalog.schema.json').read_text());checked=[]
 for name,path,catalog_path,schema_path in [('website',website,'catalog.json','schemas/catalog.schema.json'),('hub',hub,'src/Catalog/development.json','src/Catalog/catalog.schema.json')]:
  if path is None:continue
  base=Path(path)
  if json.loads((base/catalog_path).read_text())!=canonical:raise ValueError(name+' catalog differs from canonical')
  if json.loads((base/schema_path).read_text())!=schema:raise ValueError(name+' schema differs from canonical')
  checked.append(name+':catalog/schema')
 if hub:
  text=(Path(hub)/'src/Updates/Metadata.cs').read_text()
  if not re.search(r'HubVersion\s*=\s*"0\.3\.0"',text):raise ValueError('Hub build version must be0.3.0')
  checked.append('hub:version0.3.0')
 if genesis:
  text=(Path(genesis)/'scripts/build_native.py').read_text()
  if not re.search(r"['\"]version['\"]\s*:\s*['\"]0\.4\.0['\"]",text) or not re.search(r"['\"]saveSchema['\"]\s*:\s*4\b",text):raise ValueError('Genesis builder requires0.4.0/saveSchema4')
  text=(Path(genesis)/'native/scripts/state.gd').read_text()
  if not re.search(r'"version"\s*:\s*4\b',text):raise ValueError('Genesis profile format must match confirmed schema4')
  checked.append('genesis:version0.4.0/saveSchema4')
 manifest=ROOT/'catalog/genesis-candidate.json'
 if manifest.exists():
  from distribution import validate_manifest
  data=json.loads(manifest.read_text());validate_manifest(data)
  if data['saveSchema']!=4 or data['minimumHubVersion']!='0.3.0':raise ValueError('Candidate profile compatibility mismatch')
  checked.append('genesis:minimumHub0.3.0')
 return {'checked':checked,'publicDownloads':canonical['publicDownloads'],'signedCandidatePresent':manifest.exists()}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--website',type=Path);parser.add_argument('--hub',type=Path);parser.add_argument('--genesis',type=Path);args=parser.parse_args()
 print(json.dumps(check_consumers(args.website,args.hub,args.genesis),indent=2))
