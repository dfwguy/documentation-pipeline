# Documentation pipeline

Build Markdown in an existing repository with NVIDIA repo_docs and publish through
GitLab Pages. Copier manages a small consumer configuration; the build runtime and
publishing jobs live here. Documentation source stays in the consumer repository.

- [Tutorial: adopt the pipeline](docs/tutorials/adopt.md)
- [How-to: update a consumer or test a development ref](docs/how-to/update.md)
- [Reference: configuration, commands, and CI contract](docs/reference/configuration.md)
- [Explanation: ownership and design](docs/explanation/design.md)
- [Validation and known limits](docs/reference/validation.md)

The first intended consumer is `nvis-ova/cluster-bringup`. This implementation is
local development work on `feat/copier-docs-pipeline`; no release tag or shared
GitLab ref has been published yet. Use local template copies for testing now.

Python 3.11+ and Git are required for onboarding. Linux, Bash, curl, and network
access to NVIDIA Packman and Python package services are required for builds.

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
.venv/bin/pytest -q
```

Documentation follows [Diátaxis](https://diataxis.fr/): tutorials teach adoption,
how-to guides cover maintenance tasks, reference describes contracts, and
explanation covers design choices.
