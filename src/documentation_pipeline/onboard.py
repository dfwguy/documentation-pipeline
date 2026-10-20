"""Inspect first, render in a temporary directory, then apply a reviewed plan."""
import argparse
import difflib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import tomlkit
from copier import run_copy
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

YAML_IO = YAML()
YAML_IO.preserve_quotes = True


class DecisionRequired(ValueError):
    """Configuration cannot be safely merged automatically."""


def relative_path(root, value):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts or (not path.parts and value != '.'):
        raise DecisionRequired(f"Expected a repository-relative path: {value}")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise DecisionRequired(f"Path escapes repository through a symlink: {value}")
    return path.as_posix()


def yaml_text(value):
    stream = io.StringIO()
    YAML_IO.dump(value, stream)
    return stream.getvalue()


def inspect(root, source):
    """Parse existing inputs before Copier renders or the destination is changed."""
    findings, decisions = [], []
    ci_path = root / '.gitlab-ci.yml'
    ci = YAML_IO.load(ci_path.read_text()) if ci_path.exists() else {}
    if ci is None:
        ci = {}
    if not isinstance(ci, dict):
        raise DecisionRequired('.gitlab-ci.yml must be a YAML mapping')
    stages = ci.get('stages')
    if stages is not None and (not isinstance(stages, list) or not stages or any(not isinstance(stage, str) for stage in stages)):
        raise DecisionRequired('Existing stages must be a nonempty list of stage names; choose the docs trigger stage manually.')
    findings.append('CI keys: ' + ', '.join(map(str, ci.keys())) if ci else 'No existing CI configuration')
    if ci.get('include'):
        decisions.append('Review jobs and Pages definitions in existing CI includes; remote includes are not resolved locally.')
    if 'workflow' in ci:
        decisions.append('Check that existing workflow rules permit the desired branch and merge-request pipelines.')
    if 'pages' in ci or any(isinstance(job, dict) and job.get('pages') for job in ci.values()):
        raise DecisionRequired('Existing Pages publishing found; choose how to replace or combine it before onboarding.')
    repo = root / 'repo.toml'
    if repo.exists():
        parsed = tomlkit.parse(repo.read_text())
        findings.append('repo.toml tables: ' + ', '.join(parsed.keys()) + ' (preserved unchanged)')
        if 'repo_docs' in parsed:
            decisions.append('Existing repo_docs configuration remains unchanged; reconcile its settings with the isolated .docs-pipeline configuration.')
    else:
        findings.append('No repo.toml; docs will use an isolated configuration')
    source_path = root / source
    if not source_path.is_dir():
        raise DecisionRequired(f'Documentation directory does not exist: {source}')
    ignored = {'.git', '.venv', 'node_modules', '_build', '_repo', '__pycache__'}
    documents = []
    for directory, dirs, files in os.walk(source_path):
        dirs[:] = [name for name in dirs if not name.startswith('.') and name not in ignored]
        documents.extend(Path(directory) / name for name in files
                         if not name.startswith('.') and Path(name).suffix.lower() in {'.md', '.rst'})
    documents.sort()
    if not documents:
        raise DecisionRequired(f'No Markdown or reStructuredText documents found in {source}')
    if any(p.relative_to(source_path).with_suffix('').as_posix() == '_pipeline_index' for p in documents):
        raise DecisionRequired('Reserved document name _pipeline_index already exists')
    for document in documents:
        if not document.resolve().is_relative_to(source_path.resolve()):
            raise DecisionRequired(f'Document escapes source directory: {document}')
        if '\n' in document.name or '\r' in document.name:
            raise DecisionRequired(f'Document name cannot be represented safely in navigation: {document!s}')
    stems = [p.relative_to(source_path).with_suffix('').as_posix() for p in documents]
    if len(set(stems)) != len(stems):
        raise DecisionRequired('Documents have duplicate stems (.md/.rst); resolve Sphinx document-name collisions.')
    for document in documents:
        text = document.read_text(encoding='utf-8')
        if document.suffix.lower() == '.md':
            for language in sorted(set(re.findall(r'^```(pam|mermaid|caddyfile)\s*$', text, re.MULTILINE))):
                decisions.append(f'{document.relative_to(root)}: the pinned renderer has no {language} lexer; select plain text or add centralized rendering support.')
            for link in re.findall(r'\[[^\]]*\]\(([^)\s]+/)\)', text):
                if '://' in link:
                    continue
                directory = document.parent / link
                if directory.is_dir() and not any((directory / entry).is_file() for entry in ('README.md', 'README.rst', 'index.md', 'index.rst')):
                    decisions.append(f'{document.relative_to(root)}: directory link {link} needs a README/index landing page or a different target.')
    findings.append(f'Discovered {len(documents)} documents under {source}')
    if source != '.':
        decisions.append('Review links to files outside the source directory; select --source-dir . to include repository-root documents and assets.')
    decisions.append('Review generated navigation order and titles, runner tags, Pages access controls, and the CI job-token allowlist for the shared project.')
    return ci, documents, findings, decisions


