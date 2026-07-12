#delauney feature python

import numpy as np
from scipy.stats import qmc
from scipy.spatial import Delaunay
import Part
from math import pi
V3 = App.Vector

class delauney_FP():
    def __init__(self, fp):
        fp.addProperty("App::PropertyFloat", "xsize", "Parameters", "x length of target rectangle").xsize = 2*pi*10
        fp.addProperty("App::PropertyFloat", "ysize", "Parameters", "y length of target rectangle").ysize = 40
        fp.addProperty("App::PropertyFloat", "mindist", "Parameters", "minimum distance between vertices").mindist = 5
        fp.addProperty("App::PropertyInteger", "npts", "Parameters", "number of points").npts = 80
        fp.addProperty("App::PropertyFloat", "offsetdist", "Parameters", "offset from triangles").offsetdist = -0.5
        fp.addProperty("App::PropertyFloat", "minaspect", "Parameters", "prune with height/base < minaspect").minaspect = 0.1
        fp.addProperty("App::PropertyBool", "periodic", "Parameters", "make periodic in x").periodic = True
        fp.Proxy = self

    def poissonPoints(self, fp):
        '''
        creates npts in a xmax x ymax rectangle randomly distributed at least radius apart
        '''
        rng = np.random.default_rng()
        engine = qmc.PoissonDisk(d=2, radius=fp.mindist, rng=rng, l_bounds =(0,0), u_bounds = (fp.xsize, fp.ysize))
        points = engine.random(fp.npts)
        return points

    def perioidicallyExtendPoints(self, fp, points):
        pointsm = [[ x - fp.xsize, y] for x, y in points]
        pointsp = [[ x + fp.xsize, y] for x, y in points]
        return np.vstack((pointsm, points, pointsp))

    def pointsToVertices(self, points):
        return [V3(x, y, 0) for x, y in points]

    def pruneWires(self, fp, wires):
        '''
        keep wires fully inside the xmax x ymax rectangle, plus those that overhang the xmax boundary if periodic
        '''
        pruned = list()
        for wire in wires:
            if any([v.Point.x < 0 for v in wire.Vertexes]):
                continue
            if fp.periodic:
                if all([v.Point.x > fp.xsize for v in wire.Vertexes]):
                    continue
            else:
                if any([v.Point.x > fp.xsize for v in wire.Vertexes]):
                    continue
            pruned.append(wire)
        return pruned

    def pruneSkinny(self, fp, wires):
        '''
        prune wires where height/base < self.minaspect
        '''
        fatList = list()
        for wire in wires:
            ar = 2* Part.makeFace(wire).Area/max([e.Length for e in wire.Edges])**2
            if ar > fp.minaspect:
                fatList.append(wire)
        return fatList

    def execute(self, fp):
        pointsa = self.poissonPoints(fp)
        if fp.periodic:
            points = self.perioidicallyExtendPoints(fp, pointsa)
        else:
            points = pointsa

        tri = Delaunay(points)
        wires = list()
        for simplex in tri.simplices:
            pts = [points[i] for i in simplex]
            vs = self.pointsToVertices(pts)
            vs.append(vs[0]) # make closed
            wire = Part.makePolygon(vs)
            wires.append(wire)

        #Part.show(Part.Compound(wires), 'Delauney')

        offsetWires = list()
        for wire in wires:
            try:
                offwire = wire.makeOffset2D(fp.offsetdist, join = 2, fill = False)
                offsetWires.append(offwire)
            except Exception as e:
                continue

        #Part.show(Part.Compound(offsetWires), 'OffsetWires')
        prunedOffsetWires = self.pruneWires(fp, offsetWires)
        #Part.show(Part.Compound(prunedOffsetWires), 'PrunedOffsetWires')
        fatWires = self.pruneSkinny(fp, prunedOffsetWires)
        #Part.show(Part.Compound(fatWires), 'fatWires')
        fp.Shape = Part.Compound(fatWires)

def makeDelauney(doc):
    a=doc.addObject("Part::FeaturePython","Delauney")
    delauney_FP(a)
    a.ViewObject.Proxy=0
    doc.recompute()
    return a

if __name__ == "__main__":
    doc = App.ActiveDocument if App.ActiveDocument else App.newDocument()
    makeDelauney(doc)





