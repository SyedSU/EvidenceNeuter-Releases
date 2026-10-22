"""Consumer identity checks on isolated source fixtures; no sibling checkout required."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ConsumerIdentityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.distribution = self.root / 'distribution'
        for name in ('tools', 'schemas', 'catalog'):
            shutil.copytree(ROOT / name, self.distribution / name)
        self.hub = self.root / 'hub'
        self.genesis = self.root / 'genesis'
        for path in (self.hub / 'src/Updates', self.hub / 'src/Catalog',
                     self.genesis / 'scripts', self.genesis / 'native/scripts'):
            path.mkdir(parents=True)
        shutil.copyfile(ROOT / 'catalog/development.json', self.hub / 'src/Catalog/development.json')
        shutil.copyfile(ROOT / 'schemas/catalog.schema.json', self.hub / 'src/Catalog/catalog.schema.json')
        self.lock = json.loads((ROOT / 'catalog/source-lock.json').read_text())
        self.write_sources()

    def write_sources(self):
        hub = self.lock['hub']['version']
        genesis = self.lock['genesis']['version']
        epoch = self.lock['genesis']['saveSchema']
        (self.distribution / 'catalog/source-lock.json').write_text(json.dumps(self.lock))
        (self.hub / 'src/Updates/Metadata.cs').write_text(f'const string HubVersion = "{hub}";')
        (self.hub / 'src/Hub.csproj').write_text(f'<Project><PropertyGroup><Version>{hub}</Version></PropertyGroup></Project>')
        (self.genesis / 'package.json').write_text(json.dumps({'version': genesis}))
        (self.genesis / 'scripts/component_packages.py').write_text(f'VERSION = {genesis!r}\n')
        (self.genesis / 'scripts/build_native.py').write_text(f'manifest = {{"version": {genesis!r}, "saveSchema": {epoch}}}\n')
        (self.genesis / 'native/scripts/state.gd').write_text(f'func fresh():\n\treturn {{"version":{epoch}}}\n')

    def check(self):
        return subprocess.run([sys.executable, 'tools/check_consumers.py', '--hub', str(self.hub),
                               '--genesis', str(self.genesis)], cwd=self.distribution,
                              capture_output=True, text=True)

    def test_current_sources_match_reviewed_lock(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)['publicDownloads'])

    def test_versions_follow_reviewed_lock_instead_of_hardcoded_values(self):
        self.lock['hub']['version'] = '0.7.0'
        self.lock['genesis']['version'] = '0.9.0'
        self.write_sources()
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_each_independent_version_or_epoch_mismatch_is_rejected(self):
        cases = {
            'src/Hub.csproj': (self.hub, '<Project><PropertyGroup><Version>9.0.0</Version></PropertyGroup></Project>'),
            'src/Updates/Metadata.cs': (self.hub, 'const string HubVersion="9.0.0";'),
            'package.json': (self.genesis, '{"version":"9.0.0"}'),
            'scripts/component_packages.py': (self.genesis, 'VERSION="9.0.0"'),
            'scripts/build_native.py': (self.genesis, 'manifest={"version":"9.0.0","saveSchema":4}'),
            'native/scripts/state.gd': (self.genesis, 'func fresh():\n\treturn {"version":1}\n'),
        }
        for relative, (base, content) in cases.items():
            with self.subTest(source=relative):
                self.write_sources()
                (base / relative).write_text(content)
                self.assertNotEqual(self.check().returncode, 0, relative)

    def test_comment_cannot_supply_missing_build_identity(self):
        (self.genesis / 'scripts/build_native.py').write_text('# manifest={"version":"0.5.0","saveSchema":4}\n')
        self.assertNotEqual(self.check().returncode, 0)

    def test_manifest_can_reference_checked_component_version_without_execution(self):
        version = self.lock['genesis']['version']
        epoch = self.lock['genesis']['saveSchema']
        marker = self.root / 'must-not-execute'
        (self.genesis / 'scripts/build_native.py').write_text(
            'from component_packages import VERSION\n'
            f'open({str(marker)!r}, "w").write("unsafe import")\n'
            f'manifest={{"version":{version!r},"saveSchema":{epoch}}}\n'
            f'info={{"version":VERSION,"saveSchema":{epoch}}}\n')
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(marker.exists())
