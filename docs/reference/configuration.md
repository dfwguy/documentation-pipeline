# Configuration and command reference

## Copier answers

| Answer | Default | Meaning |
| --- | --- | --- |
| `docs_title` | Project documentation | Display title |
| `docs_source_dir` | `docs` | Existing source directory, relative to consumer root; `.` supported |
| `docs_nav` | `.docs-pipeline/navigation.rst` | Navigation file relative to consumer root; entries relative to source directory |
| `ci_project` | `nvis-ova/documentation-pipeline` | Shared GitLab project on the consumer's GitLab server |
| `ci_ref` | `feat/copier-docs-pipeline` | Ref for both CI include and runtime checkout |

The repository-root `copier.yml` is versioned with the template. Saved answers
include Copier's `_src_path` and `_commit` plus all project answers. Commit
`.copier-docs-answers.yml`. The template contains no executable Copier tasks.

Copier owns `.docs-pipeline/config.toml` and `.docs-pipeline/ci.yml`. Onboarding
creates the initial navigation, adds a `docs:pipeline` trigger to root CI, and
adds `/.docs-build/` to `.gitignore`. Navigation is consumer maintained.
Direct `copier copy` renders settings but does not inspect or integrate existing
repositories; use `docs-onboard` for adoption.

## Onboarding CLI

```text
docs-onboard REPOSITORY --title TITLE
  [--source-dir docs] [--nav .docs-pipeline/navigation.rst]
  [--template PATH_OR_GIT_URL] [--vcs-ref HEAD]
  [--ci-project nvis-ova/documentation-pipeline]
  [--ci-ref feat/copier-docs-pipeline] [--dry-run] [--report FILE]
```

Python 3.11+ and Git are required. The default template URL is
`https://gitlab-master.nvidia.com/nvis-ova/documentation-pipeline.git`.
`--vcs-ref` selects the Copier template version; `--ci-ref` independently selects
the shared CI/runtime version. Supply both explicitly for production adoption.

The command prints JSON findings, changed paths, manual decisions, and unified
diffs. Exit `0` means the plan was generated/applied; `2` means inspection or a
conflict requires intervention. Dry run never writes to the consumer unless
`--report` explicitly names a file there. Template fetching may use network and
Copier caches. Inspection conflicts stop all planned writes; filesystem failures
during application can leave partial writes, so review from a clean checkout.

CI is parsed with round-trip YAML. Existing jobs, includes, comments, stages,
workflow, and defaults are preserved semantically. Formatting can change. TOML
is parsed but never rewritten. Existing Pages jobs, conflicting managed paths,
duplicate Markdown/RST stems, and conflicting `docs:pipeline` jobs block adoption.
Unresolved remote includes are reported for manual inspection. Custom CI config
paths configured in GitLab project settings are not discoverable locally; integrate
the generated trigger into that actual entry point manually.

## Shared CI contract

`/ci/docs.gitlab-ci.yml` defines `docs:build`, `.build-docs`, `.docs-rules`, and
`pages`. Consumers pin it using `include:project` with a literal `ref` in their
child config. The generated variables `DOCS_PIPELINE_PROJECT` and
`DOCS_PIPELINE_REF` must match that include.

The root `docs:pipeline` job uses the last existing stage (or standard `test`)
and waits for its child via `strategy: depend`. It runs for branch and MR
pipelines, avoiding duplicate branch jobs when an MR is open. Existing workflow
rules remain authoritative. The child has independent `build` and `deploy`
stages. Defaults from other root jobs do not affect these jobs.

Build artifacts are `.docs-build/site/`, retained for one week. The conventional
`pages` job copies them to `public/` and publishes only on the default branch.
This uses the longstanding GitLab Pages job convention rather than newer
`pages.publish` syntax. Tags do not publish; MR and other branch builds retain
artifacts without changing Pages. An existing Pages configuration requires a
manual migration decision.

Requirements: a Linux Docker-capable runner, outbound access to this GitLab
server, Ubuntu package mirrors, NVIDIA Packman/CloudFront/bootstrap services,
and Python package services. The shared private project must allow inbound
`CI_JOB_TOKEN` access from the consumer (or its group), and the pipeline user
must have permission to read it. Git uses a credential helper with the ephemeral
job token; no token is stored in the remote URL or generated consumer files.
Use GitLab CI Lint against the target server after the ref exists. Confirm Pages
is enabled and set its access controls before publishing internal documentation.

## Runtime

`python3 runtime/build.py /path/to/consumer` requires Python 3.11+, Bash, and curl.
It reads `.docs-pipeline/config.toml`, copies the selected source to a temporary
workspace under `.docs-build/`, invokes repo_docs, then copies HTML to
`.docs-build/site/`. Existing repo-tool setup and `repo.toml` are isolated.

Hidden paths, `_build`, `_repo`, `node_modules`, and `__pycache__` are excluded
from the snapshot. Included symlinks require manual review and stop the build.
Paths must stay inside the consumer; `_pipeline_index` is reserved for the
staged navigation. Links outside the selected source tree need a broader source
directory. Assets inside the source tree are copied; HTML use is subject to
Sphinx's normal asset handling. Failed builds fail CI and do not publish.
Warnings remain errors. Directory links resolve to README/index pages centrally;
unlabelled code fences use plain text.

Pinned dependencies: Copier `9.19.1`, repo_man `1.86.0`, repo_docs `0.39.2`,
Sphinx package `4.5.0.2-py3.10-${platform}`, Packman `7.5`, and its Python
`3.10.5-1`. See [validation](validation.md) for the repo_docs version constraint.
