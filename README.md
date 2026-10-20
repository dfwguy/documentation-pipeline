# Documentation pipeline

Build Markdown in an existing repository with NVIDIA repo_docs and publish through
GitLab Pages. Copier manages a small consumer configuration; the build runtime and
publishing jobs live here. Documentation source stays in the consumer repository.

- [Tutorial: adopt the pipeline](docs/tutorials/adopt.md)
- [How-to: update a consumer or test a development ref](docs/how-to/update.md)
- [Reference: configuration, commands, and CI contract](docs/reference/configuration.md)
- [Explanation: ownership and design](docs/explanation/design.md)
- [Validation and known limits](docs/reference/validation.md)

`nvis-ova/cluster-bringup` has adopted the published `feat/copier-docs-pipeline`
branch at `89deb4ab5ad65b7697481d619d4acbcf34ffa67e`. Its successful GitLab build
confirms that the configured runner and package access worked for that run.
Pages publishing remains unverified. The follow-up changes in this checkout are
local until separately committed and published; the existing remote ref does not
contain them. See [updating the existing integration](docs/how-to/update-cluster-bringup.md).

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
