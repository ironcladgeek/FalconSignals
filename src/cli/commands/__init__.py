"""CLI commands package."""

# Import all commands to register them with the app
from src.cli.commands.analyze import *  # noqa: F401, F403
from src.cli.commands.collect import *  # noqa: F401, F403
from src.cli.commands.config import *  # noqa: F401, F403
from src.cli.commands.download import *  # noqa: F401, F403
from src.cli.commands.journal import *  # noqa: F401, F403
from src.cli.commands.performance import *  # noqa: F401, F403
from src.cli.commands.publish import *  # noqa: F401, F403
from src.cli.commands.report import *  # noqa: F401, F403
from src.cli.commands.utils import *  # noqa: F401, F403
from src.cli.commands.watchlist import *  # noqa: F401, F403
