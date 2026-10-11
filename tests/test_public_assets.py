import copy,hashlib,io,json,unittest
from cryptography.hazmat.primitives.asymmetric import rsa
from tools.distribution import sign
from tools.public_assets import AssetResponse,verify_public_assets

BASE='https://github.com/SyedSU/EvidenceNeuter-Releases/releases/download/test/'
class PublicAssetTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.private=rsa.generate_private_key(public_exponent=65537,key_size=3072)
 def setUp(self):
  self.key=self.private.public_key();self.requests=[];self.remote={}
  installer=b'unsigned synthetic installer fixture'
  self.hub={'schema':1,'product':'hub','channel':'stable','platform':'windows-x64','version':'0.3.0','sequence':1,'expires':'2026-11-08T00:00:00Z','minimumHubVersion':'0.2.0','minimumWindowsBuild':19041,'sourceCommit':'a'*40,'installer':{'url':BASE+'hub.exe','size':len(installer),'sha256':hashlib.sha256(installer).hexdigest(),'publisherThumbprint':'A'*64}}
  self.genesis={'schema':1,'product':'genesis','channel':'stable','platform':'windows-x64','version':'0.4.0','sequence':1,'expires':'2026-11-08T00:00:00Z','minimumHubVersion':'0.3.0','saveSchema':4,'sourceCommit':'b'*40,'packages':[]}
  self.add(BASE+'hub.exe',installer)
  for kind,path in [('game','EvidenceGenesis.exe'),('runtime','llama-server.exe'),('model','genesis.gguf')]:
   body=(kind+' synthetic archive fixture').encode();url=BASE+kind+'.zip';self.add(url,body)
   self.genesis['packages'].append({'kind':kind,'url':url,'size':len(body),'sha256':hashlib.sha256(body).hexdigest(),'files':[{'path':path,'size':1,'sha256':'a'*64}]})
  self.hub_envelope=sign(self.hub,self.private);self.genesis_envelope=sign(self.genesis,self.private)
  self.add(BASE+'hub.json',json.dumps(self.hub_envelope).encode());self.add(BASE+'genesis.json',json.dumps(self.genesis_envelope).encode())
  self.catalog={'publicDownloads':True,'infrastructure':{'release':{'manifestUrl':BASE+'hub.json'}},'products':[{'release':{'manifestUrl':BASE+'genesis.json'}}]}
 def add(self,url,body,status=200,headers=None):self.remote[url]=(status,headers or {'Content-Length':str(len(body))},body)
 def transport(self,url):
  self.requests.append(url);status,headers,body=self.remote.get(url,(404,{},b''));return AssetResponse(status,headers,io.BytesIO(body))
 def verify(self):return verify_public_assets(self.catalog,self.hub_envelope,self.genesis_envelope,self.key,self.key,transport=self.transport)
 def test_complete_public_bundle_bytes_and_envelopes(self):
  result=self.verify();self.assertEqual(len(result['assets']),4);self.assertEqual(len(result['manifests']),2);self.assertEqual(len(self.requests),6)
 def test_missing_public_package_rejects(self):
  del self.remote[BASE+'model.zip']
  with self.assertRaises(ValueError):self.verify()
 def test_truncated_and_tampered_package_rejects(self):
  original=self.remote[BASE+'runtime.zip'][2]
  for body in [original[:-1],b'X'+original[1:]]:
   self.add(BASE+'runtime.zip',body)
   with self.assertRaises(ValueError):self.verify()
 def test_truncation_without_content_length_rejects(self):
  status,headers,body=self.remote[BASE+'model.zip'];self.remote[BASE+'model.zip']=(status,{},body[:-1])
  with self.assertRaises(ValueError):self.verify()
 def test_unapproved_or_insecure_redirect_rejected_before_request(self):
  for target in ['http://release-assets.githubusercontent.com/file','https://evil.example/file','https://user:pass@release-assets.githubusercontent.com/file','https://release-assets.githubusercontent.com:8443/file','https://github.com/login']:
   self.requests=[];self.add(BASE+'hub.exe',b'',302,{'Location':target})
   with self.assertRaises(ValueError):self.verify()
   self.assertNotIn(target,self.requests)
 def test_approved_cdn_redirect_preserves_signed_integrity(self):
  body=self.remote[BASE+'hub.exe'][2];target='https://release-assets.githubusercontent.com/fixture?temporary=fixture'
  self.add(target,body);self.add(BASE+'hub.exe',b'',302,{'Location':target});self.verify();self.assertIn(target,self.requests)
 def test_different_valid_signed_remote_manifest_rejects(self):
  changed=copy.deepcopy(self.hub);changed['sequence']=2;self.add(BASE+'hub.json',json.dumps(sign(changed,self.private)).encode())
  with self.assertRaises(ValueError):self.verify()
 def test_remote_signature_tamper_rejects(self):
  changed=dict(self.genesis_envelope,signature='AAAA');self.add(BASE+'genesis.json',json.dumps(changed).encode())
  with self.assertRaises(ValueError):self.verify()
 def test_unsigned_development_never_requests_assets(self):
  self.catalog['publicDownloads']=False;self.assertEqual(self.verify(),{'manifests':[],'assets':[]});self.assertEqual(self.requests,[])

 def test_redirect_loop_is_bounded(self):
  self.add(BASE+'hub.exe',b'',302,{'Location':BASE+'hub.exe'})
  with self.assertRaises(ValueError):self.verify()
  self.assertEqual(self.requests.count(BASE+'hub.exe'),6)
 def test_oversized_metadata_rejected_before_read(self):
  self.remote[BASE+'hub.json']=(200,{'Content-Length':str(2*1024*1024+1)},b'{}')
  with self.assertRaises(ValueError):self.verify()
 def test_encoded_asset_response_rejected(self):
  body=self.remote[BASE+'hub.exe'][2]
  self.add(BASE+'hub.exe',body,headers={'Content-Encoding':'gzip'})
  with self.assertRaises(ValueError):self.verify()
 def test_default_transport_has_no_credentials(self):
  from unittest.mock import patch
  from tools.public_assets import anonymous_transport
  response=io.BytesIO(b'fixture');response.code=200;response.headers={}
  class Opener:
   def open(inner,request,timeout):
    self.assertNotIn('Authorization',request.headers);self.assertNotIn('Cookie',request.headers)
    self.assertEqual(request.headers['Accept-encoding'],'identity');self.assertEqual(timeout,30)
    return response
  with patch('tools.public_assets.build_opener',return_value=Opener()):
   anonymous_transport(BASE+'hub.json').body.close()
