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


# Make sure that caffe imagnet reference model has been fetched:

app = Flask(__name__)

app.config.from_pyfile('../.config/settings.cfg')

if not os.path.isfile(app.config['CAFFE_ROOT']
                      + 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel'):
    print("Downloading pre-trained CaffeNet model...")
    shell_command = app.config['CAFFE_ROOT'] \
                    + 'scripts/download_model_binary.py  ' \
                    + app.config['CAFFE_ROOT'] \
                    + 'models/bvlc_reference_caffenet'
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

#app.config['ALLOWED_EXTENSIONS'] = set(['PNG', 'JPG', 'JPEG',
#                                        'png', 'jpg', 'jpeg'])


@app.route('/', methods = ["GET", "POST"])
def index():
    '''
    This is the welcome page. A simple messagge and a couple of buttons to
    push to get started.
    '''

    return '''
    <html>
    <body>
    <h2>Anomaly Detection Using A Deep Convolution Neural Network and Isolation Forest.</h2>
    This application finds anomalies in images. It does this by feeding images through a pre-trained, deep convolution neural network&sup1; extracting high-level feature weights; and constructing isolation trees&sup2; using those weights.

    <p>For more infomation on this, see the <a href="http://github.com/mw0/gcp">project description</a>.

    <p>
    You can view anomaly scores computed for images we provide, or you can upload your own:

    <form action="/provided_images" method="POST">
        <input type="submit" value="View pre-processed examples"> (Coming soon.)
    </form>
    <form action="/upload_form" method="POST">
        <input type="submit" value="I have images to upload">
    </form>
    </p>

    <p>&nbsp;</p><p class="footnote">
    &sup1;<a href="http://www.cs.toronto.edu/~fritz/absps/imagenet.pdf">Krizhevsky, Alex, Ilya Sutskever, and Geoffrey E. Hinton. ~Imagenet classification with deep convolutional neural networks.~ Advances in neural information processing systems. 2012</a>.<br>
    &sup2;<a href="http://dx.doi.org/10.1109/ICDM.2008.17">Liu, F.T., K. M. Ting and Z.-H. Zhou, <em>Isolation Forest</em>, Eighth IEEE International Conference on Data Mining, 2008, ICDM 08., p413., 2008.</a><br>
    </p>
    </body>
    </html>
    '''


@app.route('/provided_images', methods = ["GET", "POST"])
def provided_images():
    return '''
    <html>
    <body>
    <h2>Provided Images</h2>
    <p>&nbsp;</p>

    Select an example of pre-processed images to see how their anomaly scores
    turn out.

    <form action="/mostly_tigers" method="POST">
        <input type="submit" value="Mostly tigers, (Oh my!)">
    </form> 
    <form action="/mostly_homes" method="POST">
        <input type="submit" value="Mostly homes" disabled>
    </form> 
    <form action="/yum_pizza" method="POST">
        <input type="submit" value="Yum, pizza" disabled>
    </form> 

    <table>
    <tr align="left"><th>i</th><th>File name</th><th>Status</th></tr>
    '''

@app.route('/mostly_tigers', methods = ["GET", "POST"])
def mostly_tigers():
    return render_template('MostlyTigers.html')


@app.route('/anomalous_tigers', methods = ["GET", "POST"])
def anomalous_tigers():
    return render_template('AnomalousTigers.html')


@app.route('/upload_form', methods = ["GET", "POST"])
def upload_form():
    '''
    A simple form permitting users to select a local directory, and files
    within, for upload.
    '''

    # Clean out the upload folder before fetching new files.
    os.system('rm {0}/*'.format(app.config['UPLOAD_FOLDER']))

    return '''
    <html>
    <body>
    <h2>Upload Your Files</h2>
    Each time you upload files, previous uploads will be removed from the server.
    <p>
    Images in formats other than PNG and JPEG will be ignored.
    <p>
    <table>
    <tr><td>
            <form method="POST" enctype="multipart/form-data" action="/upload_process">
                <input type="file" name="file[]" multiple="">
                <input type="submit" value="Upload">
            </form>
        </td>
    </tr>
    </table>
    '''


# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']



@app.route('/upload_process', methods=["GET", "POST"])
def upload_process():

    print "\nupload_process()\n"

#   ADmodel.src_file_list = []
#   ADmodel.proc_file_list = []
    retPage = '''
    <html>
    <body>
    <h2>Uploading Your Files</h2>
    <p>&nbsp;</p>

    <form action="/display_images" method="POST">
        <input type="submit" value="Display Images">
    </form> 
    <form action="/show_anomalies" method="POST">
        <input type="submit" value="Show Anomalies">
    </form> 

    <table>
    <tr align="left"><th>i</th><th>File name</th><th>Status</th></tr>
    '''
    print "Requesting uploaded files list."
    uploaded_files = flask.request.files.getlist("file[]")
    print "uploaded_files:\n", uploaded_files
    OKstr = "<tr><td>{0}</td><td>{1}</td><td>OK</td></tr>"
    sadStr = "<tr><td>{0}</td><td>{1}</td><td>Not&nbsp;permitted&nbsp;(ignored)</td></tr>"
    bad_guys = 0
    for i, file in enumerate(uploaded_files):
#       print file.filename.encode('utf-8', 'ignore')
        print file.filename.encode('utf-8')
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#           retPage += OKstr.format(i + 1, file.filename.encode('utf-8', 'ignore'))
        else:
            bad_guys += 1
            retPage += sadStr.format(i + 1, file.filename.encode('utf-8', 'ignore'))

    # Clean up the folder to contain processed files, then move images there:
    processed_list = glob.glob(os.path.join(app.config['VALIDATED_FOLDER'], "*"))
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
        retPage += '<tr><td>&nbsp;</td><td align="center">All files ingested.</td><td>OK</td></tr>'
    success_str = "<p>\nSucessfully uploaded {0} files.\n"
    retPage += success_str.format(len(uploaded_files) - bad_guys)
    retPage += "</table>\n</body>\n</html>"
    return retPage


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
    return render_template('display_images.html', data = files)


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

    net = caffe.Net(app.config['CAFFE_ROOT'] \
                    + 'models/bvlc_reference_caffenet/deploy.prototxt',
                    app.config['CAFFE_ROOT'] \
                    + 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel',
                    caffe.TEST)

    trans = caffe.io.Transformer({'data': net.blobs['data'].data.shape})
    trans.set_transpose('data', (2,0,1))
    trans.set_mean('data', \
                   np.load(app.config['CAFFE_ROOT'] \
                           + 'python/caffe/imagenet/ilsvrc_2012_mean.npy').mean(1).mean(1)) # mean pixel

    # The reference model operates on images in [0,255] range instead of [0,1]:
    trans.set_raw_scale('data', 255)

    # The reference model has channels in BGR order instead of RGB, so swap:
    trans.set_channel_swap('data', (2,1,0))

    print "src_directory: {0}".format(app.config['VALIDATED_FOLDER'])

    path_files = glob.glob1(app.config['VALIDATED_FOLDER'], "*")
    print "path_files:\n", path_files
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
        net.blobs['data'].data[i] \
                      = trans.preprocess('data', caffe.io.load_image(path_file))

    fc_level = 7
    if fc_level in [6, 7, 8]:
        fc_str = 'fc{0:1d}'.format(fc_level)
    else:
        waah_string = "fc_level: {0}, must be one of [6, 7, 8]. Waaah!'"
        print waah_string.format(fc_level)

    print "Pushing images through the network ..."
    start = time.time()
    net.forward()
    print "Done. That took ", time.time() - start, "seconds."

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
#   X = myINF.featurize(fc_level = 6)
    print "We have extracted features!"
    print np.shape(X)

    ADmodel.proc_file_list = src_file_list

#   ADmodel.X = X6
    print "Attempting iForest on fc6."
    ADmodel.fit(X = X6)
    print "fc6 scores:\n", ADmodel.iFmodel.anomaly_score_
    print ""
    top10fc6 = ADmodel.show_top_k(10)
    keys = top10fc6.keys()
    print top10fc6[keys[0]]
    print top10fc6[keys[1]]
    print top10fc6[keys[2]]

#   ADmodel.X = X7
    print "Attempting iForest on fc7."
    ADmodel.fit(X = X7)
    print "fc7 scores:\n", ADmodel.iFmodel.anomaly_score_
    print ""
    top10fc7 = ADmodel.show_top_k(10)

#   ADmodel.X = X8
    print "Attempting iForest on fc8."
    ADmodel.fit(X = X8)
    print "fc8 scores:\n", ADmodel.iFmodel.anomaly_score_
    print ""
    top10fc8 = ADmodel.show_top_k(10)
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
            fc6_hex_str = '#' + str(hex(int(300.*(fc6_score - 0.5) + 180))[-2:]) + 'b4b4'
        elif fc6_score > 0.75:
            print fc6_score, fc6_score - 0.75
            fc6_hex_str = '#ff' + str(hex(255 - int(1020.*(fc6_score - 0.75)))[-2:]*2)
        if fc7_score < 0.5:
            fc7_hex_str = '#b4b4b4'
        elif fc7_score >= 0.5 and fc7_score < 0.75:
            fc7_hex_str = '#' + str(hex(int(300.*(fc7_score - 0.5) + 180))[-2:]) + 'b4b4'
        elif fc7_score > 0.75:
            print fc7_score, fc7_score - 0.75
            fc7_hex_str = '#ff' + str(hex(255 - int(1020.*(fc7_score - 0.75)))[-2:]*2)
        scoreStr = "fc6_score: {0}, fc7_score: {1}, fc8_score: {2}"
        print scoreStr.format(fc6_score, fc7_score, fc8_score)
        if fc8_score < 0.5:
            fc8_hex_str = '#b4b4b4'
        elif fc8_score >= 0.5 and fc8_score < 0.75:
            fc8_hex_str = '#' + str(hex(int(300.*(fc8_score - 0.5) + 180))[-2:]) + 'b4b4'
        elif fc8_score > 0.75:
            print fc8_score, fc8_score - 0.75
            fc8_hex_str = '#ff' + str(hex(255 - int(1020.*(fc8_score - 0.75)))[-2:]*2)

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

    return render_template('display_top_k.html', data = new_scores)

#   for name, image, score in top_k_list:

#       if score < 5.5:
            
    return ""


if __name__ == '__main__':

#   INFmodel = inf.ImageNetFeaturizer()

#   ADmodel = ad.AnomalyDetect(use_color=True, max_depth=75)
    ADmodel = ad.AnomalyDetect(use_color=True, max_depth=85, n_estimators = 200)

    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
