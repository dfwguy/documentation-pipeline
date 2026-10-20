import shutil
import subprocess
from pathlib import Path

import pytest
from copier import run_update
from ruamel.yaml import YAML

from documentation_pipeline.onboard import main

ROOT = Path(__file__).resolve().parents[1]


def git(path, *args):
    return subprocess.run(['git', '-C', str(path), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def template(tmp_path):
    target = tmp_path / 'template'
    target.mkdir()
    shutil.copy(ROOT / 'copier.yml', target)
    shutil.copytree(ROOT / 'template', target / 'template')
    git(target, 'init', '-b', 'main')
    git(target, 'config', 'user.email', 'test@example.com')
    git(target, 'config', 'user.name', 'Test')
    git(target, 'add', '.')
    git(target, 'commit', '-m', 'Template baseline')
    return target


@pytest.fixture
def consumer(tmp_path):
    target = tmp_path / 'consumer'
    shutil.copytree(ROOT / 'tests/fixtures/existing', target)
    return target


def args(consumer, template):
    return [str(consumer), '--title', 'Example docs', '--template', str(template)]


def contents(path):
    return {p.relative_to(path).as_posix(): p.read_bytes() for p in path.rglob('*') if p.is_file() and '.git' not in p.parts}


def test_dry_run_does_not_write(consumer, template):
    before = contents(consumer)
    assert main(args(consumer, template) + ['--dry-run']) == 0
    assert contents(consumer) == before


def test_preserves_jobs_repo_and_sources(consumer, template):
    before = contents(consumer)
    old_ci = YAML().load(before['.gitlab-ci.yml'])
    assert main(args(consumer, template)) == 0
    ci = YAML().load((consumer / '.gitlab-ci.yml').read_text())
    for key, value in old_ci.items():
        assert ci[key] == value
    assert ci['docs:pipeline']['stage'] == 'verify'
    for path in ['repo.toml', 'docs/README.md', 'docs/install.md']:
        assert (consumer / path).read_bytes() == before[path]
    assert '# Existing pipeline' in (consumer / '.gitlab-ci.yml').read_text()
    assert '   README\n   install\n' in (consumer / '.docs-pipeline/navigation.rst').read_text()
    answers = YAML().load((consumer / '.copier-docs-answers.yml').read_text())
    assert git(template, 'rev-parse', answers['_commit']) == git(template, 'rev-parse', 'HEAD')
    assert main(args(consumer, template)) == 2


def test_minimal_uses_real_stage(tmp_path, template):
    consumer = tmp_path / 'minimal'
    shutil.copytree(ROOT / 'tests/fixtures/minimal', consumer)
    assert main(args(consumer, template)) == 0
    assert YAML().load((consumer / '.gitlab-ci.yml').read_text())['docs:pipeline']['stage'] == 'test'


@pytest.mark.parametrize('conflict', ['pages', 'job', 'config', 'invalid_toml', 'invalid_ci', 'duplicate_docs'])
def test_conflicts_leave_repository_untouched(consumer, template, conflict):
    if conflict == 'pages':
        (consumer / '.gitlab-ci.yml').write_text('pages:\n  script: [echo existing]\n')
    elif conflict == 'job':
        (consumer / '.gitlab-ci.yml').write_text('docs:pipeline:\n  script: [echo existing]\n')
    elif conflict == 'config':
        (consumer / '.docs-pipeline').mkdir()
        (consumer / '.docs-pipeline/config.toml').write_text('title = "custom"\n')
    elif conflict == 'invalid_toml':
        (consumer / 'repo.toml').write_text('invalid = [')
    elif conflict == 'invalid_ci':
        (consumer / '.gitlab-ci.yml').write_text('- not a mapping\n')
    else:
        (consumer / 'docs/install.rst').write_text('Duplicate\n=========\n')
    before = contents(consumer)
    assert main(args(consumer, template)) == 2
    assert contents(consumer) == before


def test_root_source_and_existing_navigation(consumer, template):
    (consumer / 'index.rst').write_text('Existing navigation\n===================\n')
    assert main(args(consumer, template) + ['--source-dir', '.', '--nav', 'index.rst']) == 0
    assert (consumer / 'index.rst').read_text().startswith('Existing navigation')


def test_path_escape(consumer, template):
    before = contents(consumer)
    assert main(args(consumer, template) + ['--nav', '../escape.rst']) == 2
    assert contents(consumer) == before


def test_copier_update_preserves_consumer_edits(consumer, template):
    assert main(args(consumer, template)) == 0
    git(consumer, 'init', '-b', 'main')
    git(consumer, 'config', 'user.email', 'test@example.com')
    git(consumer, 'config', 'user.name', 'Test')
    nav = consumer / '.docs-pipeline/navigation.rst'
    nav.write_text(nav.read_text() + '\nConsumer maintained navigation.\n')
    config = consumer / '.docs-pipeline/config.toml'
    config.write_text(config.read_text() + '\n# consumer comment\n')
    git(consumer, 'add', '.')
    git(consumer, 'commit', '-m', 'Adopt docs')
    original_ci = (consumer / '.gitlab-ci.yml').read_bytes()
    template_config = template / 'template/.docs-pipeline/config.toml.jinja'
    template_config.write_text('# New shared template comment\n' + template_config.read_text())
    git(template, 'add', '.')
    git(template, 'commit', '-m', 'Evolve template')
    run_update(consumer, answers_file='.copier-docs-answers.yml', vcs_ref='HEAD', defaults=True, overwrite=True, quiet=True)
    assert 'New shared template comment' in config.read_text()
    assert '# consumer comment' in config.read_text()
    assert 'Consumer maintained navigation' in nav.read_text()
    assert (consumer / '.gitlab-ci.yml').read_bytes() == original_ci
    assert not list(consumer.rglob('*.rej'))


def test_invalid_yaml_syntax_leaves_files_untouched(consumer, template):
    (consumer / '.gitlab-ci.yml').write_text('broken: [\n')
    before = contents(consumer)
    assert main(args(consumer, template)) == 2
    assert contents(consumer) == before


def test_external_ci_symlink_is_rejected(consumer, template, tmp_path):
    outside = tmp_path / 'outside.yml'
    outside.write_text('job:\n  script: [echo external]\n')
    (consumer / '.gitlab-ci.yml').unlink()
    (consumer / '.gitlab-ci.yml').symlink_to(outside)
    assert main(args(consumer, template)) == 2
    assert 'docs:pipeline' not in outside.read_text()


def test_reports_source_rendering_decisions(consumer, template, capsys):
    (consumer / 'docs/how-to').mkdir()
    (consumer / 'docs/README.md').write_text('# Docs\n\n[Tasks](how-to/)\n\n```mermaid\ngraph LR; A-->B\n```\n')
    assert main(args(consumer, template) + ['--dry-run']) == 0
    output = capsys.readouterr().out
    assert 'needs a README/index landing page' in output
    assert 'has no mermaid lexer' in output
