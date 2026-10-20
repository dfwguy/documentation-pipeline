"""Load pinned repo tools; the consumer's repo.toml is never loaded or edited."""
import sys
from pathlib import Path

import packmanapi

runtime = Path(__file__).resolve().parents[1]
for dependency in packmanapi.pull(str(runtime / "repoman/repo-deps.packman.xml")).values():
    sys.path.insert(0, dependency)

import omni.repo.man

omni.repo.man.main(str(Path(sys.argv.pop(1)).resolve()))
