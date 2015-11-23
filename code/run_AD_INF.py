#!/usr/bin/python


# Simple script to test workings of caffe with AnomDetect.py and iForest.py. #


import numpy as np
import ImageNetFeaturizer as inf
import AnomalyDetect as ad

IMAGE_SRC_FOLDER = '/home/wilber/work/Galvanize/gcp-data/iForest/tiger'

INFmodel = inf.ImageNetFeaturizer()
print "status: ", INFmodel.preprocess_images(IMAGE_SRC_FOLDER)
X = INFmodel.featurize(fc_level = 6)
print np.shape(X)

ADmodel = ad.AnomalyDetect()
ADmodel.X = X
ADmodel.proc_file_list = INFmodel.src_file_list
ADmodel.fit()
print ADmodel.iFmodel.anomaly_score_
print ""
ADmodel.show_top_k(10)
