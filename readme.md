# Anomaly Detection in Images Using a Deep Convolution Neural Network and Isolation Forest

#### *A Capstone Project for the Galvanize Data Science Immersive Program, by Mark Wilber*

<center>
![Which of these does not belong?](https://github.com/mw0/gcp/blob/master/SesameStreetWhichNotAlike.png "Which of these does not belong?")
</center>

## Overview:

In my former work as a research scientist I was always on the look-out for anomalies; on a very good day they might point to a novel phenomenon, and later a quick publication. More typically, they served the important role of revealing errors in my code.  
  
Now that I am looking at general techniques for inferring meaning from data, I ask the question of how to find anomalies automatically. I've long wanted to work with deep convolution neural networks (DCNNs), so images are a natural, but far from exhaustive, choice of subject matter. 

The [app linked here](http://www.rustytrephine.info "Try this App! ") shows examples of images that have been given anomaly scores indicating how much they differ from the overall collection of photos provided.
To be more specific, a batch of images are fed into a deep convolution neural network (DCNN), and high-level feature weights are extracted from it. These in turn are fed into an Isolation Forest anomaly algorithm, and those images with the highest scores are displayed.

It would be too easy to cherry pick results, so you also have the option of trying it out yourself with photos that you upload.

## Outline:
* Isolation Forest
* Deep Convolution Neural Network
* Results
* Future directions

## Isolation Forest

Isolation Forest is a binary tree-based method for determining outliers due to [Lui, F.T. et al, 2008](http://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf?q=isolation).
It works by constructing an ensemble of 'isolation trees', and computing average path lengths required to isolate points in feature space.

The process for building an Isolation Tree is:
* randomly select a feature on which to branch;
* randomly select a value within the range of that feature to split the node;
* repeat the process until a single point is isolated, or until a maximum tree length is reached.

The figure below from Lui, F.T. et al, 2008 shows representative segmentation of a 2-D feature space by random binary trees, leading to the isolation of an "ordinary" point <em>x<sub>i</sub></em> and an anomolous point <em>x<sub>0</sub></em>.
On average, it is more difficult to isolate a point that has near neighbors, so a larger number of branches are needed, and an ensemble of iTrees segregating <em>x<sub>i</sub></em> will have a larger average length than that for iTrees isolating <em>x<sub>0</sub></em>.

![Isolating Points with iTrees](https://github.com/mw0/gcp/blob/master/presentation/ITreeIsolatingPoints.png)

Anomaly scores are constructed from average path length <em>&lang;h(x)&rang;</em> such that:

![anomaly score limits](https://github.com/mw0/gcp/blob/master/sx.png)

for <em>&lang;h(x)&rang;</em> the ensemble average path length required to isolate point <em>x</em>.

