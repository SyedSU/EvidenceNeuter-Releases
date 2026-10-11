"""Prepare unsigned release proposals from actual supplied bytes. Never approve gates."""
import argparse,datetime,hashlib,json,re,stat,subprocess,zipfile
from pathlib import Path
try:
 from .distribution import ROOT,release_url,safe_path,validate_manifest,validate_hub,validate_catalog
except ImportError:
 from distribution import ROOT,release_url,safe_path,validate_manifest,validate_hub,validate_catalog

def digest_file(path):
 h=hashlib.sha256();size=0
 with Path(path).open('rb') as source:
  for chunk in iter(lambda:source.read(1024*1024),b''):size+=len(chunk);h.update(chunk)
 if not size:raise ValueError('Empty artifact')
 return {'size':size,'sha256':h.hexdigest()}

def inspect_package(path):
 result=digest_file(path);files=[];seen=set();total=0
 with zipfile.ZipFile(path) as archive:
  for item in archive.infolist():
   if item.is_dir():raise ValueError('Explicit ZIP directories are unsupported by Hub')
   safe_path(item.filename)
   if item.flag_bits&1 or item.external_attr&0x400 or stat.S_ISLNK(item.external_attr>>16) or item.filename.lower() in seen:raise ValueError('Unsafe ZIP entry')
   seen.add(item.filename.lower());total+=item.file_size
   if total>8589934592:raise ValueError('Package expanded size exceeds bound')
   h=hashlib.sha256();size=0
   with archive.open(item) as entry:
    for chunk in iter(lambda:entry.read(1024*1024),b''):size+=len(chunk);h.update(chunk)
   if size!=item.file_size:raise ValueError('ZIP entry size mismatch')
   files.append({'path':item.filename,'size':size,'sha256':h.hexdigest()})
 if not files:raise ValueError('Empty component')
 return dict(result,files=files)

def import_component_report(path,config):
 report_path=Path(path);report=json.loads(report_path.read_text())
 if any(report.get(k)!=v for k,v in {'schema':1,'product':'genesis','version':'0.4.0','saveSchema':4,'minimumHubVersion':'0.3.0','sourceCommit':config['genesis']['reviewedBuildCommit']}.items()):raise ValueError('Component report source/version mismatch')
 if sorted(item['kind'] for item in report['packages'])!=['game','model','runtime']:raise ValueError('Component report identities mismatch')
 for item in report['packages']:
  safe_path(item['path']);archive=report_path.parent/item['path']
  if not archive.resolve().is_relative_to(report_path.parent.resolve()):raise ValueError('Component report path escapes artifact directory')
  actual=inspect_package(archive)
  if any(item.get(k)!=actual[k] for k in ('size','sha256','files')):raise ValueError('Component report differs from actual archive')
  config['genesis']['packages'][item['kind']]['path']=str(archive)
 config['genesis']['components']=report.get('components')
 return report.get('provenance')

def integration_mapping(repository,build,integrated):
 for commit in (build,integrated):
  if not isinstance(commit,str) or not re.fullmatch('[a-f0-9]{40}',commit):raise ValueError('Explicit full source commits required')
 def git(*args):return subprocess.check_output(['git','-C',str(repository),*args],text=True).strip()
 # A squash/rebase may change SHA: only explicit source-tree equality justifies reuse.
 trees=[git('rev-parse',commit+'^{tree}') for commit in (build,integrated)]
 if trees[0]!=trees[1]:raise ValueError('Integration changed source tree: rebuild and review required')
 return {'reviewedBuildCommit':build,'integrationCommit':integrated,'tree':trees[0],'reuseRequiresProtectedHumanReview':True}

