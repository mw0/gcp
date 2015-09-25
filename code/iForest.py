import numpy as np
import sklearn as sk
import matplotlib.pyplot as plt
import pandas as pd


def _h(i):
    return np.log(i) + 0.5772156649 


def _c(n):
    if n > 2:
        h = _h(n-1)
        return 2*h - 2*(n - 1)/n
    if n == 2:
        return 1
    else:
        return 0


def _anomaly_score(score, n_samples):

    score = -score/_c(n_samples)

    return 2**score


def _split_data(X):
    ''' split the data in the left and right nodes ''' 
    n_samples, n_columns = X.shape
    n_features = n_columns - 1
    m = M = 0
    while m == M:
        feature_id = np.random.randint(low=0, high=n_features)
        feature = X[:, feature_id]
        m = feature.min()
        M = feature.max()
        #print(m, M, feature_id, X.shape)

    split_value = np.random.uniform(m, M, 1)
    lefties = feature <= split_value
    if np.count_nonzero(lefties) == 0 or  np.count_nonzero(~lefties) == 0:
        print "np.count_nonzero(lefties): {0}, np.count_nonzero(~lefties)".format(np.count_nonzero(lefties),  np.count_nonzero(~lefties))
    left_X = X[lefties]
    right_X = X[~lefties]
    # print "{0}, {1}".format(len(left_X), len(right_X))
    return left_X, right_X, feature_id, split_value


def iTree(X, add_index=False, max_depth = np.inf):            
    ''' construct an isolation tree and returns the number of steps required
    to isolate an element. A column of index is added to the input matrix X if  
    add_index=True. This column is required in the algorithm. ''' 

    n_split = {} 
    def iterate(X, count = 0):

        n_samples, n_columns = X.shape
        n_features = n_columns - 1

        if count > max_depth:
            for index in X[:,-1]:
                n_split[index] = count
            return

        if n_samples == 1:
            index = X[0, n_columns-1]
            n_split[index] = count
            return 
        else:
            lX, rX, feature_id, split_value = _split_data(X)
            # Uncomment the print to visualize a draft of 
            # the construction of the tree
            # print(lX[:,-1], rX[:,-1], feature_id, split_value, n_split, count)
            n_samples_lX, _ = lX.shape
            n_samples_rX, _ = rX.shape
            if n_samples_lX > 0:
                iterate(lX, count+1)
            if n_samples_rX >0:
                iterate(rX, count+1)
            if n_samples_lX == 0 and n_samples_rX == 0:
                return

    if add_index:
        n_samples, _ = X.shape
        X = np.c_[X, range(n_samples)]

    iterate(X)
    return n_split


class iForest():
    ''' Class to construct the isolation forest.

    -n_estimators: is the number of trees in the forest,

    -sample_size: is the bootstrap parameter used during the construction
    of the forest,

    -add_index: adds a column of index to the matrix X. This is required and 
    add_index can be set to False only if the last column of X contains 
    already indices.

    -max_depth: is the maximum depth of each tree
    '''
    def __init__(self, n_estimators=20, sample_size=None, add_index = True, 
                 max_depth = 100):
        self.n_estimators = n_estimators
        self.sample_size = sample_size
        self.add_index = add_index
        self.max_depth = max_depth
        return


    def fit(self, X):
        print "Entering iForest.fit() ..."
        n_samples, n_features = X.shape
        if self.sample_size == None:
            self.sample_size = int(n_samples/2)

        if self.add_index:
            X = np.c_[X, range(n_samples)]


#       trees = [iTree(X[np.random.choice(n_samples, 
#                                         self.sample_size, 
#                                         replace=False)],
#                      max_depth=self.max_depth) 
#                for i in range(self.n_estimators)]

        print "About to construct all them trees."
        trees = []
        for i in range(self.n_estimators):
            print ".",
            trees.append(iTree(X[np.random.choice(n_samples,
                                                  self.sample_size, 
                                                  replace=False)],
                               max_depth=self.max_depth))
        print ""

        self.path_length_ = {k:None for k in range(n_samples)}
        for k in self.path_length_.keys():
            self.path_length_[k] = np.array([tree[k] 
                                             for tree in trees 
                                             if k in tree])

        self.path_length_ = np.array([self.path_length_[k].mean() for k in 
                                      self.path_length_.keys()])
        self.anomaly_score_ = _anomaly_score(self.path_length_, self.sample_size)
        return self
