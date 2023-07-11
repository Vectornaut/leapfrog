import sys, os, re, json
import PyQt5.QtWidgets as qt
from PyQt5.QtCore import Qt
from vispy import app
import vispy.io as io
from numpy import pi, sqrt, cos, sin, arctan2, array, dot, cross

from canvas import LeapfrogCanvas

app.use_app(backend_name='PyQt5', call_reuse=True)

# the minkowski bilinear form
def mprod(v, w):
  return dot(v[:-1], w[:-1]) - v[-1]*w[-1]

# reflect v over the plane orthogonal to m
def reflect(m, v):
  return v - 2*mprod(v, m)*m

# the lorentzian cross product
def mcross(v, w):
  result = cross(v, w)
  result[0] = -result[0]
  result[1] = -result[1]
  return result

class SwathPolygon:
  # `sides` is the list of spacelike vectors orthogonal to the polygon's sides,
  # ordered counterclockwise around the polygon when `orient` is 1 and clockwise
  # when `orient` is -1. `vtx[k-1]` and `vtex[k]` are the ends of side k, ordered
  # around the polygon according to the orientation
  def __init__(self, sides, vtx, orient, swath_r = None, swath_l = None):
    self.sides = sides
    self.vtx = vtx
    self.orient = orient
    self.ang = [arctan2(v[1], v[0]) for v in self.vtx]
    self.swath_r = swath_r
    self.swath_l = swath_l
    self.full_swath = swath_r is None and swath_l is None

  def flip(self, k):
    if self.orient > 0:
      ang_r = self.ang[k-1]
      ang_l = self.ang[k]
    else:
      ang_r = self.ang[k]
      ang_l = self.ang[k-1]
    swath_hits = self.full_swath or (ang_l > self.swath_r and self.swath_l > ang_r)
    if ang_l > ang_r and swath_hits:
      if self.full_swath:
        swath_r = ang_r
        swath_l = ang_l
      else:
        swath_r = max(self.swath_r, ang_r),
        swath_l = min(self.swath_l, ang_l)
      return SwathPolygon(
        [reflect(self.sides[k], s) for s in self.sides],
        [reflect(self.sides[k], v) for v in self.vtx],
        -self.orient,
        swath_r,
        swath_l
      )
    else:
      return None

# assumes that sides are ordered counterclockwise
def swath_polygon_from_sides(sides, swath_r = None, swath_l = None):
  vtx = []
  for k in range(len(sides)):
    vtx.append(mcross(sides[k], sides[(k+1) % len(sides)]))
  return SwathPolygon(sides, vtx, 1, swath_r, swath_l)

class Leapfrog(qt.QMainWindow):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.setWindowTitle('Leapfrog')
    self.resize(900, 900)

    # construct a p-gon that tiles with q copies around each vertex
    #
    # the formula for the side normals is adapted from Anton Sherwood's programs
    # for painting hyperbolic tilings,
    #
    #   https://commons.wikimedia.org/wiki/User:Tamfang/programs
    #
    # via the version from chorno-belyi
    #
    #   https://github.com/Vectornaut/chorno-belyi/blob/81e9f51179902da2f75ad24fdd51da3213b8a913/covering.py#L48
    #
    p = 8
    q = 3
    a = cos(pi/q) / sin(pi/p)
    b = sqrt(a*a - 1)
    sides = [array([a*cos(2*pi*k/p), a*sin(2*pi*k/p), b]) for k in range(p)]
    self.polygon = swath_polygon_from_sides(sides)

    # add the canvas
    self.canvas = LeapfrogCanvas(self.polygon, size=(1200, 1200))
    self.canvas.native.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
    self.setCentralWidget(self.canvas.native)

if __name__ == '__main__' and sys.flags.interactive == 0:
  main_app = qt.QApplication(sys.argv)
  window = Leapfrog()
  window.show()
  main_app.exec_()