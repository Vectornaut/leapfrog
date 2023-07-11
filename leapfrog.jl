using LinearAlgebra

# the minkowski bilinear form
mprod(v, w) = dot(v[1:2], w[1:2]) - v[3]*w[3]

# reflect v over the plane orthogonal to m
reflect(m, v) = v - 2mprod(v, m)*m

struct SwathPolygon
  side       # represented as the spacelike vector orthogonal to the side
  vtx        # vtx[k] is the counterclockwise end of side[k]
  ang        # the angles of the vertices from the origin
  root
  swath_init # the clockwise edge of the swath
  swath_fin  # the counterclockwise edge of the swath
end

# if side k of p intersects the swath, flip the p over k
# otherwise, return nothing
function flip(p::SwathPolygon, k)
  k_next = (k + 1) % length(p.side)
  if p.ang[k_next] > p.ang[k] && p.ang[k_next] > p.swath_init && p.swath_fin > p.ang[k]
    side = [reflect(p.side[k], s) for s in p.side]
    vtx = [reflect(p.side[k], v) for v in p.vtx]
    ang = [atan(v[2], v[1]) for v in vtx]
    swath_init =
    SwathPolygon(side, vtx, ang, k
      [reflect(p.side[k], s) for s in p.side],
      [reflect(p.side[k], v) for v in p.vtx],
      ## ...
    )
  end
end