import os
from pprint import pprint

from googleapiclient.errors import HttpError

import gdsync
import gdsync.google.backup
from gdsync.config import Config


class Merge:
    def __init__(self):
        self.backup = gdsync.google.backup.Backup()
        self.backup.callback = self._print

        self.config = Config()

    def merge(self):
        try:
            self._merge_all()
        except HttpError as error:
            self._error(error)

    def _error(self, error):
        print(error.uri)
        pprint(error.resp)
        raise error

    def _merge(self, src_id):
        backup = self.backup
        drive = backup.drive

        src_res = drive.open(src_id)
        dest_res = drive.open(self.config['merge']['destination_id'])

        dest_folder = dest_res.create_folder(src_res.name)
        backup.merge(src_res, dest_folder)

    def _merge_all(self):
        for src_id in self.config['merge']['source_ids']:
            self._merge(src_id)

    def _print(self, src_item, folder_name, state=''):
        name = os.path.join(folder_name, src_item.name)
        if src_item.is_folder():
            name += '/'

        print('%s: %s' % (state, name))


def main():
    Merge().merge()