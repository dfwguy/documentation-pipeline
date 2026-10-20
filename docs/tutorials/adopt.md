# Adopt the pipeline in an existing repository

This tutorial adopts an existing repository that has Markdown and optional CI.
Use a disposable copy of an unadopted repository for the exercise. Start with a local
checkout of this project on `feat/copier-docs-pipeline`, Python 3.11+, Git, Bash,
and curl. Keep the original consumer checkout unchanged while evaluating it.

## Install the onboarding command

From the `documentation-pipeline` checkout:

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
cp -a /path/to/unadopted-repository /tmp/docs-adoption-trial
```

## Inspect the proposed adoption

```bash
.venv/bin/docs-onboard /tmp/docs-adoption-trial \
  --template . --vcs-ref HEAD \
  --title 'Project Documentation' --source-dir . \
  --ci-ref feat/copier-docs-pipeline \
  --dry-run --report /tmp/docs-adoption-plan.json
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
.venv/bin/docs-onboard /tmp/docs-adoption-trial \
  --template . --vcs-ref HEAD \
  --title 'Project Documentation' --source-dir . \
  --ci-ref feat/copier-docs-pipeline
python3 runtime/build.py /tmp/docs-adoption-trial
python3 -m http.server 8000 --directory /tmp/docs-adoption-trial/.docs-build/site
```

Open `http://localhost:8000/`. Review `.docs-pipeline/navigation.rst` and arrange
entries for readers. The first navigation is a flat document inventory, with a
root README or index first; it does not invent a Diátaxis categorization for
existing content. Keep the consumer's established organization.

Inspect the diff: original source files and `repo.toml` should be unchanged;
existing CI jobs and stages should remain. Commit the generated configuration,
saved answers, navigation, CI integration, and ignore rule in the consumer when
ready. Onboarding itself never commits or pushes.

## Use the published development branch

The branch `feat/copier-docs-pipeline` is published. Its initial adoption revision
is `89deb4ab5ad65b7697481d619d4acbcf34ffa67e`. To use that baseline directly:

```bash
docs-onboard /path/to/unadopted-repository \
  --template https://gitlab-master.nvidia.com/nvis-ova/documentation-pipeline.git \
  --vcs-ref 89deb4ab5ad65b7697481d619d4acbcf34ffa67e \
  --ci-ref feat/copier-docs-pipeline \
  --title 'Project Documentation' --source-dir . --dry-run
```

This baseline predates the follow-up fixes in the current working tree. To adopt
those fixes remotely, select their reviewed commit only after it has been
published. For local development use `--template .`; dirty snapshots are suitable
for disposable trials but their temporary commit IDs are not durable update bases.
For lasting adoption use a clean committed template or the Git URL.

Repeating onboarding with the same settings verifies the installed configuration
and reports no changes, preserving consumer formatting, runner overrides, and
curated navigation. It does not upgrade an adoption; use [Copier updates](../how-to/update.md)
for a new template version. Existing settings or shared-reference disagreements
stop the command and direct you to reconcile them with Copier.

A moving CI ref supports development testing; an immutable commit for both refs
makes builds reproducible. Branch/MR child pipelines build artifacts;
default-branch child pipelines also publish Pages. Set Pages access controls
before running a default-branch pipeline. This tutorial itself does not publish.
