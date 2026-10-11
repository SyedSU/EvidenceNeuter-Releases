import copy,json,tempfile,unittest,zipfile,subprocess
from pathlib import Path
from tools.prepare_release import prepare,inspect_package,integration_mapping,ROOT
class PreparationTests(unittest.TestCase):
 def setUp(self):self.config=json.loads((ROOT/'release/preparation.json').read_text())
 def test_missing_inputs_produce_blocked_record_without_fabricated_assets(self):
  result=prepare(self.config)
  self.assertFalse(result['publicationAuthorized']);self.assertFalse(result['publicDownloads']);self.assertEqual(result['unsignedProposals'],{});self.assertGreater(len(result['blockers']),5)
 def test_source_lock_mismatch_rejected(self):
  self.config['hub']['reviewedBuildCommit']='a'*40
  with self.assertRaises(ValueError):prepare(self.config)
 def test_package_hashes_actual_file_bytes(self):
  import hashlib
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'package.zip'
   with zipfile.ZipFile(path,'w') as archive:archive.writestr('EvidenceGenesis.exe',b'real supplied fixture bytes')
   result=inspect_package(path)
   self.assertEqual(result['sha256'],hashlib.sha256(path.read_bytes()).hexdigest());self.assertEqual(result['files'][0]['sha256'],hashlib.sha256(b'real supplied fixture bytes').hexdigest())
 def test_package_traversal_and_duplicate_rejected(self):
  for names in [('../unsafe',),('FILE','file')]:
   with tempfile.TemporaryDirectory() as directory:
    path=Path(directory)/'package.zip'
    with zipfile.ZipFile(path,'w') as archive:
     for name in names:archive.writestr(name,b'fixture')
    with self.assertRaises(ValueError):inspect_package(path)
 def test_merge_tree_mapping_requires_explicit_equivalence(self):
  with tempfile.TemporaryDirectory() as directory:
   def git(*args):return subprocess.check_output(['git','-C',directory,*args],text=True).strip()
   git('init','-q');git('config','user.email','test@example.invalid');git('config','user.name','Fixture')
   path=Path(directory)/'source';path.write_text('first');git('add','.');git('commit','-qm','first');first=git('rev-parse','HEAD')
   git('commit','--allow-empty','-qm','same tree');same=git('rev-parse','HEAD');self.assertTrue(integration_mapping(directory,first,same)['reuseRequiresProtectedHumanReview'])
   path.write_text('changed');git('add','.');git('commit','-qm','changed')
   with self.assertRaises(ValueError):integration_mapping(directory,first,git('rev-parse','HEAD'))
 def test_user_report_cannot_authorize_publication(self):
  self.config['productionTrustConfigured']=True;self.config['userReportedLaptopAcceptance']['independentlyVerified']=True
  result=prepare(self.config);self.assertFalse(result['authenticated']);self.assertFalse(result['publicationAuthorized'])

 def test_full_unsigned_proposal_uses_real_packages_but_never_approves(self):
  import datetime
  with tempfile.TemporaryDirectory() as directory:
   base='https://github.com/SyedSU/EvidenceNeuter-Releases/releases/download/rc-0.4/'
   self.config['metadata']={'sequence':1,'expires':(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=2)).isoformat(),'hubManifestUrl':base+'hub.json','genesisManifestUrl':base+'genesis.json'}
   installer=Path(directory)/'hub.exe';installer.write_bytes(b'synthetic unsigned fixture')
   self.config['hub'].update(installerPath=str(installer),installerUrl=base+'hub.exe',publisherThumbprint='A'*64)
   for kind,name in [('game','EvidenceGenesis.exe'),('runtime','llama-server.exe'),('model','genesis.gguf')]:
    path=Path(directory)/(kind+'.zip')
    with zipfile.ZipFile(path,'w') as archive:archive.writestr(name,b'fixture')
    self.config['genesis']['packages'][kind]={'path':str(path),'url':base+kind+'.zip'}
   result=prepare(self.config)
   self.assertEqual(len(result['unsignedProposals']['genesis']['packages']),3)
   self.assertFalse(result['unsignedProposals']['catalog']['publicDownloads']);self.assertFalse(result['publicationAuthorized'])
   evidence=Path(directory)/'acceptance.json';evidence.write_text(json.dumps({'synthetic':True}))
   self.config['acceptanceEvidencePath']=str(evidence)
   with self.assertRaisesRegex(ValueError,'Synthetic'):prepare(self.config)

class EnvironmentTests(unittest.TestCase):
 def test_missing_environment_or_reviewers_fail_closed(self):
  from tools.environment_preflight import validate_environment
  for environment in [{},{'name':'distribution-release','protection_rules':[]}]:
   with self.assertRaises(ValueError):validate_environment(environment,{})
 def test_only_strict_main_review_policy_accepted(self):
  from tools.environment_preflight import validate_environment
  environment={'name':'distribution-release','can_admins_bypass':False,'protection_rules':[{'type':'required_reviewers','prevent_self_review':True,'reviewers':[{'type':'User','reviewer':{'id':1}}]}],'deployment_branch_policy':{'custom_branch_policies':True,'protected_branches':False}}
  policies={'branch_policies':[{'name':'main','type':'branch'}]}
  self.assertTrue(validate_environment(environment,policies)['protected'])
  for field,value in [('can_admins_bypass',True),('deployment_branch_policy',None)]:
   bad=copy.deepcopy(environment);bad[field]=value
   with self.assertRaises(ValueError):validate_environment(bad,policies)
  with self.assertRaises(ValueError):validate_environment(environment,{'branch_policies':[{'name':'*','type':'branch'}]})

class BundleProofTests(unittest.TestCase):
 def test_bundle_requires_replay_floors_and_no_approval(self):
  from unittest.mock import patch
  from tools.verify_bundle import verify_bundle
  data={'publicDownloads':True,'sequence':3,'expires':'future'}
  with patch('tools.verify_bundle.verify') as verify,patch('tools.verify_bundle.validate_candidate',return_value=data) as validate,patch('tools.verify_bundle.verify_public_assets',return_value={'manifests':[],'assets':[]}) as public:
   result=verify_bundle({}, {}, {},None,None,None,{},'pin','huburl','genesisurl',3,4,5)
   self.assertFalse(result['publicationAuthorized']);self.assertEqual(validate.call_count,2);self.assertEqual(public.call_count,1)
   self.assertEqual([call.args[-1] for call in verify.call_args_list],[3,4,5,3,4,5])
   with self.assertRaises(ValueError):verify_bundle({}, {}, {},None,None,None,{},'pin','huburl','genesisurl',-1)
 def test_development_bundle_cannot_supply_production_proof(self):
  from unittest.mock import patch
  from tools.verify_bundle import verify_bundle
  with patch('tools.verify_bundle.verify'),patch('tools.verify_bundle.validate_candidate',return_value={'publicDownloads':False}),patch('tools.verify_bundle.verify_public_assets') as public:
   with self.assertRaises(ValueError):verify_bundle({}, {}, {},None,None,None,{},'pin','huburl','genesisurl')
   public.assert_not_called()
