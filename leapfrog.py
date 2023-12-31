import sys, os, re, json
import PyQt5.QtWidgets as qt
from PyQt5.QtCore import Qt
from vispy import app
import vispy.io as io
from sage.all import (
  sqrt, pi, cos, sin, chebyshev_T, chebyshev_U,
  ZZ, number_field_elements_from_algebraics, AA,
  FreeModule, matrix
)

from canvas import LeapfrogCanvas

app.use_app(backend_name='PyQt5', call_reuse=True)

# reflect v over the plane orthogonal to m
def reflect(m, v):
  return v - 2*v.inner_product(m)*m

# the lorentzian cross product
def lorentz_cross(v, w):
  return v.parent()([
    -v[1]*w[2] + v[2]*w[1],
    -v[2]*w[0] + v[0]*w[2],
     v[0]*w[1] - v[1]*w[0]
  ])

def right_of(v, w):
  return v[0]*w[1] > w[0]*v[1]

class SwathPolygon:
  # `sides` is the list of spacelike vectors orthogonal to the polygon's sides,
  # ordered counterclockwise around the polygon when `side_order` is 1 and
  # clockwise when `side_order` is -1. `vtx[k-1]` and `vtex[k]` are the ends of
  # side k, ordered around the polygon according to the side order
  def __init__(self, sides, vtx, side_order, swath_r = None, swath_l = None):
    self.sides = sides
    self.vtx = vtx
    self.side_order = side_order
    self.swath_r = swath_r
    self.swath_l = swath_l
    self.full_swath = swath_r is None and swath_l is None

  def flip(self, k):
    # the spacial vectors end_r and end_l point from the origin toward the
    # right and left ends of side k, where right and left are measured as seen
    # from inside the polygon
    if self.side_order > 0:
      end_r = self.vtx[k-1][:-1]
      end_l = self.vtx[k][:-1]
    else:
      end_r = self.vtx[k][:-1]
      end_l = self.vtx[k-1][:-1]
    
    # does the chosen side's orientation, as seen from the origin, match its
    # orientation as seen from inside the polygon?
    side_faces_outward = right_of(end_r, end_l)

    # does the swath of geodesics consistent with the trajectory so far go
    # through the chosen side?
    swath_hits_side = (
      self.full_swath
      or (right_of(self.swath_r, end_l) and right_of(end_r, self.swath_l))
    )

    if side_faces_outward and swath_hits_side:
      # some of the geodesics in the swath can continue through the chosen side,
      # because we answered yes to both of the questions above

      # cut down the swath of geodesics, keeping only the ones that go through
      # the chosen side
      if self.full_swath:
        swath_r = end_r
        swath_l = end_l
      else:
        swath_r = end_r if right_of(self.swath_r, end_r) else self.swath_r
        swath_l = end_l if right_of(end_l, self.swath_l) else self.swath_l
      
      # flip the polygon over the chosen side
      return SwathPolygon(
        [reflect(self.sides[k], s) for s in self.sides],
        [reflect(self.sides[k], v) for v in self.vtx],
        -self.side_order,
        swath_r,
        swath_l
      )
    else:
      # none of the geodesics in the swath can continue through the chosen side
      return None

# build a swath polygon from a list of sides. the sides have to be ordered
# counterclockwise (the function doesn't check this condition)
def swath_polygon_from_sides(sides, swath_r = None, swath_l = None):
  vtx = []
  for k in range(len(sides)):
    vtx.append(lorentz_cross(sides[k], sides[(k+1) % len(sides)]))
  return SwathPolygon(sides, vtx, 1, swath_r, swath_l)

class Leapfrog(qt.QMainWindow):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.setWindowTitle('Leapfrog')
    self.resize(900, 900)

    # --- construct a p-gon that tiles with q copies around each vertex ---
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

    # build an algebraic number field K that contains the entries of the
    # polygon's side normals
    p = 6
    q = 4
    cp_symb = cos(pi/p)
    sp_symb = sin(pi/p)
    cq_symb = cos(pi/q)
    sq_symb = sin(pi/q)
    a_symb = cq_symb / sp_symb
    b_symb = sqrt(a_symb**2 - 1)
    K, (cp, sp, cq, sq, b), _ = number_field_elements_from_algebraics(
      [cp_symb, sp_symb, cq_symb, sq_symb, b_symb],
      minimal=True, embedded=True
    )
    a = cq / sp
    print(K)

    # construct the Minkowski spacetime K^(2,1)
    lorentz_form = matrix(ZZ, [[1, 0, 0], [0, 1, 0], [0, 0, -1]])
    M = FreeModule(K, 3, inner_product_matrix = lorentz_form)

    # build the polygon from its side normals
    sides = [M([
      a*chebyshev_T(2*k, cp),      # a*cos(2*k*pi/p)
      a*chebyshev_U(2*k-1, cp)*sp, # a*sin(2*k*pi/p)
      b
    ]) for k in range(p)]
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