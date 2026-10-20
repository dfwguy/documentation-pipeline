"""Opt-in integration tests execute NVIDIA's pinned repo_docs, requiring network."""
import html
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from documentation_pipeline.onboard import main

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(os.environ.get('DOCS_BUILD_INTEGRATION') != '1', reason='Requires Packman and package network access')
@pytest.mark.parametrize('fixture', ['minimal', 'existing'])
def test_real_repo_docs_build(tmp_path, fixture):
    consumer = tmp_path / fixture
    shutil.copytree(ROOT / 'tests/fixtures' / fixture, consumer)
    # Cover repository directory links and unlabelled code fences.
    nested = consumer / 'docs/guide'
    nested.mkdir()
    (nested / 'README.md').write_text('# Guide\n\n```\necho hello\n```\n')
    readme = consumer / 'docs/README.md'
    readme.write_text(readme.read_text() + '\nRead the [guide](guide/).\n')
    original = {p.relative_to(consumer): p.read_bytes() for p in consumer.rglob('*') if p.is_file()}
    assert main([str(consumer), '--title', 'Example "Docs"', '--template', str(ROOT)]) == 0
    adopted_ci = (consumer / '.gitlab-ci.yml').read_bytes()
    subprocess.run([sys.executable, str(ROOT / 'runtime/build.py'), str(consumer)], check=True)
    site = consumer / '.docs-build/site'
    readme_html = (site / 'README.html').read_text()
    assert 'guide/README.html' in readme_html
    assert (site / 'index.html').is_file()
    assert 'Example "Docs"' in html.unescape((site / 'index.html').read_text())
    for path, content in original.items():
        if path != Path('.gitlab-ci.yml'):
            assert (consumer / path).read_bytes() == content
    assert (consumer / '.gitlab-ci.yml').read_bytes() == adopted_ci
    assert not (consumer / 'docs/conf.py').exists()
