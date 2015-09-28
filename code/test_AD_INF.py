import numpy as np
import ImageNetFeaturizer as inf
import AnomalyDetect as ad

source_directory = '/home/wilber/work/caffe/examples/kitties/img'
myINF = inf.ImageNetFeaturizer()
myINF.preprocess_images(source_directory)
X = myINF.featurize(fc_level = 7)
print np.shape(X)

myAD = ad.AnomalyDetect()
myAD.X = X
myAD.proc_files_list = myINF.src_file_list
myAD.fit()
myAD.show_top_k(10)
