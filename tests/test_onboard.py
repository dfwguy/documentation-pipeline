import json
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
    adopted = contents(consumer)
    assert main(args(consumer, template)) == 0
    assert contents(consumer) == adopted


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


@pytest.mark.parametrize('fence', [
    '1. Configure:\n\n   ```caddyfile\n   :80 {}\n   ```\n',
    '> ```pam\n> account required pam_permit.so\n> ```\n',
    '  ~~~mermaid\n  graph LR; A-->B\n  ~~~\n',
    '- Parent\n  - Child\n\n    ````caddyfile extra\n    :80 {}\n    ````\n',
])
def test_nested_fences_report_language_and_line(consumer, template, capsys, fence):
    document = consumer / 'docs/install.md'
    document.write_text('# Install\n\n' + fence)
    before = contents(consumer)
    assert main(args(consumer, template) + ['--dry-run']) == 0
    report, _ = json.JSONDecoder().raw_decode(capsys.readouterr().out)
    warnings = [message for message in report['manual_decisions'] if 'has no' in message]
    assert len(warnings) == 1
    assert warnings[0].startswith('docs/install.md:')
    assert contents(consumer) == before


def test_fence_examples_and_indented_code_are_not_fences(consumer, template, capsys):
    (consumer / 'docs/install.md').write_text('# Install\n\n`````text\n```caddyfile\n:80 {}\n```\n`````\n\n    ```mermaid\n    graph LR; A-->B\n    ```\n')
    assert main(args(consumer, template) + ['--dry-run']) == 0
    report, _ = json.JSONDecoder().raw_decode(capsys.readouterr().out)
    assert not any('has no' in message for message in report['manual_decisions'])


def test_repeat_preserves_overrides_curated_navigation_and_formatting(consumer, template, capsys):
    assert main(args(consumer, template)) == 0
    ci = consumer / '.docs-pipeline/ci.yml'
    ci.write_text(ci.read_text() + '\ndocs:build:\n  tags: [team-runner]\npages:\n  tags: [team-runner]\n')
    nav = consumer / '.docs-pipeline/navigation.rst'
    nav.write_text('Curated\n=======\n\n.. toctree::\n\n   install\n')
    (consumer / '.docs-pipeline/ADOPTION.md').write_text('Consumer adoption notes.\n')
    root_ci = consumer / '.gitlab-ci.yml'
    root_ci.write_text('# Maintainer formatting\n\n' + root_ci.read_text())
    before = contents(consumer)
    capsys.readouterr()
    assert main(args(consumer, template)) == 0
    report, _ = json.JSONDecoder().raw_decode(capsys.readouterr().out)
    assert report['changes'] == []
    assert contents(consumer) == before
    assert main(args(consumer, template) + ['--dry-run']) == 0
    assert contents(consumer) == before
    assert main(args(consumer, template) + ['--ci-ref', 'another-revision']) == 2
    assert contents(consumer) == before


@pytest.mark.parametrize('drift', ['include', 'runtime', 'project'])
def test_repeat_rejects_inconsistent_references_without_rewriting(consumer, template, drift):
    assert main(args(consumer, template)) == 0
    file = consumer / '.docs-pipeline/ci.yml'
    ci = YAML().load(file.read_text())
    if drift == 'include':
        ci['include'][0]['ref'] = 'different-ref'
    elif drift == 'runtime':
        ci['variables']['DOCS_PIPELINE_REF'] = 'different-ref'
    else:
        ci['variables']['DOCS_PIPELINE_PROJECT'] = 'different/project'
    with file.open('w') as output:
        YAML().dump(ci, output)
    before = contents(consumer)
    assert main(args(consumer, template)) == 2
    assert contents(consumer) == before


