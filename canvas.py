from vispy import app, gloo
import vispy.util.keys as keys
from sage.all import AA ## just for printing swath edges

vertex = '''
attribute vec2 position;

void main() {
  gl_Position = vec4(position, 0., 1.);
}
'''

fragment = ('''
// display settings
uniform vec2 resolution;
uniform float shortdim;

// polygon
uniform int n_sides;
uniform vec3 sides [128];
uniform bool full_swath;
uniform vec2 swath_r;
uniform vec2 swath_l;

// --- minkowski geometry ---

// the minkowski bilinear form
float mprod(vec3 v, vec3 w) {
  return dot(v.xy, w.xy) - v.z*w.z;
}

bool right_of(vec2 v, vec2 w) {
  return v.x*w.y > w.x*v.y;
}

// --- swath polygon ---

const float VIEW = 1.1;
const float EPS = 1e-6;
const float TWIN_EPS = 1e-5;

void main() {
  // find screen coordinate
  vec2 u = VIEW*(2.*gl_FragCoord.xy - resolution) / shortdim;
  float r_sq = dot(u, u);
  
  // find pixel radius, for area sampling
  float r_px_screen = VIEW / shortdim; // the inner radius of a pixel in the Euclidean metric of the screen
  float r_px = 2.*r_px_screen / (1.-r_sq); // the approximate inner radius of our pixel in the hyperbolic metric

  // check containment
  if (r_sq < 1.) {
    vec3 v = vec3(2.*u, 1.+r_sq) / (1.-r_sq);
    float ang = atan(u.y, u.x);

    // check which side of each mirror we're on
    float max_mirror_prod;
    float nearest_mirror = -1;
    for (int k = 0; k < n_sides; k++) {
      float mirror_prod = mprod(v, sides[k]);
      if (nearest_mirror < 0 || mirror_prod > max_mirror_prod) {
        max_mirror_prod = mirror_prod;
        nearest_mirror = k;
      }
      if (mirror_prod > 0.) {
        // we're on the outer side of a mirror, so we're outside the polygon
        vec3 color = vec3(0.4);
        if (!full_swath && (right_of(swath_l, v.xy) || right_of(v.xy, swath_r))) {
          color *= 0.5;
        }
        gl_FragColor = vec4(color, 1.);
        return;
      }
    }

    // we're on the inward side of every mirror, so we're inside the polygon
    vec3 color;
    if (max_mirror_prod > -0.1) {
      if (nearest_mirror == 0) color = vec3(1., 0., 0.);
      else if (nearest_mirror == 1) color = vec3(1., 0.5, 0.);
      else if (nearest_mirror == 2) color = vec3(1., 0.9, 0.);
      else if (nearest_mirror == 3) color = vec3(0., 1., 0.);
      else if (nearest_mirror == 4) color = vec3(0., 0., 1.);
      else if (nearest_mirror == 5) color = vec3(0.5, 0., 1.);
      else color = vec3(1., 0., 1.);
    } else {
      color = vec3(1.);
    }
    if (!full_swath && (right_of(swath_l, v.xy) || right_of(v.xy, swath_r))) {
      color *= 0.5;
    }
    gl_FragColor = vec4(color, 1.);
    return;
  }
  gl_FragColor = vec4(vec3(0.), 1.);
}
''')

class LeapfrogCanvas(app.Canvas):
  def __init__(self, polygon, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.program = gloo.Program(vertex, fragment, count = 6) # we'll always send 6 vertices
    
    # draw a rectangle that covers the canvas
    self.program['position'] = [
      (-1, -1), (-1, 1), (1, 1), # northwest triangle
      (-1, -1), (1, 1), (1, -1)  # southeast triangle
    ]
    
    # initialize resolution
    self.update_resolution()

    # initialize polygon
    self.set_polygon(polygon)

  def update_resolution(self, size=None):
    width, height = size if size else self.physical_size
    gloo.set_viewport(0, 0, width, height)
    self.program['resolution'] = [width, height]
    self.program['shortdim'] = min(width, height)

  def set_polygon(self, polygon):
    self.polygon = polygon
    n_sides = len(polygon.sides)
    self.program['n_sides'] = n_sides
    for k in range(n_sides):
      self.program['sides[{}]'.format(k)] = polygon.sides[k]
    for k in range(n_sides, 128):
      self.program['sides[{}]'.format(k)] = [0, 0, 0]
    self.program['full_swath'] = polygon.full_swath
    if polygon.full_swath:
      self.program['swath_r'] = [0, 0];
      self.program['swath_l'] = [0, 0];
    else:
      print('swath_r: ', list(map(AA, polygon.swath_r)))
      print('swath_l: ', list(map(AA, polygon.swath_l)))
      print('------')
      self.program['swath_r'] = polygon.swath_r
      self.program['swath_l'] = polygon.swath_l

  def on_draw(self, event):
    self.program.draw()
  
  def on_resize(self, event):
    self.update_resolution()

  def on_key_press(self, event):
    for k in range(len(self.polygon.sides)):
      if event.key == str(k+1):
        flipped = self.polygon.flip(k)
        if not flipped is None:
          print('flip side {}'.format(k+1))
          self.set_polygon(flipped)
          self.update()
          break
        else:
          print("swath doesn't cross side {}".format(k+1))