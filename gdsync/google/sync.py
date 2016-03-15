from dateutil import parser
import os

from gdsync.google.drive import Drive, Resource
from gdsync.google.finished_folders import FinishedFolders

FinishedFolders.db_file_name = 'backup.db'


class Sync:
    def __init__(self, src, dest, config_dir=None, sync_id=None):
        self.callback = print_none
        self.drive = Drive(config_dir=config_dir)

        self.src = self._init_resource(src)
        self.dest = self._init_resource(dest)

        self.sync_id = sync_id

        self.finished_folders = None

    def sync(self):
        if self.sync_id:
            self.finished_folders = FinishedFolders(self.dest.id)
            self.finished_folders.load()

        self._sync(self.src, self.dest, '')
        return self

    def _init_resource(self, res):
        if isinstance(res, Resource):
            return self.drive.open(res.id)
        elif isinstance(res, str):
            return self.drive.open(res)
        else:
            raise ValueError('Value must be Resource object or resource id')

    def _sync(self, src_res, dest_res, folder_name):
        folder_name = os.path.join(folder_name, dest_res.name)

        for src_item in src_res.list():
            self._sync_item(src_item, dest_res, folder_name)

    def _sync_item(self, src_item, dest_res, folder_name):
        if src_item.is_folder():
            self._sync_folder(src_item, dest_res, folder_name)
        elif src_item.is_app():
            pass
        else:
            self._sync_file(src_item, dest_res, folder_name)

    def _sync_folder(self, src_item, dest_res, folder_name):
        if self.finished_folders is not None and src_item.id in self.finished_folders:
            self.callback(src_item, folder_name, state='skip')
            return

        dest_folder = dest_res.find_folder(src_item.name)
        if not dest_folder:
            dest_folder = dest_res.create_folder(src_item.name)

        self.callback(src_item, folder_name, state='folder')
        self._sync(src_item, dest_folder, folder_name)

        if self.finished_folders is not None:
            self.finished_folders.add(src_item.id)
            self.finished_folders.save()

    def _sync_file(self, src_item, dest_res, folder_name):
        dest_file = dest_res.find(src_item.name, mime_type=src_item.mimeType)
        if not dest_file:
            self.callback(src_item, folder_name, state='new')
            src_item.copy_to(dest_res)
        elif parser.parse(dest_file.createdTime) < parser.parse(src_item.modifiedTime):
            self.callback(src_item, folder_name, state='update')
            dest_file.delete()
            src_item.copy_to(dest_res)
        else:
            self.callback(src_item, folder_name, state='skip')


def print_none(src_item, folder_name, state=''):
    pass