def prepare(config):
 report={'schema':1,'status':'blocked','publicDownloads':False,'authenticated':False,'publicationAuthorized':False,'blockers':[], 'provenance':{},'unsignedProposals':{},'userReportedLaptopAcceptance':config.get('userReportedLaptopAcceptance'), 'publicationOrder':['immutable installer and component archives','independently signed Hub and Genesis manifests','anonymous public verification and reviewed Windows evidence','signed catalog last and byte-preserving website mirror']}
 if config.get('componentReportPath'):report['componentProvenance']=import_component_report(config['componentReportPath'],config)
 blockers=report['blockers'];lock=json.loads((ROOT/'catalog/source-lock.json').read_text())
 for product in ('hub','genesis'):
  source=config[product]
  if source.get('reviewedBuildCommit')!=lock[product]['sourceCommit']:raise ValueError('Reviewed build source differs from canonical lock')
  if source.get('repository') and source.get('integrationCommit'):report['provenance'][product]=integration_mapping(source['repository'],source['reviewedBuildCommit'],source['integrationCommit'])
  else:blockers.append(product+': postmerge integration mapping missing')
 metadata=config['metadata']
 if not isinstance(metadata.get('sequence'),int) or metadata['sequence']<1 or not metadata.get('expires'):blockers.append('Reviewed sequence and fresh expiry missing')
 else:
  expiry=datetime.datetime.fromisoformat(metadata['expires'].replace('Z','+00:00'))
  if not datetime.datetime.now(datetime.timezone.utc)<expiry<=datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=30):raise ValueError('Invalid preparation expiry')
 hub=config['hub'];genesis=config['genesis'];ready=all(metadata.get(k) for k in ('sequence','expires','hubManifestUrl','genesisManifestUrl'))
 for k in ('hubManifestUrl','genesisManifestUrl'):
  if metadata.get(k):release_url(metadata[k],metadata_locator=True)
  else:blockers.append(k+' missing')
 for field in ('installerPath','installerUrl','publisherThumbprint'):
  if not hub.get(field):blockers.append('Hub '+field+' missing');ready=False
 if hub.get('installerUrl'):release_url(hub['installerUrl'])
 if hub.get('publisherThumbprint') and not re.fullmatch('[A-F0-9]{64}',hub['publisherThumbprint']):raise ValueError('Invalid reviewed publisher fingerprint')
 for kind,item in genesis['packages'].items():
  if kind not in ('game','runtime','model'):raise ValueError('Unexpected component')
  if item.get('url'):release_url(item['url'])
  if not item.get('path') or not item.get('url'):blockers.append(kind+' actual archive and immutable URL missing');ready=False
 if set(genesis['packages'])!={'game','runtime','model'}:raise ValueError('Missing component identity')
 if ready:
  common={'schema':1,'channel':'stable','platform':'windows-x64','sequence':metadata['sequence'],'expires':metadata['expires']}
  hub_payload=dict(common,product='hub',version='0.3.0',sourceCommit=hub['reviewedBuildCommit'],minimumHubVersion='0.3.0',minimumWindowsBuild=19041,installer=dict(digest_file(hub['installerPath']),url=hub['installerUrl'],publisherThumbprint=hub['publisherThumbprint']))
  genesis_payload=dict(common,product='genesis',version='0.4.0',sourceCommit=genesis['reviewedBuildCommit'],minimumHubVersion='0.3.0',saveSchema=4,packages=[dict(inspect_package(item['path']),kind=kind,url=item['url']) for kind,item in genesis['packages'].items()])
  validate_hub(hub_payload);validate_manifest(genesis_payload)
  catalog=json.loads((ROOT/'catalog/development.json').read_text());catalog.update(sequence=metadata['sequence'],expires=metadata['expires'])
  for entry,payload,url in [(catalog['infrastructure'],hub_payload,metadata['hubManifestUrl']),(catalog['products'][0],genesis_payload,metadata['genesisManifestUrl'])]:
   entry['sourceCommit']=payload['sourceCommit'];entry['release']={'manifestUrl':url,'version':payload['version'],'sourceCommit':payload['sourceCommit'],'platform':'windows-x64','download':{k:hub_payload['installer'][k] for k in ('url','size','sha256')} if entry['id']=='hub' else None}
  components=genesis.get('components')
  if components and all(c and c.get('version') and re.fullmatch('[a-f0-9]{40}',c.get('sourceCommit') or '') and c.get('licenseNotices') and all(n.get('url') for n in c['licenseNotices']) for c in components.values()):catalog['products'][0]['components']=components
  else:blockers.append('Component identity or approved publication license-notice URLs missing')
  validate_catalog(catalog)
  report['unsignedProposals']={'hub':hub_payload,'genesis':genesis_payload,'catalog':catalog}
 blockers.extend(['Production role pins and signed envelopes require independent review','Artifact-bound Windows/Authenticode acceptance requires protected human review','Anonymous published-byte proof has not run','Approved license and component provenance required'])
 if config.get('acceptanceEvidencePath'):
  evidence=json.loads(Path(config['acceptanceEvidencePath']).read_text());report['acceptanceEvidence']=evidence
  # An unsigned assertion is evidence to review, never authentication or approval.
  if evidence.get('synthetic') is not False:raise ValueError('Synthetic acceptance cannot be production evidence')
  if not ready:raise ValueError('Acceptance evidence requires exact actual artifacts')
  expected={ 'hub':hub_payload['installer']['sha256'],**{p['kind']:p['sha256'] for p in genesis_payload['packages']}}
  if evidence.get('artifactSha256')!=expected:raise ValueError('Acceptance evidence artifact binding mismatch')
  if evidence.get('publisherThumbprint')!=hub['publisherThumbprint'] or evidence.get('platform')!='windows-x64' or evidence.get('winVerifyTrust')!='passed':raise ValueError('Windows trust acceptance incomplete')
 return report

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('config');parser.add_argument('--output',required=True);args=parser.parse_args()
 Path(args.output).write_text(json.dumps(prepare(json.loads(Path(args.config).read_text())),indent=2)+'\n')
