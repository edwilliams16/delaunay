# make delaunay trianguled shape with offset.

import numpy as np
from scipy.stats import qmc
from scipy.spatial import Delaunay
import Part
from math import pi
V3 = App.Vector

def poissonPoints(radius, npts, xmax = 1.0, ymax = 1.0):
    '''
    creates npts in a xmax x ymax rectangle randomly distributed at least radius apart
    '''
    rng = np.random.default_rng()
    engine = qmc.PoissonDisk(d=2, radius=radius, rng=rng, l_bounds =(0,0), u_bounds = (xmax, ymax))
    points = engine.random(npts)
    return points

def perioidicallyExtendPoints(points, period):
    pointsm = [[ x-period, y] for x, y in points]
    pointsp = [[ x+period, y] for x, y in points]
    return np.vstack((pointsm, points, pointsp))



def pointsToVertices(points):
    return [V3(x, y, 0) for x, y in points]

def pruneWires(wires, period):
    '''
    keep wires fully inside the xmax x ymax rectangle, plus those that overhang the xmax boundary
    '''
    pruned = list()
    for wire in wires:
        if any([v.Point.x < 0 for v in wire.Vertexes]):
            continue
        if all([v.Point.x > period for v in wire.Vertexes]):
            continue
        pruned.append(wire)
    return pruned

def pruneSkinny(wires, minAspectRatio = 0.05):
    '''
    prune wires where height/base < minAspectRatio
    '''
    fatList = list()
    for wire in wires:
        ar = 2* Part.makeFace(wire).Area/max([e.Length for e in wire.Edges])**2
        if ar > minAspectRatio:
            fatList.append(wire)
    return fatList


#def triangulateDelauney(points):
    '''
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.Delaunay.html
    '''
xsize = 2*pi*10 #target rectangle - periodic direction
ysize = 40 # target rectangle y dimension
mindist = 5 #min distance between vertices
npts = 80 # number of vertices - roughly proportional to rectangle area/ mindist^2
pointsa = poissonPoints(mindist, npts, xmax = xsize, ymax = ysize)
points = perioidicallyExtendPoints(pointsa, xsize)
tri = Delaunay(points)
wires = list()
for simplex in tri.simplices:
    pts = [points[i] for i in simplex]
    vs = pointsToVertices(pts)
    vs.append(vs[0]) # make closed
    wire = Part.makePolygon(vs)
    wires.append(wire)

Part.show(Part.Compound(wires), 'Delauney')
offsetDistance = -0.5
offsetWires = list()
for wire in wires:
    try:
        offwire = wire.makeOffset2D(offsetDistance, join = 2, fill = False)
        offsetWires.append(offwire)
    except Exception as e:
        continue

Part.show(Part.Compound(offsetWires), 'OffsetWires')
prunedOffsetWires = pruneWires(offsetWires, xsize)
Part.show(Part.Compound(prunedOffsetWires), 'PrunedOffsetWires')
fatWires = pruneSkinny(prunedOffsetWires, 0.1)
Part.show(Part.Compound(fatWires), 'fatWires')