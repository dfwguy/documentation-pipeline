"""Check generated CI references and the documented rule scenarios locally.

This evaluates the small expression subset in these jobs, not GitLab scheduling.
"""
import re
from pathlib import Path

import pytest
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
SHARED = YAML().load((ROOT / 'ci/docs.gitlab-ci.yml').read_text())


def selected(rules, environment):
    for rule in rules:
        expression = re.sub(r'\$([A-Z_]+)', lambda match: repr(environment.get(match[1], '')), rule.get('if', 'True'))
        expression = expression.replace('&&', 'and').replace('||', 'or')
        if eval(expression, {'__builtins__': {}}, {}):
            return rule.get('when', 'on_success') != 'never'
    return False


@pytest.mark.parametrize('source,branch,default,expected', [
    ('parent_pipeline', 'main', 'main', True),
    ('parent_pipeline', 'production', 'production', True),
    ('parent_pipeline', 'main', 'production', False),
    ('parent_pipeline', 'feature', 'main', False),
    ('parent_pipeline', '', 'main', False),  # MR or tag child pipeline
    ('merge_request_event', 'main', 'main', False),
    ('push', 'main', 'main', False),
    ('web', 'main', 'main', False),
])
def test_pages_only_in_default_branch_child(source, branch, default, expected):
    assert selected(SHARED['pages']['rules'], {
        'CI_PIPELINE_SOURCE': source,
        'CI_COMMIT_BRANCH': branch,
        'CI_DEFAULT_BRANCH': default,
    }) == expected


def test_pages_uses_only_successful_build_artifact():
    assert SHARED['pages']['needs'] == [{'job': 'docs:build', 'artifacts': True}]
    assert SHARED['pages']['artifacts']['paths'] == ['public/']
    assert '.docs-build/runtime-sha.txt' in SHARED['.build-docs']['artifacts']['paths']
    assert 'git -C .docs-build/runtime rev-parse HEAD > .docs-build/runtime-sha.txt' in SHARED['.build-docs']['before_script']


@pytest.mark.parametrize('source,branch,open_mrs,expected', [
    ('push', 'feature', '', True),
    ('push', 'feature', 'group/project!1', False),
    ('merge_request_event', '', 'group/project!1', True),
    ('push', '', '', False),
])
def test_parent_trigger_deduplication(tmp_path, source, branch, open_mrs, expected):
    from documentation_pipeline.onboard import main
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'docs/README.md').write_text('# Docs\n')
    assert main([str(tmp_path), '--title', 'Docs', '--template', str(ROOT)]) == 0
    trigger = YAML().load((tmp_path / '.gitlab-ci.yml').read_text())['docs:pipeline']
    assert selected(trigger['rules'], {
        'CI_PIPELINE_SOURCE': source, 'CI_COMMIT_BRANCH': branch, 'CI_OPEN_MERGE_REQUESTS': open_mrs,
    }) == expected
