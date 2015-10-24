import numpy as np
import time
import sys
import subprocess
import os
import glob

import AnomalyDetect as ad
from flask import Flask, render_template
import flask
from werkzeug import secure_filename

# This replaces app.py, which attempted to use the ImageNetFeaturizer class.
# Flask would not cooperate with that, and the current version inserts caffe
# calls directly. This is not only uglier, unfortunately, but also has some
# extra overhead. A fix is forthcoming, although a low-priority.

# Make sure that caffe imagnet reference model has been fetched:

app = Flask(__name__)

app.config.from_pyfile('../.config/settings.cfg')

cpath = app.config['CAFFE_ROOT']
cpath += 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel'

if not os.path.isfile(cpath):
    print("Downloading pre-trained CaffeNet model...")
    shell_command = (app.config['CAFFE_ROOT'] +
                     'scripts/download_model_binary.py  ' +
                     app.config['CAFFE_ROOT'] +
                     'models/bvlc_reference_caffenet')
    print "shell_command: ", shell_command
    subprocess.call(shell_command)

sys.path.insert(0, app.config['CAFFE_ROOT'] + 'python')
import caffe


# CAFFE_ROOT = '/home/wilber/work/caffe/'
# BACKGROUND_IMG = 'white128x128.png'
# UPLOAD_FOLDER = '/home/wilber/work/Galvanize/gcp-data/iForest/tmp'
# VALIDATED_FOLDER = '/home/wilber/work/Galvanize/gcp/app/static'
# BCKGND_FOLDER = '/home/wilber/work/Galvanize/gcp-data/iForest/'

# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['VALIDATED_FOLDER'] = VALIDATED_FOLDER

# app.config['ALLOWED_EXTENSIONS'] = set(['PNG', 'JPG', 'JPEG',
#                                         'png', 'jpg', 'jpeg'])


@app.route('/', methods=["GET", "POST"])
def index():
    '''
    This is the welcome page. A simple messagge and a couple of buttons to
    push to get started.
    '''

    return render_template('home.html')


@app.route('/provided_images', methods=["GET", "POST"])
def provided_images():
    return render_template('Pre-processedResults.html')


@app.route('/mostly_tigers', methods=["GET", "POST"])
def mostly_tigers():
    return render_template('MostlyTigers.html')


@app.route('/anomalous_tigers', methods=["GET", "POST"])
def anomalous_tigers():
    return render_template('AnomalousTigers.html')


@app.route('/upload_form', methods=["GET", "POST"])
def upload_form():
    '''
    A simple form permitting users to select a local directory, and files
    within, for upload.
    '''

    # Clean out the upload folder before fetching new files.
    os.system('rm {0}/*'.format(app.config['UPLOAD_FOLDER']))

    return render_template('UploadFiles.html')


# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


@app.route('/upload_process', methods=["GET", "POST"])
def upload_process():

    print "\nupload_process()\n"

    print "Requesting uploaded files list."
    uploaded_files = flask.request.files.getlist("file[]")
    print "uploaded_files:\n", uploaded_files

    bad_guys = 0
    bad_list = []
    for i, file in enumerate(uploaded_files):
        # print file.filename.encode('utf-8', 'ignore')
        print file.filename.encode('utf-8')
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            bad_guys += 1
            bad_list.append([str(i + 1),
                             file.filename.encode('utf-8', 'ignore'),
                             'Not&nbsp;permitted&nbsp;(ignored)'])
    # Clean up the folder to contain processed files, then move images there:
    shorter = app.config['VALIDATED_FOLDER']
    processed_list = glob.glob(os.path.join(shorter, "*"))
    print "processed_list:\n", processed_list
    processed_contents = [name for name in processed_list
                          if os.path.isfile(name)]
    print "processed_contents:\n", processed_contents
    processed_ct = len(processed_contents)
    if processed_ct > 0:
        for file in processed_contents:
            os.remove(file)

    print 'execute: mv {0}/* {1}'.format(app.config['UPLOAD_FOLDER'],
                                         app.config['VALIDATED_FOLDER'])
    os.system('mv {0}/* {1}'.format(app.config['UPLOAD_FOLDER'],
                                    app.config['VALIDATED_FOLDER']))

    if bad_guys == 0:
        bad_list.append([' ', 'All files ingested.', 'OK'])
    success_str = "Sucessfully uploaded {0} files."

    data = [bad_list, success_str.format(len(uploaded_files) - bad_guys)]

    return render_template('UploadProcess.html', data=data)


@app.route('/display_images', methods=["GET", "POST"])
def display_images():
    print "\nAction selected: show images\n"
    path_files = [file for file in
                  glob.glob(os.path.join(app.config['VALIDATED_FOLDER'], "*"))
                  if allowed_file(file)]
    fileCt = len(path_files)
    print "file count: ", fileCt
