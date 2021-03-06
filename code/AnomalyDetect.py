#!/usr/bin/python

# import cv2
import os
import glob
import iForest as isof
import subprocess
import numpy as np
import time
from collections import OrderedDict


class AnomalyDetect(object):
    '''
    Uses the Isolation Forest method to detect anomalies in photos.
    '''

    def __init__(self, show_calc_time=True, use_color=True,
                 n_estimators=60,
                 max_depth=40,
                 src_dir='/home/wilber/work/Galvanize/gcp-data/iForest/tmp',
                 proc_dir='/home/wilber/work/Galvanize/gcp/app/static'):

        # place to temporarily store processed user images:
        self.proc_dir = proc_dir

        # where images originate:
        self.src_dir = src_dir
        self.src_file_list = []			# list of file names therein
        self.proc_file_list = []		# list of processed file names

        self.use_color = use_color		# treat images as color not B&W
        self.n_estimators = n_estimators        # number of iTrees to construct
        self.show_calc_time = show_calc_time
        self.X = None
        self.max_depth = max_depth
        return

    def process_files(self, src_dir):
        '''
        INPUT:
            src_dir	location of raw files uploaded by user
        OUTPUT:
            None
        Converts images into 100 x 100 thumbnails, stuffs results into
        self.src_dir. Images are first made to be 100 x n or n x 100, for
        n >= 100, followed by cropping to 100 x 100. Extreme aspect ratio
        source images will have bad results!

        !!! This is more-or-less obsolete, as the ImageNetFeaturizer	!!!
        !!! class now will resize/stretch images to fit 256x256 pixels.	!!!
        !!! Retaining this for cases when wish to apply iForest to raw	!!!
        !!! pixels.							!!!
        '''

        self.src_dir = src_dir
        path_files = glob.glob1(self.src_dir, "*")

        fileCt = len(path_files)
        print "re-sizing images in {0} ".format(self.src_dir),
        self.proc_file_list = []

        sizeFit = "100x100^"
        sizeCrop = "100x100"
        # sizeFit = "256x256^"
        # sizeCrop = "256x256"
        if self.use_color:
            print "\nColor: True\n"
        else:
            print "\nColor: False\n"
        for i, file in enumerate(path_files):
            # if i % 10 == 0:
            #     print '.',
            print "file: {0}".format(file)
            name = ".".join(file.split('.')[:-1])
            suffix = file.split('.')[-1]
            if self.use_color:
                conv_comm = ["convert",
                             "{0}/{1}.{2}".format(self.src_dir, name, suffix),
                             "-resize", sizeFit, "-set",
                             # "-colorspace", "sRGB",  "-gravity",
                             "-colorspace", "RGB",
                             "-gravity", "center", "-extent", sizeCrop,
                             "{0}/{1}.png".format(self.proc_dir, name)]
            else:
                conv_comm = ["convert",
                             "{0}/{1}.{2}".format(self.src_dir, name, suffix),
                             "-channel", "RGBA", "-matte",
                             "-colorspace", "gray",
                             "-resize", sizeFit,
                             "-gravity", "center", "-extent", sizeCrop,
                             "{0}/{1}.png".format(self.proc_dir, name)]
                print " ".join(conv_comm)
            convert = subprocess.Popen(conv_comm, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            conv_message, conv_error = convert.communicate()
#           if ('@ warning' in conv_message or '@ error' in conv_message):
            if '@ error' in conv_error:
                print "\n\t--->\tError converting {0}. Skipping.".format(name)
            else:
                self.src_file_list.append("{0}.{1}".format(name, suffix))
                self.proc_file_list.append("{0}.png".format(name))

        lenStrang = "\nlen(self.proc_file_list): {0}\n"
        print lenStrang.format(len(self.proc_file_list))

        return

    def load_files(self, proc_dir=None):
        """
        INPUT:
            proc_dir	str, location of pre-processed files.

        OUTPUT: None
        Takes 100x100 pixel images and loads them into self.X

        !!! This is more-or-less obsolete, as the ImageNetFeaturizer	!!!
        !!! class now will resize/stretch images to fit 256x256 pixels.	!!!
        !!! Retaining this for cases when wish to apply iForest to raw	!!!
        !!! pixels.							!!!
        """
        # if proc_dir != None:
        if proc_dir is not None:
            self.proc_dir = proc_dir

        path_files = glob.glob1(self.proc_dir, "*.png")
        fileCt = len(path_files)
        print "\npath_files:\n", path_files, "\n"

        if self.use_color:
            Xraw = np.full((fileCt, 30000), np.nan)
        else:
            Xraw = np.full((fileCt, 10000), np.nan)

        for i, file in enumerate(path_files):
            if self.use_color:
                img = cv2.imread(self.proc_dir + '/' + file)
            else:
                img = cv2.imread(self.proc_dir + '/' + file,
                                 cv2.IMREAD_GRAYSCALE)

            if i % 100 == 0:
                print "{0}\t{1}\t{2}".format(i, file, type(img))
            print file
            if self.use_color:
                if len(img.flatten()) == 30000:
                    Xraw[i, :] = img.flatten()
                    self.proc_file_list.append(file)
            else:
                if len(img.flatten()) == 10000:
                    Xraw[i, :] = img.flatten()
                    self.proc_file_list.append(file)
        print Xraw.shape
        self.X = Xraw
        print self.proc_file_list[:10]

        print "Exiting .load_files()."
        return

    def fit(self, X=None):
        """
        INPUT:
            X		X, n x p features variable. Will use values from
                        .load_files() step (in self.X), if not supplied here.
        OUTPUT: None
        With data in self.X, this calls the Isolation Forest model to obtain
        anomaly scores.
        """

        # if X != None:
        if X is not None:
            self.X = X

        self.iFmodel = isof.iForest(n_estimators=self.n_estimators,
                                    max_depth=self.max_depth)

        if self.show_calc_time:
            print "Constructing iTrees ..."
            start = time.time()

        self.iFmodel.fit(self.X)

        if self.show_calc_time:
            totsecs = time.time() - start
            mins = int(totsecs/60)
            secs = totsecs - 60.0*mins
            print "Elapsed time = {0} minutes, {1} seconds".format(mins, secs)
        return

    def show_top_k(self, k):
        '''
        INPUT:
            k			number of top anomaly scores to show
        OUTPUT:
            dict		key: file_order, value: (file_name, anom_score)
        This is to accommodate kludge needed to interact with Flask.
        Return k, anomaly scores and corresponding file names in ranked order.
        '''

        anom_scores = self.iFmodel.anomaly_score_
        sort_indices = np.argsort(anom_scores)
        print "\nk: {0}".format(k)
        cryStr = "Only {0} anomaly scores returned by model. " \
                 + "Cannot return {1}."
        nScores = len(anom_scores)
        if k > nScores:
            print cryStr.format(nScores, k)
            k = nScores
        print ""

        top_k = OrderedDict()
        for i in range(1, k + 1):
            ind = sort_indices[-i]
            print i, " ",
            print sort_indices[-i], " ",
            print self.proc_file_list[ind], " ",
            print anom_scores[ind]
            top_k[str(i)] = (ind, self.proc_file_list[ind],
                             anom_scores[ind])

        return top_k

    def show_top_k_ori(self, k, files_to_display=None):
        '''
        INPUT:
            k			number of top anomaly scores to show
            files_to_display	list, files for which you want scores no
                                matter the anomaly score.
        OUTPUT:
            None
        List k files and anomaly scores in ranked order.
        '''

        anom_scores = self.iFmodel.anomaly_score_
        sort_indices = np.argsort(anom_scores)
        print "\nk: {0}".format(k)
        cryStr = "Only {0} anomaly scores returned by model. " \
                 + "Cannot return {1}."
        nScores = len(anom_scores)
        if k > nScores:
            print cryStr.format(nScores, k)
            k = nScores
        print ""

        top_k = []
        for i in range(1, k + 1):
            ind = sort_indices[-i]
            print i, " ",
            print sort_indices[-i], " ",
            print self.proc_file_list[ind], " ",
            print anom_scores[ind]
            top_k.append((str(i), self.proc_file_list[ind],
                          str(anom_scores[ind])))

        # if files_to_display == None:
        if files_to_display is None:
            return top_k
        else:
            my_files = []
            for i in range(1, len(self.src_file_list)):
                ind = sort_indices[-i]
                if names[ind] in files_to_display:
                    my_files.append(((str(i), str(names[ind]),
                                     str(anom_scores[ind]))))
            return top_k, my_files


if __name__ == '__main__':
    myModel = AnomalyDetect()
    myModel.process_files()
    myModel.load_files()
    myModel.fit()
    myModel.show_top_k(10)
