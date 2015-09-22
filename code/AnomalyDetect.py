#!/usr/bin/python

import cv2
import os
import glob
import iForest as isof
import subprocess
import numpy as np
import time

class AnomalyDetect(object):
    '''
    Uses the Isolation Forest method to detect anomalies in photos (nominally).
    '''

    def __init__(self, show_calc_time = True, use_color = True,
                 n_estimators = 200,
                 src_dir = '/home/wilber/work/Galvanize/gcp-data/iForest/tmp',
                 proc_dir = '/home/wilber/work/Galvanize/gcp/app/static'):

        # place to temporarily store processed user images:
        self.proc_dir = proc_dir

        # where images originate:
        self.src_dir = src_dir
        self.src_file_list = []			# list of file names therein
        self.proc_file_list = []		# list of processed file names

        self.use_color = use_color		# treat images as color not B&W
        self.n_estimators = n_estimators	# number of iTrees to construct
        self.show_calc_time = show_calc_time
        self.X = None

    def process_files(self, src_dir):
        '''
        INPUT:
            src_dir	location of raw files uploaded by user
        OUTPUT:
            None
        Converts images into 100 x 100 thumbnails, stuffs results into
        self.src_dir. Images are first made to be 100 x n or n x 100, for
        n >= 100, followed by cropping to 100 x 100. Extreme aspect ratio source
        images will have bad results!
        '''

        self.src_dir = src_dir
        path_files = glob.glob1(self.src_dir, "*")

        fileCt = len(path_files)
        print "re-sizing images in {0} ".format(self.src_dir),
        self.proc_file_list = []

        if self.use_color:
            print "\nColor: True\n"
        else:
            print "\nColor: False\n"
        for i, file in enumerate(path_files):
#           if i % 10 == 0:
#               print '.',
            print "file: {0}".format(file)
            name = ".".join(file.split('.')[:-1])
            suffix = file.split('.')[-1]
            if self.use_color:
                conv_comm = ["convert",
                             "{0}/{1}.{2}".format(self.src_dir, name, suffix),
                             "-resize", "100x100^", "-set",
                             # "-colorspace", "sRGB",  "-gravity",
                             "-colorspace", "RGB",
                             "-gravity", "center", "-extent", "100x100",
                             "{0}/{1}.png".format(self.proc_dir, name)]
                pass
            else:
                conv_comm = ["convert",
                             "{0}/{1}.{2}".format(self.src_dir, name, suffix),
                             "-channel", "RGBA", "-matte",
                             "-colorspace", "gray", 
                             "-resize", "100x100^",
                             "-gravity", "center", "-extent", "100x100",
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

        print "\nlen(self.proc_file_list): {0}\n".format(len(self.proc_file_list))

    def load_files(self, proc_dir = None):

        if proc_dir != None:
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
                    Xraw[i,:] = img.flatten()
                    self.proc_file_list.append(file)
            else:
                if len(img.flatten()) == 10000:
                    Xraw[i,:] = img.flatten()
                    self.proc_file_list.append(file)
        print Xraw.shape
        self.X = Xraw
        print self.proc_file_list[:10]

        print "Exiting .load_files()."


    def fit(self):
        self.model = isof.iForest(n_estimators=self.n_estimators,
                                  max_depth = 100)

        if self.show_calc_time:
            print "Constructing iTrees ..."
            start = time.time()

        self.model.fit(self.X)

        if self.show_calc_time:
            totsecs = time.time() - start
            mins = int(totsecs/60)
            secs = totsecs - 60.*mins
            print "Elapsed time = {0} minutes, {1} seconds".format(mins, secs)


    def show_top_k(self, k, files_to_display=None):
        '''
        INPUT:
            k			number of top anomaly scores to show
            files_to_display	list, files for which you want scores no
				matter the anomaly score.
        OUTPUT:
            None
        List k files and anomaly scores in ranked order.
        '''

        anom_scores = self.model.anomaly_score_
        sort_indices = np.argsort(anom_scores)
        print "\nk: {0}".format(k)
        cryStr = "Only {0} anomaly scores returned by model. Cannot return {1}."
        nScores = len(anom_scores)
        if k > nScores:
            print cryStr.format(nScores, k)
            k = nScores
        print ""

        print self.proc_file_list, "\n"
        print "# files in self.proc_file_list: {0}".format(len(self.proc_file_list))
        top_k = []
        for i in range(1, k + 1):
            ind = sort_indices[-i]
            print i, " ",
            print sort_indices[-i], " "
            print self.proc_file_list[ind], " ",
            print anom_scores[ind]
            top_k.append((str(i), self.proc_file_list[ind],
                          str(anom_scores[ind])))

        if files_to_display == None:
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