def navigation(root, source, documents, title):
    entries = [p.relative_to(root / source).with_suffix('').as_posix() for p in documents]
    entries.sort(key=lambda p: (p.lower() not in {'readme', 'index'}, p.lower()))
    return f'{title}\n{"=" * len(title)}\n\n.. toctree::\n   :maxdepth: 3\n\n' + ''.join(f'   {entry}\n' for entry in entries)


def plan(args):
    root = args.repository.resolve()
    if not root.is_dir():
        raise DecisionRequired(f'Repository does not exist: {root}')
    for managed in ('.gitlab-ci.yml', '.gitignore', '.docs-pipeline', '.copier-docs-answers.yml'):
        relative_path(root, managed)
    source = relative_path(root, args.source_dir)
    nav = relative_path(root, args.nav)
    if Path(nav).suffix != '.rst':
        raise DecisionRequired('Navigation must be a reStructuredText (.rst) file')
    ci, documents, findings, decisions = inspect(root, source)
    if (root / '.copier-docs-answers.yml').exists():
        raise DecisionRequired('Saved answers already exist. Use copier update --answers-file .copier-docs-answers.yml instead.')
    if not args.title.strip() or '\n' in args.title or '\r' in args.title:
        raise DecisionRequired('Title must be a nonempty single line')
    data = dict(docs_title=args.title, docs_source_dir=source, docs_nav=nav,
                ci_project=args.ci_project, ci_ref=args.ci_ref)
    with tempfile.TemporaryDirectory(prefix='docs-onboard-') as temp:
        run_copy(args.template, temp, data=data, defaults=True, vcs_ref=args.vcs_ref, quiet=True)
        generated = {p.relative_to(temp).as_posix(): p.read_text() for p in Path(temp).rglob('*') if p.is_file()}
    changes = {}
    for name, content in generated.items():
        relative_path(root, name)
        destination = root / name
        if destination.exists() and destination.read_text() != content:
            raise DecisionRequired(f'Generated file already exists with different content: {name}')
        if not destination.exists():
            changes[name] = content
    if (root / nav).exists():
        findings.append(f'Existing navigation preserved: {nav}')
    else:
        changes[nav] = navigation(root, source, documents, args.title)
    trigger = {
        'stage': (ci.get('stages') or ['test'])[-1],
        'trigger': {'include': [{'local': '.docs-pipeline/ci.yml'}], 'strategy': 'depend'},
        'rules': [{'if': '$CI_PIPELINE_SOURCE == "merge_request_event"'},
                  {'if': '$CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS', 'when': 'never'},
                  {'if': '$CI_COMMIT_BRANCH'}],
    }
    if 'docs:pipeline' in ci and ci['docs:pipeline'] != trigger:
        raise DecisionRequired('Existing docs:pipeline job conflicts; rename it before onboarding.')
    ci['docs:pipeline'] = trigger
    # Do not rewrite YAML unnecessarily when an identical integration exists.
    if not (root / '.gitlab-ci.yml').exists() or (YAML_IO.load((root / '.gitlab-ci.yml').read_text()) or {}).get('docs:pipeline') != trigger:
        changes['.gitlab-ci.yml'] = yaml_text(ci)
    ignore = (root / '.gitignore').read_text() if (root / '.gitignore').exists() else ''
    if '/.docs-build/' not in ignore.splitlines():
        changes['.gitignore'] = ignore + ('\n' if ignore and not ignore.endswith('\n') else '') + '/.docs-build/\n'
    return root, changes, findings, decisions


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository', type=Path)
    parser.add_argument('--title', required=True)
    parser.add_argument('--source-dir', default='docs')
    parser.add_argument('--nav', default='.docs-pipeline/navigation.rst')
    parser.add_argument('--template', default='https://gitlab-master.nvidia.com/nvis-ova/documentation-pipeline.git', help='Copier template path or Git URL')
    parser.add_argument('--vcs-ref', default='HEAD', help='Copier template version')
    parser.add_argument('--ci-project', default='nvis-ova/documentation-pipeline')
    parser.add_argument('--ci-ref', default='feat/copier-docs-pipeline')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--report', type=Path, help='Write a JSON report (also in dry run)')
    args = parser.parse_args(argv)
    try:
        root, changes, findings, decisions = plan(args)
        report = {'dry_run': args.dry_run, 'findings': findings, 'changes': list(changes), 'manual_decisions': decisions}
        print(json.dumps(report, indent=2))
        for name, content in changes.items():
            old = (root / name).read_text() if (root / name).exists() else ''
            print(''.join(difflib.unified_diff(old.splitlines(True), content.splitlines(True), fromfile=f'a/{name}', tofile=f'b/{name}')))
        if args.report:
            args.report.write_text(json.dumps(report, indent=2) + '\n')
        if not args.dry_run:
            for name, content in changes.items():
                destination = root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content)
        return 0
    except (ValueError, OSError, YAMLError, subprocess.CalledProcessError) as error:
        print(f'Onboarding stopped; review the working tree and resolve: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
