"""Cross-check optional consumer sources against the reviewed lock; never execute them."""
import argparse
import ast
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from distribution import ROOT, validate_catalog


def build_identity(path, component_version):
    """Read literal manifest identities without importing a consumer's build script."""
    identities = []
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
        if not isinstance(node, ast.Dict):
            continue
        fields = {key.value: value for key, value in zip(node.keys, node.values)
                  if isinstance(key, ast.Constant) and isinstance(key.value, str)}
        if 'version' in fields and 'saveSchema' in fields:
            try:
                version = fields['version']
                version = component_version if isinstance(version, ast.Name) and version.id == 'VERSION' else ast.literal_eval(version)
                identities.append((version, ast.literal_eval(fields['saveSchema'])))
            except (ValueError, TypeError):
                raise ValueError('Genesis build identity must be literal reviewed metadata') from None
    if not identities or any(value != identities[0] for value in identities):
        raise ValueError('Genesis build identity missing or conflicting')
    return identities[0]


def package_version(path):
    values = []
    for node in ast.parse(path.read_text(encoding='utf-8')).body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'VERSION' for target in node.targets):
            values.append(ast.literal_eval(node.value))
    if len(values) != 1:
        raise ValueError('Genesis component VERSION missing or ambiguous')
    return values[0]


def check_consumers(website=None, hub=None, genesis=None):
    canonical = json.loads((ROOT / 'catalog/development.json').read_text())
    validate_catalog(canonical)
    schema = json.loads((ROOT / 'schemas/catalog.schema.json').read_text())
    lock = json.loads((ROOT / 'catalog/source-lock.json').read_text())
    checked = []
    for name, path, catalog_path, schema_path in [
        ('website', website, 'catalog.json', 'schemas/catalog.schema.json'),
        ('hub', hub, 'src/Catalog/development.json', 'src/Catalog/catalog.schema.json'),
    ]:
        if path is None:
            continue
        base = Path(path)
        if json.loads((base / catalog_path).read_text()) != canonical:
            raise ValueError(name + ' catalog differs from canonical')
        if json.loads((base / schema_path).read_text()) != schema:
            raise ValueError(name + ' schema differs from canonical')
        checked.append(name + ':catalog/schema')
    hub_version = lock['hub']['version']
    genesis_version = lock['genesis']['version']
    epoch = lock['genesis']['saveSchema']
    if hub:
        base = Path(hub)
        text = (base / 'src/Updates/Metadata.cs').read_text(encoding='utf-8')
        # Ignore source comments; a commented-out constant cannot prove identity.
        text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
        versions = re.findall(r'\bHubVersion\s*=\s*"([^"]+)"', text)
        project_versions = ET.parse(base / 'src/Hub.csproj').getroot().findall('.//Version')
        if versions != [hub_version] or [node.text for node in project_versions] != [hub_version]:
            raise ValueError('Hub application/update version differs from reviewed lock')
        checked.append('hub:version' + hub_version)
    if genesis:
        base = Path(genesis)
        component_version = package_version(base / 'scripts/component_packages.py')
        if (build_identity(base / 'scripts/build_native.py', component_version) != (genesis_version, epoch)
                or component_version != genesis_version
                or json.loads((base / 'package.json').read_text())['version'] != genesis_version):
            raise ValueError('Genesis application/build/component identity differs from reviewed lock')
        text = (base / 'native/scripts/state.gd').read_text(encoding='utf-8')
        text = re.sub(r'#[^\n]*', '', text)
        fresh = re.search(r'^func fresh\([^\n]*\n(.*?)(?=^func |\Z)', text, flags=re.M | re.S)
        versions = re.findall(r'[\'"]version[\'"]\s*:\s*(\d+)\b', fresh.group(1) if fresh else '')
        if versions != [str(epoch)]:
            raise ValueError('Genesis fresh profile format differs from reviewed save epoch')
        checked.append('genesis:version' + genesis_version + '/saveSchema' + str(epoch))
    manifest = ROOT / 'catalog/genesis-candidate.json'
    if manifest.exists():
        from distribution import validate_manifest
        data = json.loads(manifest.read_text())
        validate_manifest(data)
        if (data['saveSchema'] != epoch or data['minimumHubVersion'] != hub_version
                or data['version'] != genesis_version or data['sourceCommit'] != lock['genesis']['sourceCommit']):
            raise ValueError('Candidate identity or profile compatibility differs from reviewed lock')
        checked.append('genesis:minimumHub' + hub_version)
    return {'checked': checked, 'publicDownloads': canonical['publicDownloads'],
            'signedCandidatePresent': manifest.exists()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--website', type=Path)
    parser.add_argument('--hub', type=Path)
    parser.add_argument('--genesis', type=Path)
    args = parser.parse_args()
    print(json.dumps(check_consumers(args.website, args.hub, args.genesis), indent=2))
