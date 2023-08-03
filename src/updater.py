import requests
import schedule
import logging
import time
import sys

from datetime import datetime
from typing import Optional

from src.exceptions import RecordDoesNotExistException, RecordNotUpdatedException

# Logger configuration.

root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


class Updater:

    def __init__(self, config: dict[str, str | None], key: str):

        self.config = config
        self.record_key = key

        self.LIST_URL: str = f'https://api.cloudflare.com/client/v4/zones/{config["ZONE_ID"]}/dns_records'
        self.UPDATE_URL: Optional[str] = None
        self.HEADERS: dict = {
            'Authorization': f'Bearer {config["CLOUDFLARE_TOKEN"]}',
            'Content-Type': 'application/json'
        }

        self.current_address: str = self.get_public_address()

    @staticmethod
    def get_public_address():
        """
        :return: Own public IPv4 address as string.
        """
        return requests.get('https://api.ipify.org').content.decode('utf8')

    def get_record_ids(self) -> list[str]:
        """
        Retrieves the ids corresponding to the records that contain `record_key` on its comment.

        :return: List containing the record ids.
        """

        response: requests.Response = requests.get(self.LIST_URL, headers=self.HEADERS)
        result: list[str] = []

        for dns_record in response.json()["result"]:
            if self.record_key in dns_record["comment"]:
                root.info(f"Record {dns_record['id']} matches the comment {self.record_key}")
                result.append(dns_record["id"])

        if len(result) == 0:
            raise RecordDoesNotExistException("Make sure to add a comment on the record that includes `record_id`.")

        return result

    def update_record(self, new_address: str) -> int:
        """
        Given a new public ip address, this function retrieves every record containing the key provided on the constructor
        and updates each record field 'content' to the new address. Also adds a timestamp to the comment for the last
        update.

        Todo: Allow previous comment concatenation on the new record comment.

        :param new_address: New IPv4 address to replace on the DNS record.
        :return: Returns the number of changed records.
        """

        to_change_records: list[str] = self.get_record_ids()

        for record_id in to_change_records:

            self.UPDATE_URL: str = (f'https://api.cloudflare.com/client/v4/zones/'
                                    f'{self.config["ZONE_ID"]}/dns_records/{record_id}')

            current_datetime: str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            data: dict = {'content': new_address, 'comment': f"{self.record_key} [Updated at {current_datetime}]"}

            response: requests.Response = requests.patch(self.UPDATE_URL, headers=self.HEADERS, json=data)

            if len(response.json()["errors"]) > 0:
                root.error("Could not update the error.")
                raise RecordNotUpdatedException(' '.join(response.json()["messages"]))

            root.info(f"Record {record_id} now points to {new_address}")

        return len(to_change_records)

    def check(self) -> None:
        """
        Checks whether the public IPv4 address has changed.
        If it has, then run `update_record()` to update the records.
        If not then just return.

        :return: None
        """

        root.info("Checking for address changes...")

        fetched_address: str = self.get_public_address()
        if fetched_address != self.current_address:

            root.info("Address has updated, trying to update records...")
            self.current_address = fetched_address

            try:
                records_updated: int = self.update_record(fetched_address)
                root.info(f"Successfully updated ({records_updated}) records.")

            except RecordDoesNotExistException as e:
                root.error(f"RecordDoesNotExistException: {str(e)}")

            except RecordNotUpdatedException as e:
                root.error(f"RecordNotUpdatedException: {str(e)}")

            except requests.exceptions.RequestException as e:
                root.error(f"RequestException: {str(e)}")

        else:
            root.info("No changes detected, continuing...")

    def run(self, delta: int = 1):
        """
        Service main loop.
        Uses the `schedule` module to schedule the `check()` method for each minute.

        :param delta: Time interval in minutes between checks. Defaults to 1 minute if nothing is passed.
        :return: None
        """

        root.info("Service started.")
        schedule.every(delta).minutes.do(self.check)

        while True:

            try:
                schedule.run_pending()
                time.sleep(1)

            except KeyboardInterrupt:
                root.info("Shutting down application...")
                return
