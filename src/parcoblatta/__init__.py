from importlib import resources
from pathlib import Path

ROOT_PATH = Path(__file__).parents[2]
PACKAGE_PATH = Path(str(resources.files(__name__)))
QUERIES_PATH = PACKAGE_PATH / "queries"
TEMPLATES_PATH = PACKAGE_PATH / "templates"

