#delaunay feature python

import numpy as np
from scipy.stats import qmc
from scipy.spatial import Delaunay
import Part
from math import pi
V3 = App.Vector

class delaunay_FP():
    def __init__(self, fp):
        fp.addProperty("App::PropertyFloat", "xsize", "Parameters", "x length of target rectangle").xsize = 2*pi*10
        fp.addProperty("App::PropertyFloat", "ysize", "Parameters", "y length of target rectangle").ysize = 40
        fp.addProperty("App::PropertyFloat", "mindist", "Parameters", "minimum distance between vertices").mindist = 5
        fp.addProperty("App::PropertyInteger", "npts", "Parameters", "number of points (0 -> max)").npts = 100
        fp.addProperty("App::PropertyFloat", "offsetdist", "Parameters", "offset from triangles").offsetdist = -0.5
        fp.addProperty("App::PropertyFloat", "minaspect", "Pruning", "prune with height/base < minaspect").minaspect = 0.1
        fp.addProperty("App::PropertyBool", "periodic", "Parameters", "make periodic in x").periodic = True
        fp.addProperty("App::PropertyInteger", "randomseed", "Parameters", "seed for random generator").randomseed = 1234
        fp.addProperty("App::PropertyFloat", "percentbyarea", "Pruning", "prune by area").percentbyarea = 100
        fp.Proxy = self
        #self.usingMax = True
        #self.maxnpts = int(fp.xsize *fp.ysize /(0.866 * fp.mindist**2)) #close packed array

    def poissonPoints(self, fp):
        '''
        creates npts in a xsize x ysize rectangle randomly distributed at least mindist apart
        '''
        rng = np.random.default_rng(seed = fp.randomseed)
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

    def pruneSmall(self, fp, wires):
        if len(wires) > 0:
            sortedwires = sorted(wires, key = lambda wire: -Part.makeFace(wire).Area ) #decreasing area
            numberbigwires = round((fp.percentbyarea/100)*len(wires))
            return sortedwires[:numberbigwires]
        else:
            return wires

    def execute(self, fp):
        #limit 3 <= npts <= maxnpts else set to max(3,maxnpts)
        maxnpts = max(3,int(fp.xsize *fp.ysize /(0.866 * fp.mindist**2))) #close packed array
        if fp.npts < 3 or fp.npts > maxnpts:
            fp.npts = maxnpts

        fp.percentbyarea = min(100, max(0, fp.percentbyarea))
        fp.minaspect = max(0, fp.minaspect)

        pointsa = self.poissonPoints(fp)
        App.Console.PrintMessage(f'number of points made {len(pointsa)} asked  {fp.npts}\n')
        if len(pointsa) < 3:
            App.Console.PrintMessage('Not enough points created to triangulate\n')
            fp.Shape = Part.Shape()
            return

        if fp.periodic:
            points = self.perioidicallyExtendPoints(fp, pointsa)
        else:
            points = pointsa

        tri = Delaunay(points, qhull_options = "QJ")
        wires = list()
        for simplex in tri.simplices:
            pts = [points[i] for i in simplex]
            vs = self.pointsToVertices(pts)
            vs.append(vs[0]) # make closed
            wire = Part.makePolygon(vs)
            wires.append(wire)

        #Part.show(Part.Compound(wires), 'Delaunay')

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
        bigWires = self.pruneSmall(fp, fatWires)
        #Part.show(Part.Compound(fatWires), 'fatWires')
        fp.Shape = Part.Compound(bigWires)
        App.Console.PrintMessage(f'No. triangles: {len(bigWires)}, no. pruned: {len(prunedOffsetWires) - len(bigWires)}\n')


def makeDelaunay(doc):
    a=doc.addObject("Part::FeaturePython","Delaunay")
    delaunay_FP(a)
    a.ViewObject.Proxy=0
    doc.recompute()
    return a

def createSketch(doc, delaunayname):
    '''
    creates target xsize * ysize rectangle sketch
    '''
    Sketch = doc.addObject('Sketcher::SketchObject', 'Sketch')
    geo0 = Sketch.addGeometry(Part.LineSegment(V3 (0.0, 0.0, 0.0), V3(20*pi, 0.0, 0.0)))
    geo1 = Sketch.addGeometry(Part.LineSegment(V3(20*pi, 0.0, 0.0), V3(20*pi, 40.0, 0.0)))
    geo2 = Sketch.addGeometry(Part.LineSegment(V3(20*pi, 40.0, 0.0), V3(0.0, 40.0, 0.0)))
    geo3 = Sketch.addGeometry(Part.LineSegment(V3(0.0, 40.0, 0.0), V3(0.0, 0.0, 0.0)))
    Sketch.addConstraint(Sketcher.Constraint('Coincident', geo0, 2, geo1, 1))
    Sketch.addConstraint(Sketcher.Constraint('Coincident', geo1, 2, geo2, 1))
    Sketch.addConstraint(Sketcher.Constraint('Coincident', geo2, 2, geo3, 1))
    Sketch.addConstraint(Sketcher.Constraint('Coincident', geo3, 2, geo0, 1))
    Sketch.addConstraint(Sketcher.Constraint('Horizontal', geo0))
    Sketch.addConstraint(Sketcher.Constraint('Horizontal', geo2))
    Sketch.addConstraint(Sketcher.Constraint('Vertical', geo1))
    Sketch.addConstraint(Sketcher.Constraint('Vertical', geo3))
    Sketch.addConstraint(Sketcher.Constraint('Coincident', geo0, 1, -1, 1))
    Sketch.addConstraint(Sketcher.Constraint('DistanceY', geo1, 1, geo1, 2, 40.0))
    Sketch.addConstraint(Sketcher.Constraint('DistanceX', geo2, 2, geo2, 1, 20*pi))
    Sketch.setExpression('Constraints[10]', f'{delaunayname}.xsize')
    Sketch.setExpression('Constraints[9]', f'{delaunayname}.ysize')
    return Sketch



if __name__ == "__main__":
    doc = App.ActiveDocument if App.ActiveDocument else App.newDocument()
    delaunay = makeDelaunay(doc)
    targetSketch = createSketch(doc, delaunay.Name)
    targetSketch.Visibility = True
    doc.recompute()
    Gui.SendMsgToActiveView("ViewFit")





