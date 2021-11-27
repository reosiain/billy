import sys
from pathlib import Path

from standing_bot.hello import launch_bot

sys.path.append(Path(__file__).parent.parent.__str__())

if __name__ == "__main__":
    launch_bot()
