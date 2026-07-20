```
 Name:             Delaunay_FP
 Version:          1.0.
 Date:             2026-07-18
 Author:           Ed Williams
 Contact/Forum:    edwilliams16
 License:          LGPL-2.1
 Description:      Creates  random points in a rectangle a minimum distance apart
                   It then Delaunay triangulates them. There is an option to make
                   the triangulation periodic in one (x) direction.
                   Using the Curves Workbench Sketch on Surface or Map On Face
                   tools, you can apply the pattern to a surface, creating a
                   random array of triangular holes, indentations or protrusions.
 Properties        xsize:  target rectangle x length
                   ysize:  target rectangle y length
                   periodic: Boolean True pattern is periodic in x
                   mindist: minimum distance between otherwise random points
                   npts:  desired number of points - setting to 0 requests
                          a maximum possible number of points.  The number
                          obtained will be less than this, because the random
                          points are not optimally packed. See report view
                          messages.
                   offsetdist:  if 0.0 the output is a compound of Delaunay
                          triangles. When < 0 the triangles are each offset
                          inward by |offsetdistance|
                   randomseed:  change this to get a different random realization
                   You can remove possibly undesired triangles with the Pruning
                   parameters.
                   percentbyarea:  keep only this percentage of triangles
                          ordered by area.
                   minaspect: This prunes skinny triangles with
                          height/base < minaspect

 Output             A compound of triangular wires and a rectangular xsize * ysize
                          sketch
 ==============================================================================
 Usage:
 1. Open the FreeCAD document you want to modify.
 2. Open this macro in FreeCAD (Macro -> Macros -> Edit).
 3. Click "Execute".
 ==============================================================================
```
