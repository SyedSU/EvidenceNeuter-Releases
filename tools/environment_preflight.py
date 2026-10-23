"""Read-only guard against automatically creating an unprotected release environment."""
import argparse,json,subprocess

def validate_environment(environment,policies,expected='distribution-release'):
 if expected not in ('distribution-release','distribution-candidate'):raise ValueError('Unknown protected environment role')
 if environment.get('name')!=expected:raise ValueError('Existing '+expected+' environment required')
 rules=environment.get('protection_rules',[])
 reviewer=[rule for rule in rules if rule.get('type')=='required_reviewers']
 if len(reviewer)!=1 or not reviewer[0].get('reviewers') or reviewer[0].get('prevent_self_review') is not True:raise ValueError('Human reviewers with no self approval required')
 branch=environment.get('deployment_branch_policy')
 if not branch or branch.get('custom_branch_policies') is not True or branch.get('protected_branches') is not False:raise ValueError('Explicit main-only branch policy required')
 entries=policies.get('branch_policies',[])
 if len(entries)!=1 or entries[0].get('name')!='main' or entries[0].get('type')!='branch':raise ValueError('Only main branch may publish')
 if environment.get('can_admins_bypass') is not False:raise ValueError('Environment admin bypass must be disabled')
 return {'environment':expected,'protected':True,'readOnly':True}

def api(path):
 return json.loads(subprocess.check_output(['gh','api',path],text=True))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--environment',choices=('distribution-release','distribution-candidate'),default='distribution-release')
 name=parser.parse_args().environment
 root='repos/SyedSU/EvidenceNeuter-Releases/environments/'+name
 print(json.dumps(validate_environment(api(root),api(root+'/deployment-branch-policies'),name)))
