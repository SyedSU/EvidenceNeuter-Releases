import copy,json,tempfile,unittest
from pathlib import Path
from tools.distribution import validate_catalog,sign,verify,package,check_lock
from cryptography.hazmat.primitives.asymmetric import rsa
class DistributionTests(unittest.TestCase):
 def setUp(self): self.catalog=json.loads(Path('catalog/development.json').read_text())
 def test_development(self): validate_catalog(self.catalog)
 def test_unsigned_downloads_blocked(self):
  self.catalog['publicDownloads']=True
  with self.assertRaises(ValueError):validate_catalog(self.catalog)
 def test_unknown_field(self):
  self.catalog['secret']='x'
  with self.assertRaises(ValueError):validate_catalog(self.catalog)
 def test_expiry_and_replay(self):
  self.catalog['expires']='2000-01-01T00:00:00Z'
  with self.assertRaises(ValueError):validate_catalog(self.catalog)
  self.setUp()
  with self.assertRaises(ValueError):validate_catalog(self.catalog,minimum_sequence=2)
 def test_sign_tamper(self):
  key=rsa.generate_private_key(public_exponent=65537,key_size=3072);e=sign(self.catalog,key)
  self.assertEqual(verify(e,key.public_key()),self.catalog)
  e['payload']=e['payload'][:-4]+'AAAA'
  with self.assertRaises(ValueError):verify(e,key.public_key())
 def test_package_deterministic(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'in').mkdir();(p/'in/a.txt').write_text('abc')
   a=package(p/'in',p/'a.zip');b=package(p/'in',p/'b.zip');self.assertEqual(a,b)
   (p/'in/link').symlink_to(p/'in/a.txt')
   with self.assertRaises(ValueError):package(p/'in',p/'c.zip')
 def test_version_lock(self):
  lock={'hub':{'version':'0.3.0','sourceCommit':'a'*40},'genesis':{'version':'0.4.0','sourceCommit':'b'*40,'saveSchema':4}}
  check_lock(lock,'genesis','0.4.0','b'*40,4)
  with self.assertRaises(ValueError):check_lock(lock,'genesis','0.4.0','a'*40,4)
  with self.assertRaises(ValueError):check_lock(lock,'genesis','0.4.0','b'*40,3)
 def test_authenticated_public_gate_complete(self):
  c=self.catalog;c['publicDownloads']=True;c['releaseGate'].update(status='approved',reasons=[])
  for k in ['trustConfigured','signedArtifactsPublished','windowsAcceptancePassed','licensesApproved','authenticodeVerified']:c['releaseGate'][k]=True
  for e in [c['infrastructure'],c['products'][0]]:
   e.update(availability='available',sourceCommit='a'*40,licenseNotices=[{'name':'Test notice','url':'https://github.com/SyedSU/EvidenceNeuter-Releases/releases/download/test/LICENSE.txt'}])
   e['release']={'manifestUrl':'https://github.com/SyedSU/EvidenceNeuter-Releases/releases/download/test/manifest.json','version':e['version'],'sourceCommit':e['sourceCommit'],'platform':'windows-x64','download':{'url':'https://github.com/SyedSU/EvidenceNeuter-Releases/releases/download/test/hub.exe','size':12,'sha256':'a'*64} if e['id']=='hub' else None}
  c['products'][0]['components']={k:{'version':'1.0.0','sourceCommit':'b'*40,'licenseNotices':[{'name':'Notice','url':'https://github.com/SyedSU/EvidenceNeuter-Releases/releases/download/test/LICENSE.txt'}]} for k in ['runtime','model']}
  validate_catalog(c,authenticated=True)
  extra=c['products'][1];extra.update(availability='available',version='1.0.0',sourceCommit='a'*40,release=dict(c['products'][0]['release'],version='1.0.0'))
  with self.assertRaises(ValueError):validate_catalog(c,authenticated=True)
  extra.update(availability='planned',version=None,sourceCommit=None,release=None)
  with self.assertRaises(ValueError):validate_catalog(c)
  c['infrastructure']['release']['download']=None
  with self.assertRaises(ValueError):validate_catalog(c,authenticated=True)
 def test_manifest_compatible_and_overlap_rejected(self):
  from tools.distribution import validate_manifest
  m={'schema':1,'product':'genesis','channel':'stable','platform':'windows-x64','version':'0.4.0','sequence':1,'expires':self.catalog['expires'],'minimumHubVersion':'0.3.0','saveSchema':4,'sourceCommit':'a'*40,'packages':[]}
  for kind,path in [('game','EvidenceGenesis.exe'),('runtime','llama-server.exe'),('model','genesis.gguf')]:m['packages'].append({'kind':kind,'url':'https://github.com/SyedSU/EvidenceNeuter-Releases/releases/download/test/'+kind+'.zip','size':1,'sha256':'a'*64,'files':[{'path':path,'size':1,'sha256':'b'*64}]})
  validate_manifest(m)
  m['packages'][0]['files'].append({'path':'brain/llama-server.exe','size':1,'sha256':'b'*64})
  with self.assertRaises(ValueError):validate_manifest(m)
 def test_hub_manifest_publisher_and_url(self):
  from tools.distribution import validate_hub
  m={'schema':1,'product':'hub','channel':'stable','platform':'windows-x64','version':'0.3.0','sequence':1,'expires':self.catalog['expires'],'minimumHubVersion':'0.2.0','minimumWindowsBuild':19041,'sourceCommit':'a'*40,'installer':{'url':'https://github.com/SyedSU/EvidenceNeuter-Releases/releases/download/test/hub.exe','size':10,'sha256':'a'*64,'publisherThumbprint':'A'*64}}
  validate_hub(m);m['installer']['url']='https://evil.example/hub.exe'
  with self.assertRaises(ValueError):validate_hub(m)
 def test_screenshot_traversal(self):
  self.catalog['infrastructure']['screenshots']=[{'url':'/../private','alt':'Test'}]
  with self.assertRaises(ValueError):validate_catalog(self.catalog)

 def test_schema4_requires_hub03(self):
  from tools.distribution import validate_manifest
  m={'schema':1,'product':'genesis','channel':'stable','platform':'windows-x64','version':'0.4.0','sequence':1,'expires':self.catalog['expires'],'minimumHubVersion':'0.2.0','saveSchema':4,'sourceCommit':'a'*40,'packages':[]}
  for kind,path in [('game','EvidenceGenesis.exe'),('runtime','llama-server.exe'),('model','genesis.gguf')]:m['packages'].append({'kind':kind,'url':'https://github.com/SyedSU/EvidenceNeuter-Releases/releases/download/test/'+kind+'.zip','size':1,'sha256':'a'*64,'files':[{'path':path,'size':1,'sha256':'b'*64}]})
  with self.assertRaises(ValueError):validate_manifest(m)
 def test_screenshot_encoded_and_backslash_paths_rejected(self):
  for url in ['/assets/%2e%2e/private.png','/\\evil.example/image.png','/assets/image.png?redirect=evil','//evil.example/image.png']:
   with self.subTest(url=url):
    self.setUp();self.catalog['infrastructure']['screenshots']=[{'url':url,'alt':'Test'}]
    with self.assertRaises(ValueError):validate_catalog(self.catalog)
 def test_asset_url_dot_segments_rejected(self):
  from tools.distribution import release_url
  for suffix in ['test/../hub.exe','test/%2e%2e','%2e%2e/hub.exe','test/a%2f..%2fhub.exe']:
   with self.subTest(suffix=suffix):
    with self.assertRaises(ValueError):release_url('https://github.com/SyedSU/EvidenceNeuter-Releases/releases/download/'+suffix)
 def test_mounted_ancestor_conflict_rejected(self):
  from tools.distribution import validate_manifest
  m={'schema':1,'product':'genesis','channel':'stable','platform':'windows-x64','version':'0.4.0','sequence':1,'expires':self.catalog['expires'],'minimumHubVersion':'0.3.0','saveSchema':4,'sourceCommit':'a'*40,'packages':[]}
  for kind,path in [('game','EvidenceGenesis.exe'),('runtime','llama-server.exe'),('model','genesis.gguf')]:m['packages'].append({'kind':kind,'url':'https://github.com/SyedSU/EvidenceNeuter-Releases/releases/download/test/'+kind+'.zip','size':1,'sha256':'a'*64,'files':[{'path':path,'size':1,'sha256':'b'*64}]})
  m['packages'][1]['files'] += [{'path':'shared','size':1,'sha256':'b'*64},{'path':'shared/file.dll','size':1,'sha256':'b'*64}]
  with self.assertRaises(ValueError):validate_manifest(m)
 def test_review_candidate_requires_complete_source_lock(self):
  from tools.distribution import validate_candidate
  key=rsa.generate_private_key(public_exponent=65537,key_size=3072);envelope=sign(self.catalog,key)
  pending={'hub':{'version':'0.3.0','sourceCommit':None},'genesis':{'version':'0.4.0','sourceCommit':None,'saveSchema':4}}
  with self.assertRaises(ValueError):validate_candidate(envelope,key.public_key(),'catalog',pending)

 def test_review_hub_candidate_matches_locked_source(self):
  from tools.distribution import validate_candidate
  key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
  lock={'hub':{'version':'0.3.0','sourceCommit':'a'*40},'genesis':{'version':'0.4.0','sourceCommit':'b'*40,'saveSchema':4}}
  m={'schema':1,'product':'hub','channel':'stable','platform':'windows-x64','version':'0.3.0','sequence':1,'expires':self.catalog['expires'],'minimumHubVersion':'0.2.0','minimumWindowsBuild':19041,'sourceCommit':'a'*40,'installer':{'url':'https://github.com/SyedSU/EvidenceNeuter-Releases/releases/download/test/hub.exe','size':10,'sha256':'a'*64,'publisherThumbprint':'A'*64}}
  validate_candidate(sign(m,key),key.public_key(),'hub',lock)
  for field,value in [('sourceCommit','c'*40),('version','0.3.1')]:
   candidate=dict(m);candidate[field]=value
   with self.assertRaises(ValueError):validate_candidate(sign(candidate,key),key.public_key(),'hub',lock)
 def test_consumer_checker_detects_schema_drift(self):
  import subprocess,sys
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'schemas').mkdir();(root/'catalog.json').write_text(json.dumps(self.catalog));schema=json.loads(Path('schemas/catalog.schema.json').read_text());(root/'schemas/catalog.schema.json').write_text(json.dumps(schema))
   command=[sys.executable,'tools/check_consumers.py','--website',str(root)]
   self.assertEqual(subprocess.run(command,capture_output=True).returncode,0)
   schema['properties']['schema']['const']=2;(root/'schemas/catalog.schema.json').write_text(json.dumps(schema))
   result=subprocess.run(command,capture_output=True,text=True);self.assertNotEqual(result.returncode,0);self.assertIn('schema differs from canonical',result.stderr)
 def test_mutable_release_and_executable_notice_urls_rejected(self):
  from tools.distribution import release_url
  for tag in ['latest','stable','genesis-stable','hub-stable']:
   with self.subTest(tag=tag):
    with self.assertRaises(ValueError):release_url('https://github.com/SyedSU/EvidenceNeuter-Releases/releases/download/'+tag+'/a.zip')
  self.catalog['products'][0]['licenseNotices']=[{'name':'Unsafe','url':'javascript:alert(1)'}]
  with self.assertRaises(ValueError):validate_catalog(self.catalog)

 def test_metadata_locator_is_separate_from_immutable_download(self):
  from tools.distribution import release_url
  value='https://github.com/SyedSU/EvidenceNeuter-Releases/releases/download/hub-stable/hub-stable.json'
  release_url(value,metadata_locator=True)
  with self.assertRaises(ValueError):release_url(value)
 def test_local_screenshot_and_notice_are_valid(self):
  self.catalog['products'][0]['licenseNotices']=[{'name':'License','url':'/assets/license.txt'}]
  self.catalog['products'][0]['screenshots']=[{'alt':'Preview','url':'/assets/preview.png'}]
  validate_catalog(self.catalog)
