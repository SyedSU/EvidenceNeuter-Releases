"""Anonymous TLS-only verification of already-reviewed public activation assets."""
import hashlib,json,ssl,time
from dataclasses import dataclass
from urllib.parse import urlsplit,urljoin
from urllib.request import build_opener,HTTPSHandler,HTTPRedirectHandler,Request
from urllib.error import HTTPError
try:
 from .distribution import release_url,verify
except ImportError:
 from distribution import release_url,verify

@dataclass
class AssetResponse:
 status:int
 headers:object
 body:object

class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None

def anonymous_transport(url):
 # No cookies, credentials, netrc, GitHub CLI or authorization headers.
 opener=build_opener(HTTPSHandler(context=ssl.create_default_context()),NoRedirect())
 request=Request(url,headers={'User-Agent':'EvidenceNeuter-activation-verifier','Accept-Encoding':'identity'})
 try:response=opener.open(request,timeout=30)
 except HTTPError as error:response=error
 return AssetResponse(response.code,response.headers,response)

def approved(url):
 u=urlsplit(url)
 if u.scheme!='https' or u.username or u.password or u.port not in (None,443) or u.fragment or u.hostname not in ('github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'):raise ValueError('Unapproved anonymous asset redirect')
 if u.hostname=='github.com':release_url(url,metadata_locator=True)

def read_asset(url,transport,limit,expected_size=None,expected_hash=None):
 release_url(url,metadata_locator=True);deadline=time.monotonic()+7200
 for attempt in range(6):
  approved(url);response=transport(url)
  if response.status in (301,302,303,307,308):
   try:
    location=response.headers.get('Location')
    if not location:raise ValueError('Missing asset redirect location')
    url=urljoin(url,location);approved(url)
   finally:response.body.close()
   continue
  try:
   if response.status!=200:raise ValueError('Public asset missing or unavailable')
   length=response.headers.get('Content-Length')
   if length is not None and (not str(length).isdigit() or int(length)>limit or expected_size is not None and int(length)!=expected_size):raise ValueError('Public asset length mismatch')
   if response.headers.get('Content-Encoding','identity').lower()!='identity':raise ValueError('Encoded public asset response')
   digest=hashlib.sha256();count=0;chunks=[]
   while True:
    if time.monotonic()>deadline:raise ValueError('Public asset verification deadline exceeded')
    chunk=response.body.read(65536)
    if not chunk:break
    count+=len(chunk)
    if count>limit:raise ValueError('Public asset exceeds signed bound')
    digest.update(chunk)
    if expected_hash is None:chunks.append(chunk)
   if length is not None and count!=int(length) or expected_size is not None and count!=expected_size or expected_hash is not None and digest.hexdigest()!=expected_hash:raise ValueError('Public asset byte integrity mismatch')
   return b''.join(chunks) if expected_hash is None else {'size':count,'sha256':digest.hexdigest()}
  finally:response.body.close()
 raise ValueError('Too many anonymous asset redirects')

def verify_public_assets(catalog,hub_envelope,genesis_envelope,hub_key,genesis_key,transport=anonymous_transport):
 """Call only after validate_candidate; downloaded envelopes retain exact signed bytes."""
 result={'manifests':[],'assets':[]}
 if not catalog['publicDownloads']:return result
 if hub_key is None or genesis_key is None:raise ValueError('Explicit release trust keys required')
 for entry,envelope,key,kind in [(catalog['infrastructure'],hub_envelope,hub_key,'hub'),(catalog['products'][0],genesis_envelope,genesis_key,'manifest')]:
  manifest=verify(envelope,key,kind);locator=entry['release']['manifestUrl']
  remote=json.loads(read_asset(locator,transport,2*1024*1024))
  verify(remote,key,kind)
  if remote!=envelope:raise ValueError('Published signed envelope differs from reviewed bundle')
  result['manifests'].append(locator)
  assets=[manifest['installer']] if kind=='hub' else manifest['packages']
  for asset in assets:
   evidence=read_asset(asset['url'],transport,asset['size'],asset['size'],asset['sha256'])
   result['assets'].append(dict(url=asset['url'],**evidence))
 return result
