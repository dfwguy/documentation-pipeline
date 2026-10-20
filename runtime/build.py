#!/usr/bin/env python3
"""Build a consumer in an isolated workspace using the centralized repo tools."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import tomllib


def inside(root, value):
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Path escapes repository: {value}")
    return path


def build(root):
    root = Path(root).resolve()
    runtime = Path(__file__).resolve().parent
    config = tomllib.loads((root / ".docs-pipeline/config.toml").read_text())
    source = inside(root, config["source_dir"])
    navigation = inside(root, config["navigation"])
    if not source.is_dir() or not navigation.is_file():
        raise ValueError("Documentation source directory or navigation does not exist")
    work = root / ".docs-build"
    work.mkdir(exist_ok=True)
    # Build from a snapshot: repo_docs writes conf.py and other generated files.
    with tempfile.TemporaryDirectory(prefix="repo-docs-", dir=work) as temporary:
        staging = Path(temporary)
        snapshot = staging / "source"
        def ignore(directory, names):
            return {n for n in names if n.startswith('.') or n in {"_build", "_repo", "node_modules", "__pycache__"}}
        # Check only included files; excluded virtualenvs often contain symlinks.
        for directory, dirs, files in os.walk(source):
            excluded = ignore(directory, dirs + files)
            dirs[:] = [name for name in dirs if name not in excluded]
            for name in dirs + [name for name in files if name not in excluded]:
                path = Path(directory) / name
                if path.is_symlink():
                    raise ValueError(f"Documentation symlinks require manual review: {path}")
        if (source / "_pipeline_index.rst").exists() or (source / "_pipeline_index.md").exists():
            raise ValueError("Reserved document name _pipeline_index already exists")
        shutil.copytree(source, snapshot, ignore=ignore)
        shutil.copyfile(navigation, snapshot / "_pipeline_index.rst")
        # repo_docs 0.39.2 adds version.js independently of the selector setting.
        # We export one site without the parent versions/ layout that script needs.
        sphinx_overrides = (
            f"project = {config['title']!r}\n"
            'highlight_language = "none"\n'
            'html_js_files = [script for script in html_js_files if script != "version.js"]\n'
        )
        repo_config = f'''[repo]
name = "documentation"
[repo.folders]
repo_deps = {json.dumps(str(runtime / "_deps"))}
[repo_docs]
enabled = true
project = "documentation"
name = "Documentation"
sphinx_conf_py_extra = {json.dumps(sphinx_overrides)}
python_paths = [{json.dumps(str(runtime / 'sphinx_ext'))}]
extensions_extra = ["repository_links"]
version = "1.0"
docs_root = "${{root}}/source"
docs_dst = "${{root}}/_build/docs"
root_doc = "_pipeline_index"
sphinx_dont_exclude_patterns = [{json.dumps(str(snapshot / 'README.md'))}]
sphinx_exclude_patterns = {json.dumps([navigation.relative_to(source).as_posix()] if navigation.is_relative_to(source) else [])}
sphinx_version = "4.5.0.2-py3.10-${{platform}}"
version_selector_enabled = false
social_media_set = ""
'''
        (staging / "repo.toml").write_text(repo_config)
        subprocess.run([str(runtime / "packman/python.sh"), str(runtime / "repoman/bootstrap.py"), str(staging), "docs"], check=True, cwd=staging)
        output = staging / "_build/docs/documentation/latest"
        if not (output / "_pipeline_index.html").is_file():
            raise RuntimeError(f"repo_docs did not produce the expected HTML in {output}")
        site = work / "site"
        if site.exists():
            shutil.rmtree(site)
        shutil.copytree(output, site)
        shutil.copyfile(site / "_pipeline_index.html", site / "index.html")
    print(f"Built documentation: {work / 'site/index.html'}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else ".")
