#!/usr/bin/python


# Simple script to test workings of caffe with AnomDetect.py and iForest.py. #


import numpy as np
import ImageNetFeaturizer as inf
import AnomalyDetect as ad

#PROCESSED_FOLDER = '/home/wilber/work/Galvanize/gcp-data/iForest/cat'
#PROCESSED_FOLDER = '/home/wilber/work/caffe/examples/kitties/img'
#PROCESSED_FOLDER = '/home/wilber/work/Galvanize/gcp-data/iForest/pizza'
#PROCESSED_FOLDER = '/home/wilber/work/Galvanize/gcp-data/iForest/tiger'
PROCESSED_FOLDER = '/home/wilber/work/Galvanize/gcp/app/static'
#PROCESSED_FOLDER = '/home/wilber/work/Galvanize/gcp-data/iForest/loonie'
#PROCESSED_FOLDER = '/home/wilber/work/Galvanize/gcp-data/iForest/suburban_homes'

INFmodel = inf.ImageNetFeaturizer()
print "status: ", INFmodel.preprocess_images(PROCESSED_FOLDER)
#X = INFmodel.featurize(fc_level = 7)
X = INFmodel.featurize(fc_level = 6)
print np.shape(X)

ADmodel = ad.AnomalyDetect()
ADmodel.X = X
ADmodel.proc_file_list = INFmodel.src_file_list
ADmodel.fit()
print ADmodel.iFmodel.anomaly_score_
print ""
ADmodel.show_top_k(10)
