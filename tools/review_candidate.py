"""Read-only workflow verification before protected publication. Never signs metadata."""
import json
import os
from pathlib import Path
import re
import subprocess

from cryptography.hazmat.primitives import serialization
try:
    from .distribution import validate_candidate,verify
    from .verify_bundle import verify_bundle
except ImportError:
    from distribution import validate_candidate,verify
    from verify_bundle import verify_bundle


def reviewed_json(path):
    p=Path(path)
    if not path or p.is_absolute() or '..' in p.parts or not p.is_file() or p.suffix!='.json' or not p.resolve().is_relative_to(Path.cwd().resolve()):
        raise ValueError('Invalid reviewed metadata path')
    return json.loads(p.read_text(encoding='utf-8'))


def public_key(environment,name,required=True):
    value=environment.get(name,'')
    if not value:
        if required:raise ValueError('Reviewed production trust prerequisite absent: '+name)
        return None
    return serialization.load_pem_public_key(value.encode())


def sequence_floor(environment,name):
    value=environment.get(name,'')
    if not isinstance(value,str) or not re.fullmatch(r'0|[1-9][0-9]*',value):
        raise ValueError('Explicit reviewed sequence floor required: '+name)
    return int(value)


def review(environment=None):
    environment=os.environ if environment is None else environment
    commit=environment['COMMIT'];tag=environment['TAG'];kind=environment['KIND']
    if kind not in ('catalog','manifest','hub'):raise ValueError('Invalid metadata role')
    if not re.fullmatch('[a-f0-9]{40}',commit) or subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()!=commit:
        raise ValueError('Reviewed source commit mismatch')
    if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,100}',tag):raise ValueError('Invalid reviewed metadata tag')
    floors={role:sequence_floor(environment,name) for role,name in [
        ('catalog','CATALOG_SEQUENCE_FLOOR'),('hub','HUB_SEQUENCE_FLOOR'),('manifest','GENESIS_SEQUENCE_FLOOR')]}
    keys={role:public_key(environment,name,role==kind) for role,name in [
        ('catalog','PUBLIC_KEY'),('hub','HUB_PUBLIC_KEY'),('manifest','GENESIS_PUBLIC_KEY')]}
    envelope=reviewed_json(environment['FILE'])
    # Published metadata must advance its own role. Already published referenced
    # product envelopes may equal their retained floor during catalog activation.
    data=verify(envelope,keys[kind],kind,floors[kind]+1)
    public_activation=kind=='catalog' and data['publicDownloads']
    hub_file=environment.get('HUB_FILE','');genesis_file=environment.get('GENESIS_FILE','')
    hub=reviewed_json(hub_file) if hub_file else None
    genesis=reviewed_json(genesis_file) if genesis_file else None
    urls={'hub':environment.get('HUB_URL',''),'genesis':environment.get('GENESIS_URL','')}
    lock=json.loads(Path('catalog/source-lock.json').read_text())
    pin=environment.get('PUBLISHER_PIN')
    validate_candidate(envelope,keys[kind],kind,lock,hub,genesis,urls,keys['hub'],keys['manifest'],pin)
    if public_activation:
        proof=verify_bundle(envelope,hub,genesis,keys['catalog'],keys['hub'],keys['manifest'],lock,
                            pin,urls['hub'],urls['genesis'],floors['catalog']+1,floors['hub'],floors['manifest'])
        print(json.dumps(proof,indent=2))
    verify(envelope,keys[kind],kind,floors[kind]+1)
    return data


if __name__=='__main__':
    result=review()
    print(json.dumps({'kind':os.environ['KIND'],'sequence':result['sequence'],'expires':result['expires'],
                      'publicDownloads':result.get('publicDownloads',False),'publicationAuthorized':False},indent=2))
