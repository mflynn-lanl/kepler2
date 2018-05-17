from bs4 import BeautifulSoup
import os
import re
root_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'data')

for root, subdirs, files in os.walk(root_dir):
    print('--\nroot = ' + root)
    list_file_path = os.path.join(root, 'my-directory-list.txt')
    print('list_file_path = ' + list_file_path)

    with open(list_file_path, 'wb') as list_file:
        for subdir in subdirs:
            print('\t- subdirectory ' + subdir)

        for filename in files:
            file_path = os.path.join(root, filename)

            if file_path.endswith('.dat'):
                with open(file_path, 'r') as fp:
                    out_file = file_path.split('.')[0] + '.csv'
                    with open(os.path.join(root, out_file), 'w') as fp2:
                        first_line = True
                        for line in fp:
                            if not first_line:
                                line = re.sub(r"\s+", ',', line.strip()) + '\n'
                            else:
                                first_line = False
                            fp2.write(line)
