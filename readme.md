# Anomaly Detection in Images Using a Deep Convolution Neural Network and Isolation Forest

#### *A Capstone Project for the Galvanize Data Science Immersive Program, by Mark Wilber*

[Which of these do not belong?](https://github.com/mw0/gcp/SesameStreetWhichNotAlike.png)

## Overview:

In my former work as a research scientist I was always on the look-out for anomalies; on a very good day they might point to a novel phenomenon, and later a quick publication. More typically, they served the important role of revealing errors in my code.  
  
Now that I am looking at general techniques for inferring meaning from data, I ask the question of how to find anomalies automatically. I've long wanted to work with deep convolution neural networks (DCNNs), so images are a natural, but far from exhaustive, choice of subject matter. 

The [app linked here](http://www.rustytrephine.info "Try this App!") shows examples of images that have been processed through a DCNN, and returns those with the 10 highest scores computed by an anomaly algorithm.
To be more specific, high-level feature weights are extracted from the back end of the DCNN, and fed into an Isolation Forest routine. Those found to be least alike the bulk of the photos in the collection are listed.  
  
It would be too easy to cherry pick results, so you also have the option of trying it out yourself with photos you upload.

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

The figure below from Lui, F.T. et al, 2008 shows representative segmentation of a 2-D feature space by random binary trees, leading to the isolation of an "ordinary" point <em>x<sub>1</sub></em> and an anomolous point <em>x<sub>0</sub></em>.
On average, it is more difficult to isolate a point that has near neighbors, so a larger number of branches are needed, and an ensemble of iTrees segregating <em>x<sub>1</sub></em> will have a larger average length than that for iTrees isolating <em>x<sub>0</sub></em>.

![Isolating Points with iTrees](https://github.com/mw0/gcp/blob/master/presentation/ITreeIsolatingPoints.png)

Anomaly scores are constructed from average path length <em>&lang;h(x)\&rang;</em> such that:

$s \longrightarrow \begin{cases}
  1, & \left< h(x) \rightarrow 0 \\
  0, & \left< h(x) \rightarrow \infty
\end{cases}
$
