# Validation record

## Follow-up integration validation (2026-10-20)

The fixes are local to `feat/copier-docs-pipeline`; **42 tests passed**, including
two real repo_docs fixture builds. Six expected dirty-local-template warnings
occurred in disposable current-template trials; update trials used committed
temporary templates. Nothing was pushed, merged, tagged, or deployed during this
follow-up.

```bash
DOCS_BUILD_INTEGRATION=1 .venv/bin/pytest -q
```

Focused coverage includes CommonMark fences nested in lists and block quotes,
tilde fences and false-positive code examples, initial adoption with existing CI,
repeat onboarding with byte-identical consumer files, inconsistent-reference
rejection, and Copier updates from the actual `89deb4a` template contents. Updates
preserve runner overrides, consumer configuration comments, curated navigation,
root CI, source files, and adoption notes. A separate reference-change case checks
saved answers, the shared include, and runtime ref remain aligned.

CI rule tables cover default branches with different names, non-default branches,
MR/tag contexts, non-child sources, and parent branch/MR deduplication. These are
local expression checks, not a replacement for the target GitLab scheduler.
The Pages job still requires the successful build artifact and only runs in a
default-branch child pipeline. Its publication rules were not broadened.

Two fixtures build real repo_docs HTML. Every generated HTML page is checked for
removal of `version.js`, while retaining other renderer scripts. The shared CI
now records the fetched runtime SHA in the job log and build artifact; no previous
run's SHA has been inferred from a moving branch.

### Trials against the actual consumer revisions

A disposable pre-integration snapshot at `3b46a55` was dry-run inspected, adopted,
and inspected again. Existing verification and source bytes were preserved; the
second onboarding run made no changes. The updated parser reports the indented
`caddyfile` fence in `docs/internal_app_access/how-to/add-caddy-site.md:15`, which
the earlier scanner missed.

A disposable clone of the current consumer at `72a01e7` was updated using Copier
from its saved full `89deb4ab5ad65b7697481d619d4acbcf34ffa67e` revision to a committed
temporary snapshot of the upstream changes, retaining the existing CI branch ref.
Only the saved template revision/source (temporary local source for the trial)
and the generated CI maintenance comment changed. All **93 consumer-owned files**
remained byte-identical, including both runner overrides, curated navigation,
root CI, Markdown, scripts, and `ADOPTION.md`. No conflict/reject files appeared.
Repeat onboarding returned `changes: []`, and the strict build passed.

Headless Chrome loaded four pages: root and nested pages both at `/` and under
`/team/project/`. The local HTTP server recorded **80 requests, zero version
metadata requests, and zero asset errors**. This reproduces the browser behavior
behind the metadata defect and verifies the corrected artifact without deploying.

### Remaining limits

The supplied integration findings report a successful GitLab build at the
published baseline. That establishes working runner, include, runtime-fetch, and
package access for that run; earlier API 403 responses are not evidence of broken
CI permissions. The old job's exact runtime SHA/logs and formal allowlist/settings
were not independently inspected here.

Actual Pages publication, delivery URLs and access controls remain untested. No
live pipeline was launched for these local changes. Cold-cache package downloads
and other runner environments were not revalidated. Tests exercise the installed
pinned renderer using available package caches.

The renderer still lacks PAM, Caddyfile, and Mermaid fence support. Source fixes
and curated navigation belong to the consumer. Copier can require manual conflict
resolution if a CI ref change touches the last generated line next to appended
consumer overrides; same-ref upgrades and overrides were verified automatically.
Follow the [existing-integration update instructions](../how-to/update-cluster-bringup.md).

## Historical pre-integration trial (2026-10-19)

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
site. These source/rendering decisions were left for adoption at the time. The subsequent
consumer integration addressed them; this table records the earlier trial. Onboarding reports the known unsupported fence labels
and directory links without landing pages before application. It does not claim
to validate every Markdown link or anchor; the real build provides that check.

The subsequent integration uses `perflab` and `size/medium` runner overrides.

## Version availability

The supplied repo_docs `3.1.0` reference pages returned HTTP 403 and the public
Packman registry could not resolve that package version. The implementation pins
and validates `0.39.2`, the version in NVIDIA's public cloud-native-docs manifest.
This is a tested fallback baseline, not a claim of `3.1.0` compatibility. See
[version selection](../explanation/design.md#sources-and-version-selection).
