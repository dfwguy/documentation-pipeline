# Why the pipeline has two layers

Copier records a versioned adoption contract: project title, source location,
navigation location, shared CI project, and shared ref. Consumer repositories own
those values and their documentation. The central repository owns fetching repo
tools, building a site, adapting repository-style links, and publishing Pages.
This keeps fixes reusable without copying build scripts into each consumer.

A GitLab child pipeline gives documentation independent stages without replacing
an application's stage list. The root integration is a small trigger job; its
child includes the central YAML at a chosen Git ref. It also checks out the runtime
from that ref because GitLab YAML includes do not fetch executable files. A
release should pin immutable refs; a development branch supports integration
experiments. Template and runtime refs can evolve independently, and maintainers
should review both when upgrading.

The build uses an isolated source snapshot because repo_docs writes temporary
configuration and generated content. It never imports a consumer's existing
repo.toml or repo-tool extensions. This avoids accidentally invoking application
build behavior or replacing existing tool dependencies. Existing repo_docs users
must reconcile any custom extensions or build options explicitly.

Navigation starts as a deterministic inventory. Existing documentation is not
moved or rewritten to impose a new information architecture. The pipeline's own
documentation uses the four reader needs described by
[Diátaxis](https://diataxis.fr/); consumers can retain their established structure.

Only GitLab Pages publishing is implemented. Future destinations can add central
publishing jobs without changing where source documents live.

# Sources and version selection

The requested [repo_docs 3.1.0 quickstart](http://omniverse-docs.s3-website-us-east-1.amazonaws.com/repo_docs/3.1.0/quickstart.html)
and [how it works](http://omniverse-docs.s3-website-us-east-1.amazonaws.com/repo_docs/3.1.0/how-it-works.html)
returned HTTP 403 during implementation. Public Packman could not resolve
`repo_docs@3.1.0` either. Its configuration has not been claimed as verified.

The working baseline follows NVIDIA's public
[cloud-native-docs dependency manifest](https://github.com/NVIDIA/cloud-native-docs/blob/ca002206c61c3372d0ddc5ad8888afd200faa0f1/deps/repo-deps.packman.xml)
which pins repo_docs `0.39.2`. The downloaded package's configuration and code
were inspected and real builds verified against it. A future move to `3.1.0`
requires access to the official package and documentation, a compatible bootstrap,
and build validation before changing the central dependency manifest.

Copier's [template and saved answers documentation](https://copier.readthedocs.io/en/stable/)
and [update workflow](https://copier.readthedocs.io/en/stable/updating/)
inform the adoption/update contract. GitLab's
[CI YAML reference](https://docs.gitlab.com/ci/yaml/) describes includes, child
pipelines, and Pages. The target self-managed instance still needs live CI Lint
and a pipeline run after maintainers publish the shared ref.
