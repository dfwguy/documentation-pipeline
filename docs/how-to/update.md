# Update an adopted consumer

Use a clean consumer working tree with committed `.copier-docs-answers.yml`.
Install the onboarding package's pinned Copier version in your maintenance
environment. Run updates from the consumer root:

```bash
copier update --answers-file .copier-docs-answers.yml \
  --vcs-ref <template-tag-or-commit> --pretend
copier update --answers-file .copier-docs-answers.yml \
  --vcs-ref <template-tag-or-commit>
```

Review the resulting diff and resolve any Copier conflict markers or `.rej` files.
Commit answers together with changed managed files. Copier maintains the files in
`template/`; the root CI trigger, ignore rule, and navigation are adoption edits,
so updates do not replace them. Add newly written documents to navigation yourself.
Do not rerun onboarding to update an adopted repository.

To change the shared build/publishing version as well, pass the new ref as an answer:

```bash
copier update --answers-file .copier-docs-answers.yml \
  --vcs-ref <template-ref> --data ci_ref=<shared-ci-ref>
```

Both the `include:project` ref and runtime checkout ref are generated from
`ci_ref`. Use a SHA or tag for reproducibility. A moving branch is useful for
testing but can change between CI config resolution and runtime checkout.

# Test template development locally

Use a separate consumer copy, a committed template checkout, and `--template
/path/to/documentation-pipeline --vcs-ref HEAD`. Make another template commit,
commit the consumer adoption, then use `copier update --answers-file
.copier-docs-answers.yml --vcs-ref HEAD` in the consumer. No tags are necessary.
A local template path in saved answers is only portable to machines with that
path; use the repository Git URL for lasting adoption.

# Reuse existing navigation

Pass `--nav docs/index.rst` (or another repository-relative `.rst` file) during
adoption. Existing navigation is preserved; entries must be relative to the
selected source directory as expected by Sphinx. Missing navigation is generated
from discovered documents. For Markdown landing pages, keep that Markdown and
reference it from the generated reStructuredText navigation.

# Configure a runner

Add a local override in `.docs-pipeline/ci.yml`, for example for cluster-bringup's
current runners:

```yaml
docs:build:
  tags: [perflab, size/medium]
pages:
  tags: [perflab, size/medium]
```

Use runners that can run the configured Linux container image. Parent pipeline
defaults do not propagate into this child pipeline.
