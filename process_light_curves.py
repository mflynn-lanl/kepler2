import pandas as pd
import numpy as np
import os
from collections import OrderedDict
import argparse
from scipy import interpolate, fftpack


def calc_rotation_period(k2):
    f = interpolate.interp1d(k2['time'], k2['flux'])
    x_data_new = np.arange(k2['time'].min(), k2['time'].max(), .02)
    y_data_new = f(x_data_new)
    dt = x_data_new[1] - x_data_new[0]
    X = fftpack.fft(y_data_new)
    freqs = fftpack.fftfreq(len(y_data_new)) * 1/dt
    abs_x = np.abs(X)
    mags = abs_x[np.where(freqs > 0)]
    pos_freqs = freqs[np.where(freqs > 0)]
    ind = np.argpartition(mags, -2)[-2:]
    oscillation_strength = mags[ind].max()/mags[ind].min()
    return pos_freqs[np.argmax(mags)], oscillation_strength

def calc_derivative(k2):
    """
    :param file_path: path to file
    :return: numpy array of first derivatives
    """

    d1 = np.zeros(len(k2['time']))
    dt = np.zeros(len(k2['time']))
    it = np.nditer(k2['flux'], flags=['c_index'])
    while not it.finished:
        if it.index < len(k2['flux']) - 1:
            dt[it.index] = k2['time'][it.index + 1] - k2['time'][it.index]
            d1[it.index] = (k2['flux'][it.index + 1] - k2['flux'][it.index]) / (k2['time'][it.index + 1] - k2['time'][it.index])

        it.iternext()
    return d1


def calculate_num_flares_derivative(k2, n_std_dev):
    """

    :param filename: file with light curve
    :param file_path: path to file
    :param n_std_dev: number of standard deviations to use for threshold
    :param num_flares: number of flares detected in light curve
    :param star_type: type of star
    :param name: name of star
    :param dir_name: name of directory
    :return: number of flares
    """

    d1 = calc_derivative(k2)
    pos_threshold = n_std_dev * np.std(d1[d1 > 0]) + np.mean(d1[d1 > 0])
    neg_threshold = -np.std(d1[d1 < 0]) + np.mean(d1[d1 < 0])
    d1_thresh = np.concatenate((np.where(d1>pos_threshold)[0], np.where(d1<neg_threshold)[0]))
    indices = np.sort(d1_thresh)
    it = np.nditer(indices, flags=['c_index'])
    flair_count = 0
    above_thresh = False
    while not it.finished:
        if (it.index < len(indices) - 1) and (indices[it.index + 1] - indices[it.index] > 1) and not above_thresh:
            above_thresh = True
            print indices[it.index]
            flair_count += 1
        else:
            above_thresh = False
        it.iternext()
    return flair_count


def calculate_num_flares(k2, n_std_dev, N):
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

    thresh_value = np.mean(k2['flux']) + n_std_dev * np.std(k2['flux'])
    threshold_array = np.convolve(k2['flux'], np.ones((N,)) / N, mode='full') + thresh_value
    flare_array = np.zeros(len(k2['flux']))
    for index in range(len(k2['flux'])):
        if k2['flux'][index] > threshold_array[index]:
            flare_array[index] = k2['flux'][index]
    flare_count = len(flare_array[flare_array > 0])
    return flare_count


def get_metadata(file_path, filename, teff_list, logg_list, feh_list, rad_list, mass_list, lum_list, kp_list, jm_list, hm_list, km_list,num_flares, name, dir_name, star_type, flare_count, max_freq,
                 rotation_freq, osc_strength, oscillation_ratio):
    with open(os.path.join('/'.join(file_path.split('/')[:6]),filename.split('.')[0]+'.info')) as fp:
        lines = fp.readlines()
        teff_list.append(lines[1].split(',')[1])
        logg_list.append(lines[1].split(',')[2])
        feh_list.append(lines[1].split(',')[3])
        rad_list.append(lines[1].split(',')[4])
        mass_list.append(lines[1].split(',')[5])
        lum_list.append(lines[1].split(',')[6])
        kp_list.append(lines[1].split(',')[7])
        jm_list.append(lines[1].split(',')[8])
        hm_list.append(lines[1].split(',')[9])
        km_list.append(lines[1].split(',')[10])
    num_flares.append(flare_count)
    name.append(filename.split('.')[0])
    dir_name.append(file_path.split('/')[4])
    star_type.append(file_path.split('/')[5])
    rotation_freq.append(max_freq)
    oscillation_ratio.append(osc_strength)
    print(file_path, flare_count)
    return num_flares, name, dir_name, star_type, rotation_freq, oscillation_ratio

def process_curves(n_std_dev, N, mdwarf_list, root_dir):
    """
    Traverses directory structure to process light curve csv files
    :param n_std_dev:
    :param N:
    :param mdwarf_list: List of M-dwarf stars
    :param root_dir: root data directory
    :return:
    """
    num_flares, star_type,name, dir_name, teff_list, rotation_freq, oscillation_ratio = [], [], [], [], [], [], []
    logg_list, feh_list, rad_list, mass_list, lum_list, kp_list, jm_list, hm_list, km_list = [],[],[],[],[],[],[],[],[]

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
                            k2 = pd.read_csv(file_path)
                            k2.columns = ['time', 'flux', 'error']
                            k2.reset_index(drop=True)
                            flare_count = calculate_num_flares_derivative(k2, n_std_dev)
                            max_freq, osc_strength = calc_rotation_period(k2)
                            num_flares, name, dir_name, star_type, rotation_freq, oscillation_ratio = \
                                get_metadata(file_path, filename, teff_list, logg_list, feh_list, rad_list, mass_list, lum_list, kp_list, jm_list, hm_list, km_list, num_flares, name, dir_name, star_type,
                                             flare_count, max_freq, rotation_freq, osc_strength, oscillation_ratio)
    flare_dict = OrderedDict([('dirname', dir_name),
                              ('startype', star_type),
                              ('name', name),
                              ('numflares', num_flares),
                              ('teff', teff_list),
                              ('logg', logg_list),
                              ('feh', feh_list),
                              ('rad', rad_list),
                              ('lum', lum_list),
                              ('kp', kp_list),
                              ('jm', jm_list),
                              ('hm', hm_list),
                              ('km', km_list),
                              ('rotation_freq', rotation_freq),
                              ('oscillation_ratio', oscillation_ratio)
                              ])
    flare_df = pd.DataFrame.from_dict(flare_dict)
    flare_df.to_csv('mdwarf_flares_{0}_freqs_oscillation.csv'.format(n_std_dev))


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--std_dev", required=False)
    parser.add_argument("-N", "--window_size", required=False)
    parser.add_argument("-l", "--star_list", required=False)
    args = parser.parse_args()


    n_std_dev = float(args.std_dev) if args.star_list else 1.5
    N = int(args.window_size) if args.window_size else 10
    mdwarf_list = pd.read_csv(args.star_list, header=0) if args.star_list else pd.read_csv(os.path.join(os.path.dirname(__file__),
                                                                                            'mdwarfs_list.csv'))

    # convert integers to strings
    mdwarf_list = mdwarf_list['mdwarf_star'].apply(str)
    root_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'C4', 'COOL')
    process_curves(n_std_dev,N, mdwarf_list, root_dir)