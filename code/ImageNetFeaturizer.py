#!/usr/bin/python

import numpy as np
import matplotlib.pyplot as plt
import time
import sys
import subprocess
import glob

# Make sure that caffe is in the python path:

caffe_root = '/home/wilber/work/caffe/'
sys.path.insert(0, caffe_root + 'python')

import os
import caffe


class ImageNetFeaturizer(object):
    """
    Processes images through CaffeNet's pre-trained reference model, and
    returns an array of high-level feature weights.

    o User provides a directory to .preprocess_images() and images are
      re-scaled and stretched to fit into a 256x256 pixel array.

    o A call to .featurize() returns array of feature weights for each of the
      images.
    """

    def __init__(self):
        """
        INPUT: None
        """
        self.X = None		        # n x 4096 ndarray of feature weights
        self.src_dir = None	        # location of images to be processed
        self.src_file_list = None       # list of str, usable files in src_dir
        self.ignored_files = None       # Files not identifiable, ignored
        self.net = None		        # The caffe model itself
        self.trans = None	        # caffe's image transformation object
        print caffe_root

        # Set Caffe to GPU mode:
        caffe.set_device(0)
        caffe.set_mode_gpu()

        self.net = caffe.Net(caffe_root +
                             'models/bvlc_reference_caffenet/'
                             'deploy.prototxt',
                             caffe_root +
                             'models/bvlc_reference_caffenet/'
                             'bvlc_reference_caffenet.caffemodel',
                             caffe.TEST)

        # Input preprocessing: 'data' is the name of the
        # input blob == net.inputs[0]
        data_shape = self.net.blobs['data'].data.shape
        self.trans = caffe.io.Transformer({'data': data_shape})
        self.trans.set_transpose('data', (2, 0, 1))
        # Mean pixel values:
        path_mean = caffe_root + 'python/caffe/imagenet/ilsvrc_2012_mean.npy'
        self.trans.set_mean('data',
                            np.load(path_mean).mean(1).mean(1))

        # The reference model operates on images in [0,255] range instead
        # of [0,1]:
        self.trans.set_raw_scale('data', 255)

        # The reference model has channels in BGR order instead of RGB,
        # so swap:
        self.trans.set_channel_swap('data', (2, 1, 0))
        return

    def preprocess_images(self, src_directory):
        """
        INPUT:
            src_directory	str, location of directory in which source
                                images are located.
        OUTPUT:
            status_string	one of
                                ['OK', 'Cannot process all images; limit 120']
        Calls caffe.Net.reshape() to re-scale images.
        """

        status_string = 'OK'

        self.src_dir = src_directory
        print "src_directory: {0}".format(self.src_dir)

        path_files = glob.glob1(self.src_dir, "*")
        print "path_files:\n", path_files
        print "re-sizing images in {0} ".format(self.src_dir),

        # --------------------------------------------------------------- #
        # Start by testing all files and seeing if they look like images: #
        # --------------------------------------------------------------- #

        self.src_file_list = []
        self.ignored_files = []
        for i, file in enumerate(path_files):
            print "file: {0}".format(file)
            name = ".".join(file.split('.')[:-1])
            suffix = file.split('.')[-1]
            identify_comm = ["identify",
                             "{0}/{1}.{2}".format(self.src_dir, name, suffix)]
            identify = subprocess.Popen(identify_comm, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
            ident_message, ident_error = identify.communicate()
            if '@ error' in ident_error:
                print "\n\t--->\tError identifying {0}. Skipping.".format(name)
                self.ignored_files.append("{0}.{1}".format(name, suffix))
            else:
                self.src_file_list.append("{0}.{1}".format(name, suffix))

        # set net to batch size of file count (maximimum size of 128):
        max_count = 1024
        file_count = min([max_count, len(self.src_file_list)])
        print "file_count: ", file_count
        print "Setting net.blobs['data'] shape ... "
        print type(self.net.blobs['data'])
        self.net.blobs['data'].reshape(file_count, 3, 227, 227)

        print "net.blobs reshaped."

        # Do the ingest/pre-process:
        for i, myfile in enumerate(self.src_file_list):
            if i >= max_count:
                status_format = 'Cannot process all images; limit {0}'
                status_string = status_format.format(max_count)
                break
            path_file = self.src_dir + '/' + myfile
            print "{0}:\t{1}".format(i, path_file)
            image = self.trans.preprocess('data',
                                          caffe.io.load_image(path_file))
            self.net.blobs['data'].data[i] = image

        return status_string

    def featurize(self, fc_level=7):
        """
        INPUT:
            fc_level	int, level at which to extract features, one of
                        [6, 7, 8]; default: 7. * Note that fc_level = 8 returns
                        an array with np.shape()[1] = 1000, rather than 4096! *
        OUTPUT:
            X	ndarray(n_images, 4096) containing high-level feature weights
        Returns array containing weights of high-level features for all
        processed images.
        """

        if fc_level in [6, 7, 8]:
            fc_str = 'fc{0:1d}'.format(fc_level)
        else:
            waah_string = "fc_level: {0}, must be one of [6, 7, 8]. Waaah!'"
            print waah_string.format(fc_level)

        print "Pushing images through the network ..."
        start = time.time()
        self.net.forward()
        print "Done. That took ", time.time() - start, "seconds."

        if fc_level == 8:
            self.X = np.full((len(self.src_file_list), 1000), np.nan)
        else:
            self.X = np.full((len(self.src_file_list), 4096), np.nan)

        for i in range(len(self.src_file_list)):
            self.X[i] = self.net.blobs[fc_str].data[i]

        return self.X


if __name__ == "__main__":

    plt.rcParams['figure.figsize'] = (10, 10)
    plt.rcParams['image.interpolation'] = 'nearest'
    plt.rcParams['image.cmap'] = 'gray'

    if len(sys.argv) > 1:
        source_directory = sys.argv[1]
    else:
        source_directory = '/home/wilber/work/caffe/examples/kitties/img'

    # Make sure that caffe imagnet reference model has been fetched:

    modelPath = 'models/bvlc_reference_caffenet/' \
                + 'bvlc_reference_caffenet.caffemodel'
    if not os.path.isfile(caffe_root + modelPath):
        print("Downloading pre-trained CaffeNet model...")
        shell_command = caffe_root + 'scripts/download_model_binary.py  '
        + caffe_root + 'models/bvlc_reference_caffenet'
        subprocess.call(shell_command)

    myINF = ImageNetFeaturizer()
    myINF.preprocess_images(source_directory)
    X = myINF.featurize(fc_level=6)
    print np.shape(X)
    plt.plot(X[0])
    plt.plot(X[1])
    plt.plot(X[2])
    plt.plot(X[3])
    plt.plot(X[4])
    plt.show()