def test_update_from_published_template_preserves_runner_overrides(consumer, tmp_path):
    # Use the actual published template as the earlier revision, in a local Git
    # repository so the test never needs credentials or changes the source repo.
    earlier = '89deb4ab5ad65b7697481d619d4acbcf34ffa67e'
    template = tmp_path / 'published-template'
    template.mkdir()
    files = git(ROOT, 'ls-tree', '-r', '--name-only', earlier, '--', 'copier.yml', 'template').splitlines()
    for name in files:
        path = template / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(git(ROOT, 'show', f'{earlier}:{name}') + '\n')
    git(template, 'init', '-b', 'main')
    git(template, 'config', 'user.email', 'test@example.com')
    git(template, 'config', 'user.name', 'Test')
    git(template, 'add', '.')
    git(template, 'commit', '-m', 'Published baseline')
    assert main(args(consumer, template)) == 0
    ci_file = consumer / '.docs-pipeline/ci.yml'
    ci_file.write_text(ci_file.read_text() + '\n# Runner overrides\ndocs:build:\n  tags: [team-runner, medium]\npages:\n  tags: [team-runner, medium]\n')
    nav = consumer / '.docs-pipeline/navigation.rst'
    nav.write_text(nav.read_text() + '\nCurated by the consumer.\n')
    adoption = consumer / '.docs-pipeline/ADOPTION.md'
    adoption.write_text('Consumer record.\n')
    before = contents(consumer)
    git(consumer, 'init', '-b', 'main')
    git(consumer, 'config', 'user.email', 'test@example.com')
    git(consumer, 'config', 'user.name', 'Test')
    git(consumer, 'add', '.')
    git(consumer, 'commit', '-m', 'Consumer integration')
    shutil.copy(ROOT / 'copier.yml', template)
    shutil.copytree(ROOT / 'template', template / 'template', dirs_exist_ok=True)
    git(template, 'add', '.')
    git(template, 'commit', '-m', 'Current template')
    run_update(consumer, answers_file='.copier-docs-answers.yml', vcs_ref='HEAD',
               defaults=True, overwrite=True, quiet=True)
    child = YAML().load(ci_file.read_text())
    assert child['include'][0]['ref'] == child['variables']['DOCS_PIPELINE_REF'] == 'feat/copier-docs-pipeline'
    assert child['include'][0]['project'] == child['variables']['DOCS_PIPELINE_PROJECT']
    assert child['docs:build']['tags'] == child['pages']['tags'] == ['team-runner', 'medium']
    for name, content in before.items():
        if name not in {'.copier-docs-answers.yml', '.docs-pipeline/ci.yml'}:
            assert (consumer / name).read_bytes() == content
    assert not list(consumer.rglob('*.rej'))
    assert not list(consumer.rglob('*.conflict'))


def test_copier_reference_change_keeps_include_and_runtime_aligned(consumer, template):
    assert main(args(consumer, template)) == 0
    git(consumer, 'init', '-b', 'main')
    git(consumer, 'config', 'user.email', 'test@example.com')
    git(consumer, 'config', 'user.name', 'Test')
    git(consumer, 'add', '.')
    git(consumer, 'commit', '-m', 'Adopt')
    ref = '0123456789abcdef0123456789abcdef01234567'
    run_update(consumer, answers_file='.copier-docs-answers.yml', vcs_ref='HEAD', data={'ci_ref': ref}, defaults=True, overwrite=True, quiet=True)
    child = YAML().load((consumer / '.docs-pipeline/ci.yml').read_text())
    saved = YAML().load((consumer / '.copier-docs-answers.yml').read_text())
    assert child['include'][0]['ref'] == child['variables']['DOCS_PIPELINE_REF'] == saved['ci_ref'] == ref


def test_repeat_accepts_mapping_form_of_trigger_include(consumer, template):
    assert main(args(consumer, template)) == 0
    path = consumer / '.gitlab-ci.yml'
    ci = YAML().load(path.read_text())
    ci['docs:pipeline']['trigger']['include'] = {'local': '.docs-pipeline/ci.yml'}
    with path.open('w') as output:
        YAML().dump(ci, output)
    before = contents(consumer)
    assert main(args(consumer, template)) == 0
    assert contents(consumer) == before