#   print "\npath_files:\n", path_files, "\n"
    files = map(lambda x: x.split('/')[-1], path_files)
#   print "\nfiles:", files

    modulo8 = len(path_files) % 8
    if modulo8 != 0:
        os.system('cp {0}/{1} {2}'.format(app.config['BCKGND_FOLDER'],
                                          app.config['BACKGROUND_IMG'],
                                          app.config['VALIDATED_FOLDER']))

        files += [app.config['BACKGROUND_IMG']]*(8 - modulo8)
#   print "\nfiles:", files
    files = [files[x:x+8] for x in xrange(0, len(files), 8)]
    return render_template('display_images.html', data=files)


@app.route('/show_anomalies', methods=["GET", "POST"])
def show_anomalies():
    print "\nAction selected: show anomalies\n"

    # Before computing anomaly scores, remove white square that was used to
    # format the /display_images page:
    os.system('rm -f {0}/{1}'.format(app.config['VALIDATED_FOLDER'],
                                     app.config['BACKGROUND_IMG']))
    #############

    caffe.set_device(0)
    caffe.set_mode_gpu()

    cpath0 = (app.config['CAFFE_ROOT'] +
              'models/bvlc_reference_caffenet/deploy.prototxt')
    cpath1 = (app.config['CAFFE_ROOT'] +
              'models/bvlc_reference_caffenet/' +
              'bvlc_reference_caffenet.caffemodel')
    net = caffe.Net(cpath0, cpath1, caffe.TEST)

    t0 = time.time()

    trans = caffe.io.Transformer({'data': net.blobs['data'].data.shape})
    trans.set_transpose('data', (2, 0, 1))
    shorter = app.config['CAFFE_ROOT']
    shorter += 'python/caffe/imagenet/ilsvrc_2012_mean.npy'
    trans.set_mean('data', np.load(shorter).mean(1).mean(1))  # mean pixel

    # The reference model operates on images in [0,255] range instead of [0,1]:
    trans.set_raw_scale('data', 255)

    # The reference model has channels in BGR order instead of RGB, so swap:
    trans.set_channel_swap('data', (2, 1, 0))

    print "src_directory: {0}".format(app.config['VALIDATED_FOLDER'])

    path_files = glob.glob1(app.config['VALIDATED_FOLDER'], "*")
    print "path_files:\n", path_files
    t1 = time.time()			# time to intitialize Caffe
    print "re-sizing images in {0} ".format(app.config['VALIDATED_FOLDER']),

    # --------------------------------------------------------------- #
    # Start by testing all files and seeing if they look like images: #
    # --------------------------------------------------------------- #

    src_file_list = []
    ignored_files = []
    print "app.config['VALIDATED_FOLDER']: ", app.config['VALIDATED_FOLDER']
    for i, file in enumerate(path_files):
        print "file: {0}".format(file)
        name = ".".join(file.split('.')[:-1])
        suffix = file.split('.')[-1]
        identify_comm = ["identify",
                         "{0}/{1}.{2}".format(app.config['VALIDATED_FOLDER'],
                                              name, suffix)]
        identify = subprocess.Popen(identify_comm, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        ident_message, ident_error = identify.communicate()
        if '@ error' in ident_error:
            print "\n\t--->\tError identifying {0}. Skipping.".format(name)
            ignored_files.append("{0}.{1}".format(name, suffix))
        else:
            src_file_list.append("{0}.{1}".format(name, suffix))

    t2 = time.time()			# t2-t1: time to verify files are images

#   file_count = len(src_file_list)

#   # set net to batch size of file count (maximimum size of 128):
    max_count = 2048
    file_count = min([max_count, len(src_file_list)])

    print "file_count: ", file_count
#   print "Setting net.blobs['data'] shape ... "
#   print type(net.blobs['data'])
    net.blobs['data'].reshape(file_count, 3, 227, 227)

#   print "net.blogs reshaped."

    # Do the ingest/pre-process:
    for i, myfile in enumerate(src_file_list):
        if i >= max_count:
            print "Hmmm. Thems a lot of files! Only doing the first 2048!"
            break
        path_file = app.config['VALIDATED_FOLDER'] + '/' + myfile
        print "{0}:\t{1}".format(i, path_file)
        shorter = trans.preprocess('data', caffe.io.load_image(path_file))
        net.blobs['data'].data[i] = shorter

    t3 = time.time()

    fc_level = 7
    if fc_level in [6, 7, 8]:
        fc_str = 'fc{0:1d}'.format(fc_level)
    else:
        waah_string = "fc_level: {0}, must be one of [6, 7, 8]. Waaah!'"
        print waah_string.format(fc_level)

    print "Pushing images through the network ..."
    net.forward()
    t4 = time.time()			# t4-t2: time to push through network

    if fc_level == 8:
        X = np.full((len(src_file_list), 1000), np.nan)
    else:
        X = np.full((len(src_file_list), 4096), np.nan)

    for i in range(len(src_file_list)):
        X[i] = net.blobs[fc_str].data[i]

    X6 = np.full((len(src_file_list), 4096), np.nan)
    for i in range(len(src_file_list)):
        X6[i] = net.blobs['fc6'].data[i]

    X7 = np.full((len(src_file_list), 4096), np.nan)
    for i in range(len(src_file_list)):
        X7[i] = net.blobs['fc7'].data[i]

    X8 = np.full((len(src_file_list), 1000), np.nan)
    for i in range(len(src_file_list)):
        X8[i] = net.blobs['fc8'].data[i]

    ###########

    print "Images have been pre-processed."
#   X = myINF.featurize(fc_level=6)
    print "We have extracted features!"
    print np.shape(X)

    ADmodel.proc_file_list = src_file_list

#   ADmodel.X = X6
    print "Attempting iForest on fc6."
    ADmodel.fit(X=X6)
    print "fc6 scores:\n", ADmodel.iFmodel.anomaly_score_
    print ""
    top10fc6 = ADmodel.show_top_k(10)
    t5 = time.time()			# t5-t4: time to run iForest on fc6
    keys = top10fc6.keys()
    print top10fc6[keys[0]]
    print top10fc6[keys[1]]
    print top10fc6[keys[2]]

#   ADmodel.X = X7
    print "Attempting iForest on fc7."
    ADmodel.fit(X=X7)
    print "fc7 scores:\n", ADmodel.iFmodel.anomaly_score_
    print ""
    top10fc7 = ADmodel.show_top_k(10)
    t6 = time.time()			# t6-t5: time to run iForest on fc7

#   ADmodel.X = X8
    print "Attempting iForest on fc8."
    ADmodel.fit(X=X8)
    print "fc8 scores:\n", ADmodel.iFmodel.anomaly_score_
    print ""
    top10fc8 = ADmodel.show_top_k(10)
    t7 = time.time()			# t7-t6: time to run iForest on fc8

    keys = top10fc8.keys()
    print top10fc8[keys[0]]
    print top10fc8[keys[1]]
    print top10fc8[keys[2]]

    scores_list = []
    i = 0
    for fc7_rank in top10fc7.iterkeys():
        file_no, file_name, fc6_score = top10fc6[fc7_rank]
        file_no, file_name, fc7_score = top10fc7[fc7_rank]
        file_no, file_name, fc8_score = top10fc8[fc7_rank]
        if fc6_score < 0.5:
            fc6_hex_str = '#b4b4b4'
        elif fc6_score >= 0.5 and fc6_score < 0.75:
            val = hex(int(300.*(fc6_score - 0.5) + 180))[-2:]
            fc6_hex_str = '#' + str(val) + 'b4b4'
        elif fc6_score > 0.75:
            print fc6_score, fc6_score - 0.75
            val = hex(255 - int(1020.*(fc6_score - 0.75)))[-2:]*2
            fc6_hex_str = '#ff' + str(val)
        if fc7_score < 0.5:
            fc7_hex_str = '#b4b4b4'
        elif fc7_score >= 0.5 and fc7_score < 0.75:
            val = hex(int(300.*(fc7_score - 0.5) + 180))[-2:]
            fc7_hex_str = '#' + str(val) + 'b4b4'
        elif fc7_score > 0.75:
            print fc7_score, fc7_score - 0.75
            val = hex(255 - int(1020.*(fc7_score - 0.75)))[-2:]*2
            fc7_hex_str = '#ff' + str(val)
        scoreStr = "fc6_score: {0}, fc7_score: {1}, fc8_score: {2}"
        print scoreStr.format(fc6_score, fc7_score, fc8_score)
        if fc8_score < 0.5:
            fc8_hex_str = '#b4b4b4'
        elif fc8_score >= 0.5 and fc8_score < 0.75:
            val = hex(int(300.*(fc8_score - 0.5) + 180))[-2:]
            fc8_hex_str = '#' + str(val) + 'b4b4'
        elif fc8_score > 0.75:
            print fc8_score, fc8_score - 0.75
            val = hex(255 - int(1020.*(fc8_score - 0.75)))[-2:]*2
            fc8_hex_str = '#ff' + str()

        scores_list.append((str(i), file_name, fc6_hex_str,
                            "{0:4.2f}".format(fc6_score), fc6_hex_str,
                            "{0:4.2f}".format(fc7_score), fc6_hex_str,
                            "{0:4.2f}".format(fc8_score)))
        i += 1

    # Now make it double wide, for two-column formatting:
    new_scores = []
    for i in range(5):
        a0, a1, a2, a3, a4, a5, a6, a7 = scores_list[2*i]
        b0, b1, b2, b3, b4, b5, b6, b7 = scores_list[2*i + 1]
        new_scores.append((a0, a1, a2, a3, a4, a5, a6, a7,
                           b0, b1, b2, b3, b4, b5, b6, b7))

    dt10 = t1 - t0		# time to initialize Caffe
    dt21 = t2 - t1		# time to verify that files are images
    dt32 = t3 - t2		# time to pre-process images
    dt43 = t4 - t3		# time to push images through network
    dt54 = t5 - t4		# time to run iForest on fc6
    dt65 = t6 - t5		# time to run iForest on fc7
    dt76 = t7 - t6		# time to run iForest on fc8
    dt74 = t7 - t4		# time to run iForest on all three
    dt70 = t7 - t0		# total time to process
    dt21min = int(dt21/60.0)
    dt21sec = dt21 % 60.0
    dt32min = int(dt32/60.0)
    dt32sec = dt32 % 60.0
    dt43min = int(dt43/60.0)
    dt43sec = dt43 % 60.0
    dt74min = int(dt74/60.0)
    dt74sec = dt74 % 60.0
    dt70min = int(dt70/60.0)
    dt70sec = dt70 % 60.0

    print ("\n\ninitialize\tvalidate images\tpre-process images"
           "\tpush through net\tiForest "
           "fc6\tiForest fc7\tiForest fc8\tall iForest\ttotal time")
    formatStr = ("{0:5.3f} s\t\t{1:02d} min, {2:5.3f} s"
                 "\t{3:02d} min, {4:5.3f} s\t{5:02d} min,"
                 " {6:5.3} s\t\t{7:5.3f} s\t\t{8:5.3f} s\t\t{9:5.3f} s\t\t"
                 "{10:02d} min, {11:5.3f} s\t{12:02d} min, {13:5.3f} s\n")
    print formatStr.format(dt10, dt21min, dt21sec, dt32min, dt32sec, dt43min,
                           dt43sec, dt54, dt65, dt76, dt74min, dt74sec,
                           dt70min, dt70sec)
    formatStr = ("{0:5.3f}\t\t{1:5.3f}\t\t{2:5.3f}\t\t\t{3:5.3f}\t\t\t{4:5.3f}"
                 "\t\t{5:5.3f}\t\t{6:5.3f}\t\t{7:5.3f}\n\n")
    print formatStr.format(dt10/dt70, dt21/dt70, dt32/dt70, dt43/dt70,
                           dt54/dt70, dt65/dt70, dt76/dt70, dt74/dt70)

    time_thangs = [dt10, dt21min, dt21sec, dt32min, dt32sec, dt43min, dt43sec,
                   dt54, dt65, dt76, dt74min, dt74sec, dt70min, dt70sec,
                   dt10/dt70, dt21/dt70, dt32/dt70, dt43/dt70, dt54/dt70,
                   dt65/dt70, dt76/dt70, dt74/dt70]
    print np.shape(new_scores),  np.shape(time_thangs)
    return render_template('display_top_k.html', data=new_scores,
                           dt10="{0:5.3f}".format(dt10),
                           dt21min="{0:02d}".format(dt21min),
                           dt21sec="{0:4.2f}".format(dt21sec),
                           dt32min="{0:02d}".format(dt32min),
                           dt32sec="{0:4.2f}".format(dt32sec),
                           dt43min="{0:02d}".format(dt43min),
                           dt43sec="{0:4.2f}".format(dt43sec),
                           dt54="{0:5.3f}".format(dt54),
                           dt65="{0:5.3f}".format(dt65),
                           dt76="{0:5.3f}".format(dt76),
                           dt74min="{0:02d}".format(dt74min),
                           dt74sec="{0:4.2f}".format(dt74sec),
                           dt70min="{0:02d}".format(dt70min),
                           dt70sec="{0:4.2f}".format(dt70sec),
                           frac10="{0:5.3f}".format(dt10/dt70),
                           frac21="{0:5.3f}".format(dt21/dt70),
                           frac32="{0:5.3f}".format(dt32/dt70),
                           frac43="{0:5.3f}".format(dt43/dt70),
                           frac54="{0:5.3f}".format(dt54/dt70),
                           frac65="{0:5.3f}".format(dt65/dt70),
                           frac76="{0:5.3f}".format(dt76/dt70),
                           frac74="{0:5.3f}".format(dt74/dt70))

if __name__ == '__main__':

    # INFmodel = inf.ImageNetFeaturizer()

    # ADmodel = ad.AnomalyDetect(use_color=True, max_depth=75)
    ADmodel = ad.AnomalyDetect(use_color=True, max_depth=85, n_estimators=200)

    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
