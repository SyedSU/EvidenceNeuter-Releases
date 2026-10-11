"""Read-only production bundle proof; successful proof is never publish authorization."""
import argparse,json
from pathlib import Path
from cryptography.hazmat.primitives import serialization
try:
 from .distribution import validate_candidate
 from .public_assets import verify_public_assets
except ImportError:
 from distribution import validate_candidate
 from public_assets import verify_public_assets

def verify_bundle(catalog,hub,genesis,catalog_key,hub_key,genesis_key,lock,publisher_pin,hub_url,genesis_url):
 args=(catalog,catalog_key,'catalog',lock,hub,genesis,{'hub':hub_url,'genesis':genesis_url},hub_key,genesis_key,publisher_pin)
 data=validate_candidate(*args)
 if not data['publicDownloads']:raise ValueError('Production proof requires authenticated public activation candidate')
 public=verify_public_assets(data,hub,genesis,hub_key,genesis_key)
 validate_candidate(*args)
 return {'schema':1,'authenticated':True,'anonymousPublicAssetsVerified':True,'publicationAuthorized':False,'catalogSequence':data['sequence'],'catalogExpires':data['expires'],'sourceLock':lock,'publicEvidence':public}

if __name__=='__main__':
 parser=argparse.ArgumentParser()
 for name in ('catalog','hub','genesis','catalog-key','hub-key','genesis-key','source-lock','publisher-pin','hub-url','genesis-url'):parser.add_argument('--'+name,required=True)
 args=parser.parse_args()
 def read(name):return json.loads(Path(getattr(args,name)).read_text())
 def key(name):return serialization.load_pem_public_key(Path(getattr(args,name)).read_bytes())
 print(json.dumps(verify_bundle(read('catalog'),read('hub'),read('genesis'),key('catalog_key'),key('hub_key'),key('genesis_key'),read('source_lock'),args.publisher_pin,args.hub_url,args.genesis_url),indent=2))
