import os
import yaml
import pwd
import grp

START_DIR = './sample'

PERMISSION_FILENAME = '.filePermissions'


# searching for permission file is done by traversing directory upward
# looking for .filePermissions file
def search_for_filepermission(folder):

    files = os.listdir(folder)
    if PERMISSION_FILENAME in files:
        return os.path.join(folder, PERMISSION_FILENAME)
    else:

        head, tail = os.path.split(folder)
        return search_for_filepermission(head)


if __name__ == "__main__":

    # Root directory MUST have .forcePermission file
    if not PERMISSION_FILENAME in os.listdir(START_DIR):
        raise FileNotFoundError()

    # Loop through all files in the directory starting at the deepest level (BOTTOM UP)
    for root, dirs, files in os.walk(START_DIR, topdown=False):

        # See comments for search_for_filepermission()
        permission_file = search_for_filepermission(root)

        with open(permission_file, 'rt') as fp:
            filepermission_info = yaml.load(fp)
            latest_user_value = filepermission_info['user']
            latest_group_value = filepermission_info['group']

        print('Processing files inside folder : \'{}\''.format(root))
        for f in files:
            if f == PERMISSION_FILENAME:
                # We ignore permission file
                continue

            filename = os.path.join(root, f)
            try:
                uid = pwd.getpwnam(latest_user_value).pw_uid
                gid = grp.getgrnam(latest_group_value).gr_gid
                os.chown(filename, uid, gid)
            except KeyError as ex:
                print(
                    'User: {} or Group: {} not found'.format(latest_user_value, latest_group_value))
