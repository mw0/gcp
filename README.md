# Anomaly Detection in Images Using a Deep Convolution Neural Network and Isolation Forest

#### *A Capstone Project for the Galvanize Data Science Immersive Program, by Mark Wilber*

<center>

![Which of these does not belong?](https://github.com/mw0/gcp/blob/master/SesameStreetWhichNotAlike.png)

</center>

## Overview:

In my former work as a research scientist I always sought out anomalies; on a very good day they might point to a novel phenomenon, and later a quick publication. More typically, they served the important role of revealing errors in my code.  
  
Now I ask the question of how to find anomalies automatically, using machine learning. I've been very interested in deep convolution neural networks (DCNNs), so images make a natural &mdash; but far from exhaustive &mdash; choice of subject matter. 

The app (no longer active) showed examples of images that have been given anomaly scores, which indicate how much they differ from the overall collection of photos provided. (See below.)
To be more specific, a batch of images are fed into a deep convolution neural network (DCNN), and high-level feature weights are extracted from them. These in turn are fed into an Isolation Forest anomaly algorithm, and those images with the highest scores are displayed.

*It would be too easy to cherry pick results, so users had the option of trying out the app themselves with photos that they uploaded.*

## Outline:
* <a href="#iForest">Isolation Forest</a>
* <a href="#DCNN">Deep Convolution Neural Network</a>
* <a href="#results">Results</a>
* <a href="#profiling">Basic Profiling</a>
* About the Code
* Future Directions

## <a name="iForest">Isolation Forest</a>

Isolation Forest is a binary tree-based method for determining outliers due to [Lui, F.T. et al, \[2008\]](http://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf?q=isolation).
It works by constructing an ensemble of 'isolation trees' (iTrees), and computing average path lengths required to isolate points in feature space.

The process for building an Isolation Tree is:
* randomly select a feature on which to branch;
* randomly select a value within the range of that feature to split the node;
* repeat the process until a single point is isolated, or until a maximum tree length is reached.

The figure below from Lui, F.T. et al, [2008] shows representative segmentation of a 2-D feature space by random binary trees, leading to the isolation of an "ordinary" point <em>x<sub>i</sub></em> and an anomolous point <em>x<sub>0</sub></em>.
On average, it is more difficult to isolate a point that has near neighbors, so a larger number of branches are needed, and an ensemble of iTrees segregating <em>x<sub>i</sub></em> will have a larger average length than that for iTrees isolating <em>x<sub>0</sub></em>.

![Isolating Points with iTrees](https://github.com/mw0/gcp/blob/master/presentation/ITreeIsolatingPoints.png)

Anomaly scores <em>s</em>(<em>x</em>) are constructed from the ensemble average path length &lang;<em>h(</em><em>x</em>)&rang; required to isolate a point <em>x</em>:

![anomaly score limits](https://github.com/mw0/gcp/blob/master/presentation/sxn.png)

where *c(n)* represents the expected path length for a failed binary tree search. This results in the limits

![anomaly score limits](https://github.com/mw0/gcp/blob/master/presentation/sx.png)

Typically, scores < 0.5 indicate nothing unusual, while scores > 0.6 suggest an outlier.
(See Lui, F.T. et al, [2008] for additional details.)
The significance of particular scores, however, depends upon the homogeneity of the bulk of the sample, which here will be dependent to some degree on the choice for the high-level features of the image.  
  
In practice, the process is somewhat more complicated:

* First (training phase), an ensemble of iTrees is built from random sub-samples of the original dataset;
* Second (test phase), every data point is fed into that ensemble of iTrees, with path lengths computed for each tree;
* Third, anomaly scores are computed using each point's average path length.  
  
Key points are that:
* True anomalies will be well-represented in an isolation forest ensemble, terminating in external nodes with short path lengths;
* It is unnecessary to construct trees that isolate every "normal" point, as we are only interested in establishing that they have long path lengths; passed through the ensemble of iTrees, ordinary points will tend to terminate in the same external nodes as their near neighbors (with correspondingly long average path lengths)

##  <a name="DCNN">The Deep Convolution Neural Network</a>

Not long ago it might take a team of experts to engineer useful features from images to use in machine learning applications.
Recently, deep convolution neural networks (DCNNs) have been created which generate strongly-relevant high-level features automatically.
As a network is trained to classify images, weights in the final layers contain information about structure that best allow for discrimination between the classes.

Today, a number of models are made available via commercial products, or through academic repositories.
The [Caffe Project](http://caffe.berkeleyvision.org/) at U.C. Berkeley's Vision and Learning Center is a very fast deep learning framework, and specs for a variety of models are available through their [Model Zoo](http://caffe.berkeleyvision.org/model_zoo.html).
We have obtained their BVLC Reference CaffeNet model&sup2; ("AlexNet"), with weights pre-trained on 1.2 million images from the ImageNet LSVRC-2010 data set.

For our image anomaly framework, we insert re-sized images into the DCNN, after subtracting pixel intensities average over the entire training set.
Feature weights at the final three fully-connected layers ('fc6', 'fc7' and 'fc8') are extracted, and separately inserted into the Isolation Forest analyzer.
For fc6 and fc7 there are 4096 feature weights.
Weights from fc8 correspond to the 1000 probabilities assigned to each of the 1000 ImageNet classes; in this case they represent classes, rather than high-level features.
Anomaly scores for each image are separately calculated using the 3 sets of weights. The images presented to the user are ranked according to fc7 scores.

&sup2;[Krizhevsky, Alex, Ilya Sutskever, and Geoffrey E. Hinton. *Imagenet classification with deep convolutional neural networks.*, Advances in neural information processing systems, 2012](http://www.cs.toronto.edu/~fritz/absps/imagenet.pdf)

## <a name="#results">Results</a>

The following example illustrates the type of results obtained.
In this case, images of 55 tigers, along with 3 leopards, 3 house cats, and an actual house were provided.

<center>

![Some of the tiger image set.](https://github.com/mw0/gcp/blob/master/presentation/tigersNstuff.png)

</center>

The 10 "most anomalous" images returned are shown below:

<center>

![Least tiger-like.](https://github.com/mw0/gcp/blob/master/presentation/tigerAnomRanked.png)

</center>

* It is easy to see that these "most anomalous" include two of the three house cats, the three leopards, and the house.
* Our intuition may suggest that the missing house cat should be ranked higher than either of the tigers shown, but:
  * it is important to keep in mind that there is more to most images than the presence of a feline or house. The house, for example has grass and trees, which are also present in a large fraction of the tiger images.
  * two of the 'anomalous' tigers are on white or snow backgrounds.
  * each of these distinctions is encoded in the high-level features extracted from the neural network, while our own brains are prejudiced by the construction of the description above to focus soley  on classifying the central object.
* Isolation Forest relies on randomness, so each time it is done there are small variations in the scores. This can affect the ordering of the results displayed.

#### An example like this is subject to tampering by the author. You should try out the app (currently off-line, alas) yourself, using images that you choose!

## <a name="profiling">Basic Profiling</a>

When you try out the app yourself, you will find that there is a bit of a wait when you request anomaly scores. If you scroll to  the bottom of the table, you will see Timing Information, showing you what took all that time. Here is a typical example:

||initialize Caffe|validate images|pre-process images|push through network|iForest on fc6|iForest on fc7|iForest on fc8|iForest combined|total|
|----|--------------|---------------|------------------|--------------------|--------------|--------------|--------------|----------------|-----|
|time|0.005&nbsp;s|00&nbsp;m,&nbsp;1.44&nbsp;s|00&nbsp;m,&nbsp;15.90&nbsp;s|00&nbsp;m,&nbsp;0.24&nbsp;s|1.036&nbsp;s|0.899&nbsp;s|0.589&nbsp;s|00&nbsp;m,&nbsp;2.52&nbsp;s|00&nbsp;m,&nbsp;20.11&nbsp;s|
|fraction|0.000|0.072|0.791|0.012|0.052|0.045|0.029|0.126||

Most of the time, &gt; 75%, is spent pre-processing images (re-sizing and subtracting training pixel averages), with the time required to push those images through the neural network only about 1% of the total. Clearly, the GPUs are used to great advantage in the neural network, but are not employed when re-sizing the images.  
  
Generating the isolation forest trees and extracting anomaly scores for the three feature sets typically takes 10-20% of the total time. If you run this yourself, you may find that the greatest time required is that to upload your images in the first place!
