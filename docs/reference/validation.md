# Validation record

Validated locally on 2026-10-19, branch `feat/copier-docs-pipeline`: **17 tests passed**, including two real repo_docs builds. Copier emitted two expected dirty-local-template warnings for the development checkout; update tests use committed temporary templates.

```bash
DOCS_BUILD_INTEGRATION=1 .venv/bin/pytest -q
```

The suite covers dry runs, preserving existing CI jobs/includes/comments and
repo.toml/source bytes, collision handling, malformed configuration, path/symlink
escapes, source-specific manual decisions, root source selection, existing
navigation, and Copier updates across two committed template versions. The update
test preserves consumer comments/navigation and checks for rejected patches.

Two integration cases run the real pinned repo_docs package: a minimal repository
and a repository with an existing `verify` pipeline and repo.toml. They verify
HTML output, quoted titles, README directory links, unlabelled code fences, and
unchanged original files. Set `DOCS_BUILD_INTEGRATION=1` to include these network
checks; the default test run skips them. The repository's own CI enables them.

YAML files were parsed locally, and Bash bootstrap scripts passed `bash -n`.
Live GitLab CI Lint, child-pipeline scheduling, token permissions, runner
availability, and Pages delivery have not been tested because no shared ref was
pushed and nothing was published. Validate those on the target GitLab instance
when remote testing is authorized.

## cluster-bringup trial

A disposable copy of the local `nvis-ova/cluster-bringup` checkout was onboarded
with title `Cluster Bringup`, source directory `.`, and the development CI ref.
The dry run discovered **83 Markdown documents** and proposed six paths:

- `.copier-docs-answers.yml`
- `.docs-pipeline/config.toml`
- `.docs-pipeline/ci.yml`
- `.docs-pipeline/navigation.rst`
- `.gitlab-ci.yml`
- `.gitignore`

Its `verify` stage/job remained present. All 83 Markdown files were byte-identical
in the trial after adoption/build. The original checkout remained clean.

The strict repo_docs build found the following adoption decisions:

| Source under consumer root | Decision |
| --- | --- |
| `docs/observability_server_setup/README.md:18` and `explanation.md:3` | `how-to/` has no README/index landing page; add one or link individual guides |
| `docs/observability_server_setup/how-to/troubleshoot.md:25` | `enable-job-submission.md#layer-3-the-pmix-library` is stale; select a current heading |
| `docs/observability_server_setup/how-to/troubleshoot.md:143` | `set-up-clush.md#define-the-sinfo-group-source` is stale; select a current heading |
| `docs/compute_node_ssh_access/how-to/install-ssh-gate-on-one-compute-node.md:156` and `install-ssh-gate-on-the-compute-node-fleet.md:65` | `pam` fences need plain text or a centrally configured lexer |
| `docs/internal_app_access/explanation/architecture-and-trust.md:8` | `mermaid` needs a central rendering extension or a plain-text presentation |
| `docs/internal_app_access/how-to/add-caddy-site.md:15`, `reference/configuration.md:28`, and `tutorial.md:71` | `caddyfile` fences need plain text or a centrally configured lexer |

Warnings are errors, so this trial correctly failed and produced no publishable
site. These source/rendering decisions were left for adoption; no changes were
made in the real consumer. Onboarding reports the known unsupported fence labels
and directory links without landing pages before application. It does not claim
to validate every Markdown link or anchor; the real build provides that check.

Use the consumer's current `perflab` and `size/medium` runner tags in child job
overrides if those remain the intended runners. Confirm the shared project's
job-token allowlist, existing workflow behavior, Pages availability, and access
controls before a remote trial.

## Version availability

The supplied repo_docs `3.1.0` reference pages returned HTTP 403 and the public
Packman registry could not resolve that package version. The implementation pins
and validates `0.39.2`, the version in NVIDIA's public cloud-native-docs manifest.
This is a tested fallback baseline, not a claim of `3.1.0` compatibility. See
[version selection](../explanation/design.md#sources-and-version-selection).
