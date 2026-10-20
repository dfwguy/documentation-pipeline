# Adopt the pipeline in an existing repository

This tutorial builds a disposable copy of `cluster-bringup`. Start with a local
checkout of this project on `feat/copier-docs-pipeline`, Python 3.11+, Git, Bash,
and curl. Keep the original consumer checkout unchanged while evaluating it.

## Install the onboarding command

From the `documentation-pipeline` checkout:

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
cp -a ../cluster-bringup /tmp/cluster-bringup-docs-trial
```

## Inspect the proposed adoption

```bash
.venv/bin/docs-onboard /tmp/cluster-bringup-docs-trial \
  --template . --vcs-ref HEAD \
  --title 'Cluster Bringup' --source-dir . \
  --ci-ref feat/copier-docs-pipeline \
  --dry-run --report /tmp/cluster-bringup-docs-plan.json
```

The command inspects existing CI, parses `repo.toml` if present, discovers Markdown
and reStructuredText, and shows proposed file diffs. `--source-dir .` includes the
root README and preserves links between it and `docs/`. Use `--source-dir docs`
when documentation is self-contained in that directory.

Read the manual decisions. Existing Pages jobs or conflicting managed files stop
adoption before planned files are written. Remote CI includes and workflow rules
need human review. Confirm the runner tags and project access requirements in the
[CI reference](../reference/configuration.md).

## Apply and build locally

Run the same command without `--dry-run`, then build:

```bash
.venv/bin/docs-onboard /tmp/cluster-bringup-docs-trial \
  --template . --vcs-ref HEAD \
  --title 'Cluster Bringup' --source-dir . \
  --ci-ref feat/copier-docs-pipeline
python3 runtime/build.py /tmp/cluster-bringup-docs-trial
python3 -m http.server 8000 --directory /tmp/cluster-bringup-docs-trial/.docs-build/site
```

Open `http://localhost:8000/`. Review `.docs-pipeline/navigation.rst` and arrange
entries for readers. The first navigation is a flat document inventory, with a
root README or index first; it does not invent a Diátaxis categorization for
existing content. Keep the consumer's established organization.

Inspect the diff: original source files and `repo.toml` should be unchanged;
existing CI jobs and stages should remain. Commit the generated configuration,
saved answers, navigation, CI integration, and ignore rule in the consumer when
ready. Onboarding itself never commits or pushes.

## Prepare GitLab adoption later

After a maintainer has committed and published a usable template ref, replace the
local `--template .` with the Git URL and choose a real `--vcs-ref`. Do not adopt
from a dirty template checkout for a lasting integration: Copier's temporary dirty
snapshot commit cannot be used as a durable update base.

```bash
docs-onboard /path/to/consumer \
  --template https://gitlab-master.nvidia.com/nvis-ova/documentation-pipeline.git \
  --vcs-ref feat/copier-docs-pipeline \
  --ci-ref feat/copier-docs-pipeline \
  --title 'Cluster Bringup' --source-dir . --dry-run
```

For initial testing, the shared project must expose that development branch.
Later, prefer an immutable commit or release tag for both refs. No remote
publishing steps are performed by this tutorial. Once the consumer pipeline is
run in GitLab, branch/MR pipelines build artifacts; default-branch pipelines also
publish Pages. Set appropriate Pages access controls before running that pipeline.
