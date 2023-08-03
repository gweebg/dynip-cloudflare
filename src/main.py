import os

from src.updater import Updater
from src.exceptions import InvalidEnvironmentalVariablesException


def main():

    # Loading variables.

    config: dict[str] = {
        'CLOUDFLARE_TOKEN': os.getenv("CLOUDFLARE_TOKEN"),
        'ZONE_ID': os.getenv("ZONE_ID")
    }

    for value in config.values():
        if value is None:
            raise InvalidEnvironmentalVariablesException("The env variables CLOUDFLARE_TOKEN and ZONE_ID must be set.")

        if value == "changeme":
            raise InvalidEnvironmentalVariablesException("Make sure to change the env variables on the Dockefile.")

    service: Updater = Updater(config=config, key="[update]")  # Todo: Make key an argument for the application.
    service.run()


if __name__ == '__main__':
    SystemExit(main())
