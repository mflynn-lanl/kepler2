import pandas as pd
import numpy as np
import os
from collections import OrderedDict
import argparse


def calculate_num_flares(filename, file_path, n_std_dev, N, num_flares, star_type, name, dir_name, teff_list):
    """
    Calculates the number of flares in a light curve based on a threshold n_std_dev above a rolling average
    :param filename: file with light curve
    :param file_path: path to file
    :param n_std_dev: number of standard deviations to use for threshold
    :param N: window size for average
    :param num_flares: number of flares detected in light curve
    :param star_type: type of star
    :param name: name of star
    :param dir_name: name of directory
    :return: cumulative lists of number of flares, star names, directory names, star types
    """
    k2 = pd.read_csv(file_path)
    k2.columns = ['time', 'flux', 'error']
    k2.reset_index(drop=True)
    thresh_value = np.mean(k2['flux']) + n_std_dev * np.std(k2['flux'])
    threshold_array = np.convolve(k2['flux'], np.ones((N,)) / N, mode='full') + thresh_value
    flare_array = np.zeros(len(k2['flux']))
    for index in range(len(k2['flux'])):
        if k2['flux'][index] > threshold_array[index]:
            flare_array[index] = k2['flux'][index]
    flare_count = len(flare_array[flare_array > 0])
    with open(os.path.join('/'.join(file_path.split('/')[:6]),filename.split('.')[0]+'.info')) as fp:
        lines = fp.readlines()
        teff_list.append(lines[1].split(',')[1])
    num_flares.append(flare_count)
    name.append(filename.split('.')[0])
    dir_name.append(file_path.split('/')[4])
    star_type.append(file_path.split('/')[5])
    print(file_path, flare_count)
    # return num_flares, name, dir_name, star_type


def process_curves(n_std_dev, N, mdwarf_list, root_dir):
    """
    Traverses directory structure to process light curve csv files
    :param n_std_dev:
    :param N:
    :param mdwarf_list: List of M-dwarf stars
    :param root_dir: root data directory
    :return:
    """
    num_flares = []
    star_type = []
    name = []
    dir_name = []
    teff_list = []
    print('processing..............')
    #traverse file directory
    for root, subdirs, files in os.walk(root_dir):
        print('--\nroot = ' + root)
        list_file_path = os.path.join(root, 'my-directory-list.txt')

        with open(list_file_path, 'wb') as list_file:
            for filename in files:
                file_path = os.path.join(root, filename)
                if file_path.endswith('.csv'):
                    # is this an mdwarf star?
                    if len(mdwarf_list[mdwarf_list.str.contains(filename.split('.')[0])]) > 0:
                        with open(file_path, 'r') as fp:
                            # num_flares, name, dir_name, star_type =
                            calculate_num_flares(filename, file_path, n_std_dev, N, num_flares, star_type, name, dir_name, teff_list)

    flare_dict = OrderedDict([('dirname', dir_name),
                              ('startype', star_type),
                              ('name', name),
                              ('numflares', num_flares),
                              ('teff', teff_list)
                              ])
    flare_df = pd.DataFrame.from_dict(flare_dict)
    flare_df.to_csv('mdwarf_flares_new.csv')


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--std_dev", action='store_true')
    parser.add_argument("-N", "--window_size", action='store_true')
    parser.add_argument("-l", "--star_list", action='store_true')
    args = parser.parse_args()


    n_std_dev = float(args.std_dev) if args.star_list else 1.5
    N = int(args.window_size) if args.window_size else 10
    mdwarf_list = pd.read_csv(args.star_list, header=0) if args.star_list else pd.read_csv(os.path.join(os.path.dirname(__file__),
                                                                                            'mdwarfs_list.csv'))

    # convert integers to strings
    mdwarf_list = mdwarf_list['mdwarf_star'].apply(str)
    root_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'C4', 'COOL')
    process_curves(n_std_dev,N, mdwarf_list, root_dir)