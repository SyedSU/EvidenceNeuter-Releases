import datetime
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from tools.distribution import ROOT,sign
from tools.review_candidate import review


class ReviewedSequenceTests(unittest.TestCase):
 def setUp(self):
  temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
  self.root=Path(temporary.name);(self.root/'catalog').mkdir()
  (self.root/'catalog/source-lock.json').write_bytes((ROOT/'catalog/source-lock.json').read_bytes())
  def git(*args):return subprocess.check_output(['git','-C',str(self.root),*args],text=True).strip()
  git('init','-q');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid')
  git('add','.');git('commit','-qm','fixture')
  key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
  self.catalog=json.loads((ROOT/'catalog/development.json').read_text())
  self.catalog.update(sequence=2,expires=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=2)).isoformat())
  (self.root/'catalog.json').write_text(json.dumps(sign(self.catalog,key)))
  self.environment={'COMMIT':git('rev-parse','HEAD'),'TAG':'review-2','KIND':'catalog','FILE':'catalog.json',
    'PUBLIC_KEY':key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo).decode(),
    'CATALOG_SEQUENCE_FLOOR':'1','HUB_SEQUENCE_FLOOR':'0','GENESIS_SEQUENCE_FLOOR':'0'}
  old=Path.cwd();os.chdir(self.root);self.addCleanup(os.chdir,old)
 def test_new_signed_metadata_above_reviewed_floor_is_verified_without_approval(self):
  result=review(self.environment)
  self.assertEqual(result['sequence'],2);self.assertFalse(result['publicDownloads'])
 def test_equal_or_lower_signed_sequence_is_not_a_new_publication(self):
  for floor in ('2','3'):
   with self.subTest(floor=floor):
    self.environment['CATALOG_SEQUENCE_FLOOR']=floor
    with self.assertRaises(ValueError):review(self.environment)
 def test_missing_or_malformed_floor_fails_closed(self):
  for floor in ('','-1','false','1.5','01'):
   with self.subTest(floor=floor):
    self.environment['CATALOG_SEQUENCE_FLOOR']=floor
    with self.assertRaises(ValueError):review(self.environment)
 def test_hub_publication_uses_independent_hub_role_key(self):
  lock=json.loads((self.root/'catalog/source-lock.json').read_text())
  key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
  payload={'schema':1,'product':'hub','channel':'stable','platform':'windows-x64','version':lock['hub']['version'],
    'sequence':2,'expires':self.catalog['expires'],'sourceCommit':lock['hub']['sourceCommit'],
    'minimumHubVersion':'0.2.0','minimumWindowsBuild':19041,'installer':{
      'url':'https://github.com/SyedSU/EvidenceNeuter-Releases/releases/download/hub-review-2/setup.exe',
      'size':100,'sha256':'a'*64,'publisherThumbprint':'A'*64}}
  (self.root/'hub.json').write_text(json.dumps(sign(payload,key)))
  self.environment.update(KIND='hub',FILE='hub.json',HUB_SEQUENCE_FLOOR='1',
    HUB_PUBLIC_KEY=key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo).decode())
  self.assertEqual(review(self.environment)['product'],'hub')
  del self.environment['HUB_PUBLIC_KEY']
  with self.assertRaisesRegex(ValueError,'HUB_PUBLIC_KEY'):review(self.environment)
