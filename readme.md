# Anomaly Detection in Images Using a Deep Neural Network and Isolation Forest

** *A Capstone Project for the Galvanize Data Science Immersive Program, by Mark Wilber*

## Overview:

In my former work as a research scientist I was always on the look-out for anomalies; on a very good day they might point to a novel phenomenon, and later a quick publication. More typically, they served the important role of revealing errors in my code.  
  
Now that I am looking at general techniques for inferring meaning from data, I ask the question of how to find anomalies automatically. I've long wanted to work with deep convolution neural networks, so images are a natural, but far from exhaustive, choice of subject matter. 

The [application to be linked here](http://www.rustytrephine.info "Try this App!") takes images uploaded by users, pre-processes them, feeds them through a convolution neural network, and extracts high-level feature weights. Those weights for the collection of images are fed into an Isolation Forest model to generate anomaly scores.

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
* repeat the process until a single point is isolated, or until a maximum tree lengthis reached.

The figure below from Lui, F.T. et al, 2008 shows representative segmentation of a 2-D feature space by random binary trees, leading to the isolation of a "ordinary" point $x_1$ and an anomolous point $x_0$.
On average, it is more difficult to isolate a point that has near neighbors, so a larger number of branches are needed, and an ensemble of iTrees segregating $x_1$ will have a larger average length than that for iTrees isolating $x_0$.

![](https://github.com/mw0/gcp/presentation/ITreeIsolatingPoints.png)

Anomaly scores are constructed from average path length $\left< h(x) \right>$ such that:

$s \longrightarrow \begin{cases}
  1, & \left< h(x) \rightarrow 0 \\
  0, & \left< h(x) \rightarrow \infty
\end{cases}
$