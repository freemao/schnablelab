import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
import numpy as np
from scipy.stats import linregress

def GenDataFrameFromPath(path, pattern='*.png'):
    """
    generate a dataframe for all file in a dir with the specific pattern of file name.
    use: GenDataFrameFromPath(path, pattern='*.png')
    """
    fnpaths = list(path.glob(pattern))
    df = pd.DataFrame(dict(zip(['fnpath'], [fnpaths])))
    df['fn'] = df['fnpath'].apply(lambda x: x.name)
    return df

def ConciseVcf(fn):
    """
    concise the vcf file by remove the header, useless columns and simplfied genotype
    ConciseVcf(fn)
    """
    n = 0
    f = open(fn)
    for i in f:
        if i.startswith('##'):
            n += 1
        else:
            break
    df = pd.read_csv(fn, header=n, delim_whitespace=True)
    df = df.drop(['INFO', 'FORMAT', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER'], axis=1)
    for idx in df.columns[2:]:
        df[idx] = df[idx].map(lambda x: x.split(':')[0])
    df = df.replace(['0/0', '0/1', '1/0', '1/1', './.'], [0, 1, 1, 2, 9])
    return df
            
class SimpleStats(object):
    """
    This class will do the simple statistics on two series objecjts.
    a) linear regressoin: slope, intercept, r^2, p_value
    b) mean, std of the difference and absolute differnece
    c) MSE (mean squared error) and RMSE (root mean squared error)
    d) agreement
    e) plot the regreesion figure and the difference distribution figure
    """
    def __init__(self, series1, series2):
        self.s1 = series1
        self.s2 = series2
        self.length = series1.shape[0]
        self.diff = series1 - series2
        self.absdiff = (series1 - series2).abs()

    def regression(self):
        slope, intercept, r_value, p_value, __ = linregress(self.s1, self.s2)
        return slope, intercept, r_value**2, p_value

    def mean_std_diff(self):
        mean, std = self.diff.mean(), self.diff.std()
        return mean, std

    def mean_std_absdiff(self):
        abs_mean, abs_std = self.absdiff.mean(), self.absdiff.std()
        return abs_mean, abs_std

    def mse(self):
        mse = mean_squared_error(self.s1, self.s2)
        return mse

    def rmse(self):
        rmse = mean_squared_error(self.s1, self.s2)**0.5
        return rmse
    
    def agreement(self, cutoff):
        return (self.absdiff<=float(cutoff)).sum()/self.length
































