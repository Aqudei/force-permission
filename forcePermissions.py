import os
import yaml
import pwd
import grp
import shutil
from termcolor import colored

START_DIR = './sample'

PERMISSION_FILENAME = '.filePermissions'


class PermissionSetter(object):

    cached_permission_file = dict()

    def __init__(self):
        pass

    # searching for permission file is done by traversing directory upward
    # looking for .filePermissions file

    def _locate_permission_file(self, folder):

        files = os.listdir(folder)
        if PERMISSION_FILENAME in files:
            return os.path.join(folder, PERMISSION_FILENAME)
        else:

            head, tail = os.path.split(folder)
            return self._locate_permission_file(head)

    def _read_and_cache_permission_file(self, permission_file):

        if permission_file in self.cached_permission_file:
            print('Using cached copy of {}'.format(permission_file))
            return self.cached_permission_file[permission_file]

        print('Caching permission file: {}'.format(permission_file))

        with open(permission_file, 'rt') as fp:

            filepermission_info = yaml.load(fp)

            self.cached_permission_file[permission_file] = dict()

            if 'user' in filepermission_info:
                self.cached_permission_file[permission_file]['user'] = filepermission_info['user']
            else:
                print(colored('No user found in {}'.format(
                    permission_file), 'yellow'))
                self.cached_permission_file[permission_file]['user'] = None

            if 'group' in filepermission_info:
                self.cached_permission_file[permission_file]['group'] = filepermission_info['group']
            else:
                print(colored('No group found in {}'.format(
                    permission_file), 'yellow'))
                self.cached_permission_file[permission_file]['group'] = None

            if 'chmod' in filepermission_info:
                self.cached_permission_file[permission_file]['chmod'] = int(str(
                    filepermission_info['chmod']), 8)

            return self.cached_permission_file[permission_file]

    def _get_file_folder_info(self, filename):
        stats = os.stat(filename)
        return (
            stats.st_mode & 0o777,
            pwd.getpwuid(stats.st_uid).pw_name,
            grp.getgrgid(stats.st_gid).gr_name
        )

    def _process_folders_only(self, dirs):
        for folder_name in dirs:
            if folder_name in ['.', '..']:
                continue

            print('Processing directory: {}'.format(folder_name))
            permission_file = self._locate_permission_file(folder_name)
            filepermission_info = self._read_and_cache_permission_file(
                permission_file)

            mod, uname, gname = self._get_file_folder_info(folder_name)
            using_group = filepermission_info.get('group')
            using_user = filepermission_info.get('user')
            using_chmod = filepermission_info.get('chmod')

            if not using_group and not using_user:
                print(colored(
                    "Folder with name {} was skipped in chown because the yaml contains invalid or missing user/group".format(folder_name), 'yellow'))
            else:

                if uname == using_user and gname == using_group:
                    print(colored(
                        "Folder with name {} was skipped in chown because it already has correct user/group".format(folder_name), 'yellow'))
                else:
                    try:
                        print("Appyling chown on folder {} with user: {} and group: {} from permission file {}".format(
                            folder_name, using_user, using_group, permission_file))
                        shutil.chown(folder_name, user=using_user,
                                     group=using_group)
                        print(colored(
                            'Success: Chown was executed on folder: {}'.format(folder_name), 'green'))
                    except Exception as e:
                        print(colored(str(e), 'red'))

            if using_chmod:
                if not mod == using_chmod:
                    print('Appyling chmod: {} to folder: {}'.format(
                        oct(using_chmod), folder_name))
                    os.chmod(folder_name, using_chmod)

    def process_root(self, start_dir):

        # Loop through all files in the directory starting at the deepest level (BOTTOM UP)
        for root, dirs, files in os.walk(START_DIR, topdown=False):

            # See comments for search_for_filepermission()
            permission_file = self._locate_permission_file(root)

            filepermission_info = self._read_and_cache_permission_file(
                permission_file)

            using_user = filepermission_info['user']
            using_group = filepermission_info['group']
            using_chmod = filepermission_info.get('chmod')

            for file_ in files:
                print('\nProcessing file {}.'.format(file_))

                filename = os.path.join(root, file_)

                mod, uname, gname = self._get_file_folder_info(filename)

                if not using_group and not using_user:
                    print(colored(
                        "file {} was skipped in chown because the yaml contains invalid user/group".format(filename), 'yellow'))
                else:

                    if uname == using_user and gname == using_group:
                        print(colored(
                            "file {} was skipped in chown because file already has correct user/group".format(filename), 'yellow'))
                    else:
                        try:
                            print("Applying chown on file {} with user: {} and group: {} from permission file {}.".format(
                                filename, using_user, using_group, permission_file))
                            shutil.chown(filename, user=using_user,
                                         group=using_group)
                            print(colored(
                                'Success: Chown was executed on file: {}'.format(filename), 'green'))
                        except Exception as e:
                            print(colored(str(e), 'red'))

                if using_chmod:
                    if not mod == using_chmod:
                        print('Appyling chmod: {} to file: {}'.format(
                            oct(using_chmod), filename))
                        os.chmod(filename, using_chmod)

            self._process_folders_only([os.path.join(root, d) for d in dirs])


if __name__ == "__main__":

    # Root directory MUST have .forcePermission file
    if not PERMISSION_FILENAME in os.listdir(START_DIR):
        print('Root .filePermission file must exist.')
        raise FileNotFoundError()

    permission_setter = PermissionSetter()
    permission_setter.process_root(START_DIR)
