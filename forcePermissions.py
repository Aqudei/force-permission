import os
import yaml
import pwd
import grp
import shutil
from termcolor import colored

START_DIR = './sample'

PERMISSION_FILENAME = '.filePermissions'

cached_permission_file = dict()

# searching for permission file is done by traversing directory upward
# looking for .filePermissions file


def search_for_filepermission(folder):

    files = os.listdir(folder)
    if PERMISSION_FILENAME in files:
        return os.path.join(folder, PERMISSION_FILENAME)
    else:

        head, tail = os.path.split(folder)
        return search_for_filepermission(head)


def read_and_cache_permission_file(permission_file):
    print('Caching permission file: {}'.format(permission_file))
    with open(permission_file, 'rt') as fp:

        filepermission_info = yaml.load(fp)

        cached_permission_file[permission_file] = dict()

        if 'user' in filepermission_info:
            cached_permission_file[permission_file]['user'] = filepermission_info['user']
        else:
            print(colored('No user found in {}'.format(permission_file), 'yellow'))
            cached_permission_file[permission_file]['user'] = None

        if 'group' in filepermission_info:
            cached_permission_file[permission_file]['group'] = filepermission_info['group']
        else:
            print(colored('No group found in {}'.format(permission_file), 'yellow'))
            cached_permission_file[permission_file]['group'] = None

        if 'chmod' in filepermission_info:
            cached_permission_file[permission_file]['chmod'] = int(
                filepermission_info['chmod'], 8)


def get_file_info(filename):
    stats = os.stat(filename)
    return (
        stats.st_mode & 0o777,
        pwd.getpwuid(stats.st_uid).pw_name,
        grp.getgrgid(stats.st_gid).gr_name
    )


if __name__ == "__main__":

    # Root directory MUST have .forcePermission file
    if not PERMISSION_FILENAME in os.listdir(START_DIR):
        print('Root .filePermission file must exist.')
        raise FileNotFoundError()

    # Loop through all files in the directory starting at the deepest level (BOTTOM UP)
    for root, dirs, files in os.walk(START_DIR, topdown=False):

        # See comments for search_for_filepermission()
        permission_file = search_for_filepermission(root)
        if permission_file in cached_permission_file:

            print('Using cached version of {}'.format(
                permission_file))
        else:
            read_and_cache_permission_file(permission_file)

        filepermission_info = cached_permission_file[permission_file]

        using_user = filepermission_info['user']
        using_group = filepermission_info['group']

        using_chmod = filepermission_info.get('chmod')

        print('\nProcessing files inside folder : \'{}\''.format(root))

        for file in files:
            filename = os.path.join(root, file)

            mod, uname, gname = get_file_info(filename)

            if not using_group and not using_user:
                print(colored(
                    "file {} was skipped in chown because the yaml contains invalid user/group".format(filename), 'yellow'))
            else:

                if uname == using_user and gname == using_group:
                    print(colored(
                        "file {} was skipped in chown because file already has correct user/group".format(filename), 'yellow'))
                else:
                    try:
                        print("Using chown on {} with user: {} and group: {}".format(
                            filename, using_user, using_group))
                        shutil.chown(filename, user=using_user,
                                     group=using_group)
                        print(colored(
                            'Success: Chown was executed on file: {}'.format(filename), 'green'))
                    except Exception as e:
                        print(colored(str(e), 'red'))

            if using_chmod:
                if not mod == using_chmod:
                    os.chmod(filename, using_chmod)

        print('\nProcessing directories inside folder : \'{}\''.format(root))

        for folder in dirs:
            if folder in ['.', '..']:
                continue

            folder_name = os.path.join(root, folder)

            mod, uname, gname = get_file_info(folder_name)

            if not using_group and not using_user:
                print(colored(
                    "file {} was skipped in chown because the yaml contains invalid or missing user/group".format(folder_name), 'yellow'))
            else:

                if uname == using_user and gname == using_group:
                    print(colored(
                        "file {} was skipped in chown because file already has correct user/group".format(folder_name), 'yellow'))
                else:
                    try:
                        print("Using chown on {} with user: {} and group: {}".format(
                            folder_name, using_user, using_group))
                        shutil.chown(folder_name, user=using_user,
                                     group=using_group)
                        print(colored(
                            'Success: Chown was executed on file: {}'.format(folder_name), 'green'))
                    except Exception as e:
                        print(colored(str(e), 'red'))

            if using_chmod:
                if not mod == using_chmod:
                    os.chmod(folder_name, using_chmod)

    for d in dirs:
        directory = os.path.join(root, d)
