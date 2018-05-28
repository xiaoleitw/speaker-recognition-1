#!/usr/bin/env python
'''
provides functionality to manage audio data.
creates h5 file and labels mapping file from 
voxforge dataset.
converts wav files to filterbank energies matrix.
'''
__author__ = "Sophia Zheng, Rish Gupta, and Manish Pandit"

import os
import h5py
import json
import operator
import numpy as np
import keras as K
import matplotlib.pyplot as plt
from scipy import signal
import scipy.io.wavfile as wav
from python_speech_features import mfcc
from python_speech_features import logfbank
from config import raw_data_dir, data_dir, data_file, labels_file
from config import model_dir, model_file, model_params, max_pad_len
from encoder import LabelEncoder

def parse_label(dir):
    ''' parse speaker label from file path '''
    i = dir.find('-')
    if i == -1:
        return None
    return dir[:i]

def wav2fbank(file_path, max_pad_len):
    ''' convert wav file to filterbank energies matrix '''
    (rate,sig) = wav.read(file_path)
    fbank_feat = logfbank(sig,rate)
    fbank_feat = fbank_feat[:max_pad_len, :]
    pad_width = max_pad_len - fbank_feat.shape[0]
    fbank_feat = np.pad(fbank_feat, pad_width = ((0, pad_width), (0, 0)), mode = 'constant')
    return fbank_feat

def data_from_files():
    encoder = LabelEncoder()
    fbank_vectors = []
    label_vectors = []
    
    # walk the data dir looking for wav file
    for dirpath, dirnames, filenames in os.walk(raw_data_dir):
        for filename in [f for f in filenames if f.endswith(".wav")]:
            # get mfcc matrix for this file
            mfcc = wav2fbank(os.path.join(dirpath, filename), max_pad_len)
            # get label for this file
            label = parse_label(os.path.relpath(dirpath, raw_data_dir))
            label_id = encoder.add(label)
            # add mfcc
            fbank_vectors.append(mfcc)
            # add label
            label_vectors.append(label_id)
       
    # create numpy array for X and Y
    X_All = np.array(fbank_vectors)
    Y_All = np.array(label_vectors)
   
    # save labels file
    encoder.save()

    # random shuffle dataset
    # we need each instance of X in 3 dimensional for CNN so reshape X
    # X is now a 4D matrix
    # convert Y to one hot encoding
    permutation = np.random.permutation(X_All.shape[0])
    X_All = X_All[permutation].reshape(X_All.shape[0], X_All.shape[1], X_All.shape[2], 1)
    Y_All = Y_All[permutation].reshape(Y_All.shape[0], -1)
    Y_All = K.utils.to_categorical(Y_All)

    # split the dataset into train, dev and test sets (90%, 5%, 5% approx)
    m = X_All.shape[0]
    idx_train = int(m * 0.9)
    idx_dev = int(m * 0.95)
    # train
    X_Train = X_All[:idx_train]
    Y_Train = Y_All[:idx_train]
    # dev
    X_Dev = X_All[idx_train:idx_dev]
    Y_Dev = Y_All[idx_train:idx_dev]
    # test
    X_Test = X_All[idx_dev:]
    Y_Test = Y_All[idx_dev:]

    return X_Train, Y_Train, X_Dev, Y_Dev, X_Test, Y_Test

def create_h5_file():
    ''' 
    create h5 file with train, dev and test datasets.
    create labels mapping file.
    '''
    
    # read the raw data dir and get sets
    X_Train, Y_Train, X_Dev, Y_Dev, X_Test, Y_Test = data_from_files()

    # store the datasets to h5 file
    if not os.path.exists(os.path.dirname(data_file)):
        os.makedirs(os.path.dirname(data_file))
    f = h5py.File(data_file, 'w')
    f.create_dataset('X_Train', data=X_Train)
    f.create_dataset('Y_Train', data=Y_Train)
    f.create_dataset('X_Dev', data=X_Dev)
    f.create_dataset('Y_Dev', data=Y_Dev)
    f.create_dataset('X_Test', data=X_Test)
    f.create_dataset('Y_Test', data=Y_Test)
    f.close()    
    
def get_data(X_Set, Y_Set):
    ''' 
    get dataset by name.
    X_Set and Y_Set are name of the dataset
    returns numpy array of dataset stored in
    h5 file
    '''
    if not os.path.exists(data_file):
        create_h5_file()

    f = h5py.File(data_file, 'r')
    return f[X_Set], f[Y_Set]

def get_train_data():
    ''' 
    get training dataset.
    returns numpy array of dataset stored in h5 file.
    '''
    return get_data("X_Train", "Y_Train")

def get_dev_data():
    ''' 
    get dev dataset.
    returns numpy array of dataset stored in h5 file.
    '''
    return get_data("X_Dev", "Y_Dev")

def get_test_data():
    ''' 
    get test dataset.
    returns numpy array of dataset stored in h5 file.
    '''
    return get_data("X_Test", "Y_Test")

def main():

    create_h5_file()
    X, Y = get_train_data()
    print("X_Train, Y_Train shape:", X.shape, Y.shape)
    X, Y = get_dev_data()
    print("X_Dev, Y_Dev shape:", X.shape, Y.shape)
    X, Y = get_test_data()
    print("X_Test, Y_Test shape:", X.shape, Y.shape)

if __name__ == '__main__':
    main()
