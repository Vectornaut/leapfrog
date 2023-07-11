# leapfrog
Unfolding hyperbolic billiards

## Working languages

Python 3, Sage, GLSL.

## How to

### Play with the proof-of-concept

#### Install dependencies
1. Install [Vispy](http://vispy.org/installation.html) in your Python 3 distribution by calling `pip3 install vispy`.
2. Install Qt5 and Qt OpenGL.
  - Their Ubuntu 20.04 packages are `python3-pyqt5` and `python3-pyqt5.qtopengl`.
  - Install their Python bindings by calling `pip3 install PyQt5`.
    - If you're using Sage's internal Python distribution, as described below, call `sage -pip install PyQt5` instead.

#### Run program
1. Call `python3 leapfrog.py`. A window showing a polygon in the hyperbolic plane should appear.
  - If the interpreter complains that there's "`no module named 'sage.all'`", try using Sage's internal Python distribution by calling `sage -python explorer.py`.
    - If this also gives you trouble, call `sage -python --version` to make sure your Sage has Python 3 or above.
2. Press the keys 1&ndash;9 to unfold along sides 1&ndash;9 of the polygon.
  - The sides of the polygon are labeled by colors: (1) red, (2) orange, (3) yellow, (4) green, (5) blue, (6, 7, 8, ...) pink.
  - If you need non-color labels, let me know.
  - A message in the terminal will tell you whether the unfolding succeeded.
3. The bright part of the plane shows the swath of trajectories consistent with how you've unfolded so far.
  - The unfolding only succeeds if this swath of trajectories goes through the side you want to unfold over.
