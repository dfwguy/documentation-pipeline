# Update the existing cluster-bringup integration

The consumer integration is commit `72a01e7` on `feat/documentation-pipeline`.
Its saved template revision is
`89deb4ab5ad65b7697481d619d4acbcf34ffa67e`. It already contains curated navigation,
runner overrides, corrected source links, and an adoption record. Preserve those
files; do not regenerate navigation or copy build/runtime files into the consumer.

## Review the local trial

The follow-up was tested using a committed temporary snapshot of the changed
upstream working tree and a disposable clone of the consumer. Copier updated from
its real saved revision, retaining the existing CI ref. All consumer-owned files
were preserved and the strict build passed. Root and nested pages were also served
at `/` and `/team/project/` in headless Chrome without version-metadata requests.
See the [validation record](../reference/validation.md).

The changes in the upstream working tree are not yet published. Running an update
against the existing remote branch now would select the old implementation. Do not
save a dirty Copier snapshot's temporary SHA as a lasting consumer revision.

For another local trial, first create a reviewed local commit of these upstream
changes on `feat/copier-docs-pipeline` (no push is needed). These workstation
commands use the installed `uv` and the upstream `.venv`; see the README to create
the environment if needed. Then run:

```bash
upstream=/home/micheller/documentation-pipeline
consumer=/home/micheller/cluster-bringup
trial=$(mktemp -d)
fix_ref=$(git -C "$upstream" rev-parse HEAD)
git -C "$upstream" diff --exit-code HEAD -- copier.yml template runtime src ci pyproject.toml
uv pip install --python "$upstream/.venv/bin/python" -e "$upstream"
git -c core.hooksPath=/dev/null clone --no-hardlinks "$consumer" "$trial/consumer"
```

Point only the disposable consumer's saved template source at the local upstream;
keep `_commit` at the version it actually used:

```bash
"$upstream/.venv/bin/python" - "$trial/consumer/.copier-docs-answers.yml" "$upstream" <<'PY'
import sys
from pathlib import Path
from ruamel.yaml import YAML
path = Path(sys.argv[1])
yaml = YAML()
yaml.preserve_quotes = True
answers = yaml.load(path.read_text())
answers['_src_path'] = sys.argv[2]
with path.open('w') as output:
    yaml.dump(answers, output)
PY
git -C "$trial/consumer" -c core.hooksPath=/dev/null \
  -c user.name='Local validation' -c user.email='local-validation@example.invalid' \
  commit -am 'Use local template in disposable trial'
cd "$trial/consumer"
"$upstream/.venv/bin/copier" update --answers-file .copier-docs-answers.yml \
  --vcs-ref "$fix_ref" --data ci_ref=feat/copier-docs-pipeline --defaults --pretend
"$upstream/.venv/bin/copier" update --answers-file .copier-docs-answers.yml \
  --vcs-ref "$fix_ref" --data ci_ref=feat/copier-docs-pipeline --defaults
"$upstream/.venv/bin/docs-onboard" . --template "$upstream" \
  --title 'Cluster Bringup' --source-dir . --ci-ref feat/copier-docs-pipeline --dry-run
python3 "$upstream/runtime/build.py" "$trial/consumer"
git diff --check
git diff -- .copier-docs-answers.yml .docs-pipeline/ci.yml
```

The repeat onboarding report should have `changes: []`. The template adds a
reference-maintenance comment; the local runtime removes the unnecessary version
script. Check both child jobs still have `[perflab, size/medium]`, and the saved CI
ref, `include.ref`, and `DOCS_PIPELINE_REF` all remain `feat/copier-docs-pipeline`.
Navigation, Markdown, scripts, root CI, `.gitignore`, and `ADOPTION.md` should have
no changes. This trial's remote CI would still fetch the currently published
branch; the local build command explicitly exercises the changed runtime.
Do not transfer temporary local source paths into the real integration.

## Update the real integration after publication is separately authorized

Once the reviewed fix commit exists in the remote template repository, set
`fix_ref` to its full 40-character SHA. Run these commands from a clean consumer
checkout on `feat/documentation-pipeline`, using the updated onboarding environment:

```bash
upstream=/home/micheller/documentation-pipeline
cd /home/micheller/cluster-bringup
fix_ref=FULL_SHA_OF_THE_PUBLISHED_FIX_COMMIT
"$upstream/.venv/bin/copier" update --answers-file .copier-docs-answers.yml \
  --vcs-ref "$fix_ref" --data ci_ref=feat/copier-docs-pipeline --defaults --pretend
"$upstream/.venv/bin/copier" update --answers-file .copier-docs-answers.yml \
  --vcs-ref "$fix_ref" --data ci_ref=feat/copier-docs-pipeline --defaults
"$upstream/.venv/bin/docs-onboard" . --title 'Cluster Bringup' --source-dir . \
  --ci-ref feat/copier-docs-pipeline --dry-run
git diff --check
```

Keep `_src_path` as the existing remote URL. Verify `_commit` resolves to
`fix_ref`; Copier may abbreviate it. Review the changes and resolve any conflict
markers or rejected patches before committing the consumer update. No commit,
push, merge, tag, or deployment is performed by the commands above.

Keeping the current CI branch ref exercises the tested update path and retains
inline runner overrides. For an immutable CI/runtime pin, use
`--data ci_ref="$fix_ref"` instead. Changing that last generated variable line can
conflict with the appended runner overrides. If it does, resolve
`.docs-pipeline/ci.yml` to contain `ref: "$fix_ref"` and
`DOCS_PIPELINE_REF: "$fix_ref"`, retain both existing job tag overrides, remove all
conflict markers, and confirm the saved `ci_ref` matches. Do not silently drop the
overrides. This is a documented Copier three-way merge limitation.

## Assess verification status

The original integration's successful GitLab build establishes working access for
that run. Do not treat earlier API HTTP 403 responses as failed CI permissions.
New successful build artifacts will contain `.docs-build/runtime-sha.txt`, also
printed in the log; inspect it to identify the exact runtime commit. Moving refs
can still change between CI configuration resolution and runtime fetch.

Pages publishing, delivery URL/subpaths, access controls, and the old job's exact
runtime SHA remain unverified. A local subpath browser check does not establish a
working GitLab Pages deployment. The existing consumer `ADOPTION.md` is historical;
if updating it later, distinguish the reported successful build from unverified
Pages publishing. No consumer adoption record was changed by this follow-up.
