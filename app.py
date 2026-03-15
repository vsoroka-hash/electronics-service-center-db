import sys

from service_center.cli import main as cli_main
from service_center.gui import main as gui_main


if __name__ == "__main__":
    if "--cli" in sys.argv:
        cli_main()
    else:
        gui_main()
