# -*- coding: utf-8 -*-
"""
graphicsItems.py -  Defines several graphics item classes for use in Qt graphics/view framework
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.

Provides ImageItem, PlotCurveItem, and ViewBox, amongst others.
"""
from itertools import izip


from PyQt4 import QtGui, QtCore

if not hasattr(QtCore, 'Signal'):
    QtCore.Signal = QtCore.pyqtSignal
#from ObjectWorkaround import *
#tryWorkaround(QtCore, QtGui)
#from numpy import *
import numpy as np
try:
    import scipy.weave as weave
    from scipy.weave import converters
except:
    pass
from scipy.fftpack import fft
from scipy.signal import resample
import scipy.stats
#from metaarray import MetaArray
from Point import *
from functions import *
import sys, struct, os
import weakref
#import debug
#from debug import *

## QGraphicsObject didn't appear until 4.6; this is for compatibility with 4.5
if not hasattr(QtGui, 'QGraphicsObject'):
    class QGraphicsObject(QtGui.QGraphicsWidget):
        def shape(self):
            return QtGui.QGraphicsItem.shape(self)
    QtGui.QGraphicsObject = QGraphicsObject


## Should probably just use QGraphicsGroupItem and instruct it to pass events on to children..
class ItemGroup(QtGui.QGraphicsItem):
    def __init__(self, *args):
        QtGui.QGraphicsItem.__init__(self, *args)
        if hasattr(self, "ItemHasNoContents"):
            self.setFlag(self.ItemHasNoContents)
    
    def boundingRect(self):
        return QtCore.QRectF()
        
    def paint(self, *args):
        pass
    
    def addItem(self, item):
        item.setParentItem(self)


#if hasattr(QtGui, "QGraphicsObject"):
    #QGraphicsObject = QtGui.QGraphicsObject
#else:
    #class QObjectWorkaround:
        #def __init__(self):
            #self._qObj_ = QtCore.QObject()
        #def connect(self, *args):
            #return QtCore.QObject.connect(self._qObj_, *args)
        #def disconnect(self, *args):
            #return QtCore.QObject.disconnect(self._qObj_, *args)
        #def emit(self, *args):
            #return QtCore.QObject.emit(self._qObj_, *args)
            
    #class QGraphicsObject(QtGui.QGraphicsItem, QObjectWorkaround):
        #def __init__(self, *args):
            #QtGui.QGraphicsItem.__init__(self, *args)
            #QObjectWorkaround.__init__(self)

    
    
class GraphicsObject(QtGui.QGraphicsObject):
    """Extends QGraphicsObject with a few important functions. 
    (Most of these assume that the object is in a scene with a single view)"""
    
    def __init__(self, *args):
        QtGui.QGraphicsObject.__init__(self, *args)
        self._view = None
    
    def getViewWidget(self):
        """Return the view widget for this item. If the scene has multiple views, only the first view is returned.
        the view is remembered for the lifetime of the object, so expect trouble if the object is moved to another view."""
        if self._view is None:
            scene = self.scene()
            if scene is None:
                return None
            views = scene.views()
            if len(views) < 1:
                return None
            self._view = weakref.ref(self.scene().views()[0])
        return self._view()
    
    def getBoundingParents(self):
        """Return a list of parents to this item that have child clipping enabled."""
        p = self
        parents = []
        while True:
            p = p.parentItem()
            if p is None:
                break
            if p.flags() & self.ItemClipsChildrenToShape:
                parents.append(p)
        return parents
    
    def viewBounds(self):
        """Return the allowed visible boundaries for this item. Takes into account the viewport as well as any parents that clip."""
        bounds = QtCore.QRectF(0, 0, 1, 1)
        view = self.getViewWidget()
        if view is None:
            return None
        bounds = self.mapRectFromScene(view.visibleRange())
        
        for p in self.getBoundingParents():
            bounds &= self.mapRectFromScene(p.sceneBoundingRect())
            
        return bounds
        
    def viewTransform(self):
        """Return the transform that maps from local coordinates to the item's view coordinates"""
        view = self.getViewWidget()
        if view is None:
            return None
        return self.deviceTransform(view.viewportTransform())

    def pixelVectors(self):
        """Return vectors in local coordinates representing the width and height of a view pixel."""
        vt = self.viewTransform()
        if vt is None:
            return None
        vt = vt.inverted()[0]
        orig = vt.map(QtCore.QPointF(0, 0))
        return vt.map(QtCore.QPointF(1, 0))-orig, vt.map(QtCore.QPointF(0, 1))-orig

    def pixelWidth(self):
        vt = self.viewTransform()
        if vt is None:
            return 0
        vt = vt.inverted()[0]
        return abs((vt.map(QtCore.QPointF(1, 0))-vt.map(QtCore.QPointF(0, 0))).x())
        
    def pixelHeight(self):
        vt = self.viewTransform()
        if vt is None:
            return 0
        vt = vt.inverted()[0]
        return abs((vt.map(QtCore.QPointF(0, 1))-vt.map(QtCore.QPointF(0, 0))).y())

    def mapToView(self, obj):
        vt = self.viewTransform()
        if vt is None:
            return None
        return vt.map(obj)
        
    def mapRectToView(self, obj):
        vt = self.viewTransform()
        if vt is None:
            return None
        return vt.mapRect(obj)
        
    def mapFromView(self, obj):
        vt = self.viewTransform()
        if vt is None:
            return None
        vt = vt.inverted()[0]
        return vt.map(obj)

    def mapRectFromView(self, obj):
        vt = self.viewTransform()
        if vt is None:
            return None
        vt = vt.inverted()[0]
        return vt.mapRect(obj)
        
        
        
        

class ImageItem(QtGui.QGraphicsObject):
    
    sigImageChanged = QtCore.Signal()
    
    if 'linux' not in sys.platform:  ## disable weave optimization on linux--broken there.
        useWeave = True
    else:
        useWeave = False
    
    def __init__(self, image=None, copy=True, parent=None, border=None, *args):
        #QObjectWorkaround.__init__(self)
        QtGui.QGraphicsObject.__init__(self)
        #self.pixmapItem = QtGui.QGraphicsPixmapItem(self)
        self.qimage = QtGui.QImage()
        self.pixmap = None
        #self.useWeave = True
        self.blackLevel = None
        self.whiteLevel = None
        self.alpha = 1.0
        self.image = None
        self.clipLevel = None
        self.drawKernel = None
        if border is not None:
            border = mkPen(border)
        self.border = border
        
        #QtGui.QGraphicsPixmapItem.__init__(self, parent, *args)
        #self.pixmapItem = QtGui.QGraphicsPixmapItem(self)
        if image is not None:
            self.updateImage(image, copy, autoRange=True)
        #self.setCacheMode(QtGui.QGraphicsItem.DeviceCoordinateCache)
        
    def setAlpha(self, alpha):
        self.alpha = alpha
        self.updateImage()
        
    #def boundingRect(self):
        #return self.pixmapItem.boundingRect()
        #return QtCore.QRectF(0, 0, self.qimage.width(), self.qimage.height())
        
    def width(self):
        if self.pixmap is None:
            return None
        return self.pixmap.width()
        
    def height(self):
        if self.pixmap is None:
            return None
        return self.pixmap.height()

    def boundingRect(self):
        if self.pixmap is None:
            return QtCore.QRectF(0., 0., 0., 0.)
        return QtCore.QRectF(0., 0., float(self.width()), float(self.height()))

    def setClipLevel(self, level=None):
        self.clipLevel = level
        
    #def paint(self, p, opt, widget):
        #pass
        #if self.pixmap is not None:
            #p.drawPixmap(0, 0, self.pixmap)
            #print "paint"

    def setLevels(self, white=None, black=None):
        if white is not None:
            self.whiteLevel = white
        if black is not None:
            self.blackLevel = black  
        self.updateImage()
        
    def getLevels(self):
        return self.whiteLevel, self.blackLevel

    def updateImage(self, image=None, copy=True, autoRange=False, clipMask=None, white=None, black=None, axes=None):
        if axes is None:
            axh = {'x': 0, 'y': 1, 'c': 2}
        else:
            axh = axes
        #print "Update image", black, white
        if white is not None:
            self.whiteLevel = white
        if black is not None:
            self.blackLevel = black  
        
        gotNewData = False
        if image is None:
            if self.image is None:
                return
        else:
            gotNewData = True
            if self.image is None or image.shape != self.image.shape:
                self.prepareGeometryChange()
            if copy:
                self.image = image.view(np.ndarray).copy()
            else:
                self.image = image.view(np.ndarray)
        #print "  image max:", self.image.max(), "min:", self.image.min()
        
        # Determine scale factors
        if autoRange or self.blackLevel is None:
            if self.image.dtype is np.ubyte:
                self.blackLevel = 0
                self.whiteLevel = 255
            else:
                self.blackLevel = self.image.min()
                self.whiteLevel = self.image.max()
        #print "Image item using", self.blackLevel, self.whiteLevel
        
        if self.blackLevel != self.whiteLevel:
            scale = 255. / (self.whiteLevel - self.blackLevel)
        else:
            scale = 0.
        
        
        ## Recolor and convert to 8 bit per channel
        # Try using weave, then fall back to python
        shape = self.image.shape
        black = float(self.blackLevel)
        try:
            if not ImageItem.useWeave:
                raise Exception('Skipping weave compile')
            sim = np.ascontiguousarray(self.image)
            sim.shape = sim.size
            im = np.empty(sim.shape, dtype=np.ubyte)
            n = im.size
            
            code = """
            for( int i=0; i<n; i++ ) {
                float a = (sim(i)-black) * (float)scale;
                if( a > 255.0 )
                    a = 255.0;
                else if( a < 0.0 )
                    a = 0.0;
                im(i) = a;
            }
            """
            
            weave.inline(code, ['sim', 'im', 'n', 'black', 'scale'], type_converters=converters.blitz, compiler = 'gcc')
            sim.shape = shape
            im.shape = shape
        except:
            if ImageItem.useWeave:
                ImageItem.useWeave = False
                #sys.excepthook(*sys.exc_info())
                #print "=============================================================================="
                print "Weave compile failed, falling back to slower version."
            self.image.shape = shape
            im = ((self.image - black) * scale).clip(0.,255.).astype(np.ubyte)

        try:
            im1 = np.empty((im.shape[axh['y']], im.shape[axh['x']], 4), dtype=np.ubyte)
        except:
            print im.shape, axh
            raise
        alpha = np.clip(int(255 * self.alpha), 0, 255)
        # Fill image 
        if im.ndim == 2:
            im2 = im.transpose(axh['y'], axh['x'])
            im1[..., 0] = im2
            im1[..., 1] = im2
            im1[..., 2] = im2
            im1[..., 3] = alpha
        elif im.ndim == 3: #color image
            im2 = im.transpose(axh['y'], axh['x'], axh['c'])
            ##      [B G R A]    Reorder colors
            order = [2,1,0,3] ## for some reason, the colors line up as BGR in the final image.
            
            for i in range(0, im.shape[axh['c']]):
                im1[..., order[i]] = im2[..., i]    
            
            ## fill in unused channels with 0 or alpha
            for i in range(im.shape[axh['c']], 3):
                im1[..., i] = 0
            if im.shape[axh['c']] < 4:
                im1[..., 3] = alpha
                
        else:
            raise Exception("Image must be 2 or 3 dimensions")
        #self.im1 = im1
        # Display image
        
        if self.clipLevel is not None or clipMask is not None:
                if clipMask is not None:
                        mask = clipMask.transpose()
                else:
                        mask = (self.image < self.clipLevel).transpose()
                im1[..., 0][mask] *= 0.5
                im1[..., 1][mask] *= 0.5
                im1[..., 2][mask] = 255
        #print "Final image:", im1.dtype, im1.min(), im1.max(), im1.shape
        self.ims = im1.tostring()  ## Must be held in memory here because qImage won't do it for us :(
        qimage = QtGui.QImage(buffer(self.ims), im1.shape[1], im1.shape[0], QtGui.QImage.Format_ARGB32)
        self.pixmap = QtGui.QPixmap.fromImage(qimage)
        ##del self.ims
        #self.pixmapItem.setPixmap(self.pixmap)
        
        self.update()
        
        if gotNewData:
            #self.emit(QtCore.SIGNAL('imageChanged'))
            self.sigImageChanged.emit()
        
    def getPixmap(self):
        return self.pixmap.copy()

    def getHistogram(self, bins=500, step=3):
        """returns an x and y arrays containing the histogram values for the current image.
        The step argument causes pixels to be skipped when computing the histogram to save time."""
        stepData = self.image[::step, ::step]
        hist = np.histogram(stepData, bins=bins)
        return hist[1][:-1], hist[0]
        
    def mousePressEvent(self, ev):
        if self.drawKernel is not None and ev.button() == QtCore.Qt.LeftButton:
            self.drawAt(ev.pos())
            ev.accept()
        else:
            ev.ignore()
        
    def mouseMoveEvent(self, ev):
        #print "mouse move", ev.pos()
        if self.drawKernel is not None:
            self.drawAt(ev.pos())
    
    def mouseReleaseEvent(self, ev):
        pass
    
    def drawAt(self, pos):
        self.image[int(pos.x()), int(pos.y())] += 1
        self.updateImage()
        
    def setDrawKernel(self, kernel=None):
        self.drawKernel = kernel
    
    def paint(self, p, *args):
        
        #QtGui.QGraphicsPixmapItem.paint(self, p, *args)
        if self.pixmap is None:
            return
            
        p.drawPixmap(self.boundingRect(), self.pixmap, QtCore.QRectF(0, 0, self.pixmap.width(), self.pixmap.height()))
        if self.border is not None:
            p.setPen(self.border)
            p.drawRect(self.boundingRect())

    def pixelSize(self):
        """return size of a single pixel in the image"""
        br = self.sceneBoundingRect()
        return br.width()/self.pixmap.width(), br.height()/self.pixmap.height()


class PlotCurveItem(GraphicsObject):
    
    sigPlotChanged = QtCore.Signal(object)
    
    """Class representing a single plot curve."""
    
    sigClicked = QtCore.Signal(object)
    
    def __init__(self, y=None, x=None, copy=False, pen=None, shadow=None, parent=None, color=None, clickable=False):
        GraphicsObject.__init__(self, parent)
        self.free()
        #self.dispPath = None
        self.highlighted=False
        #self.setAcceptHoverEvents(True)
        
        if pen is None:
            if color is None:
                self.setPen((200,200,200))
            else:
                self.setPen(color)
        else:
            self.setPen(pen)
        
        self.shadow = shadow
        if y is not None:
            self.updateData(y, x, copy)
        #self.setCacheMode(QtGui.QGraphicsItem.DeviceCoordinateCache)
        
        self.metaData = {}
        self.opts = {
            'spectrumMode': False,
            'logMode': [False, False],
            'pointMode': False,
            'pointStyle': None,
            'downsample': False,
            'alphaHint': 1.0,
            'alphaMode': False
        }
            
        self.setClickable(clickable)
        #self.fps = None
        
    def setClickable(self, s):
        self.clickable = s
        
    
    def setHighlighted(self, boolean):
        self.highlighted=boolean
    
    def getData(self):
        if self.xData is None:
            return (None, None)
        if self.xDisp is None:
            nanMask = np.isnan(self.xData) | np.isnan(self.yData)
            if any(nanMask):
                x = self.xData[~nanMask]
                y = self.yData[~nanMask]
            else:
                x = self.xData
                y = self.yData
            ds = self.opts['downsample']
            if ds > 1:
                x = x[::ds]
                y = resample(y[:len(x)*ds], len(x))
            if self.opts['spectrumMode']:
                f = fft(y) / len(y)
                y = abs(f[1:len(f)/2])
                dt = x[-1] - x[0]
                x = np.linspace(0, 0.5*len(x)/dt, len(y))
            if self.opts['logMode'][0]:
                x = np.log10(x)
            if self.opts['logMode'][1]:
                y = np.log10(y)
            self.xDisp = x
            self.yDisp = y
        #print self.yDisp.shape, self.yDisp.min(), self.yDisp.max()
        #print self.xDisp.shape, self.xDisp.min(), self.xDisp.max()
        return self.xDisp, self.yDisp
            
    #def generateSpecData(self):
        #f = fft(self.yData) / len(self.yData)
        #self.ySpec = abs(f[1:len(f)/2])
        #dt = self.xData[-1] - self.xData[0]
        #self.xSpec = linspace(0, 0.5*len(self.xData)/dt, len(self.ySpec))
        
    def getRange(self, ax, frac=1.0):
        #print "getRange", ax, frac
        (x, y) = self.getData()
        if x is None or len(x) == 0:
            return (0, 1)
            
        if ax == 0:
            d = x
        elif ax == 1:
            d = y
            
        if frac >= 1.0:
            return (d.min(), d.max())
        elif frac <= 0.0:
            raise Exception("Value for parameter 'frac' must be > 0. (got %s)" % str(frac))
        else:
            return (scipy.stats.scoreatpercentile(d, 50 - (frac * 50)), scipy.stats.scoreatpercentile(d, 50 + (frac * 50)))
            #bins = 1000
            #h = histogram(d, bins)
            #s = len(d) * (1.0-frac)
            #mnTot = mxTot = 0
            #mnInd = mxInd = 0
            #for i in range(bins):
                #mnTot += h[0][i]
                #if mnTot > s:
                    #mnInd = i
                    #break
            #for i in range(bins):
                #mxTot += h[0][-i-1]
                #if mxTot > s:
                    #mxInd = -i-1
                    #break
            ##print mnInd, mxInd, h[1][mnInd], h[1][mxInd]
            #return(h[1][mnInd], h[1][mxInd])
                
            
            
        
    def setMeta(self, data):
        self.metaData = data
        
    def meta(self):
        return self.metaData
        
    def setPen(self, pen):
        self.pen = mkPen(pen)
        self.update()
        
    def setColor(self, color):
        self.pen.setColor(color)
        self.update()
        
    def setAlpha(self, alpha, auto):
        self.opts['alphaHint'] = alpha
        self.opts['alphaMode'] = auto
        self.update()
        
    def setSpectrumMode(self, mode):
        self.opts['spectrumMode'] = mode
        self.xDisp = self.yDisp = None
        self.path = None
        self.update()
    
    def setLogMode(self, mode):
        self.opts['logMode'] = mode
        self.xDisp = self.yDisp = None
        self.path = None
        self.update()
    
    def setPointMode(self, mode):
        self.opts['pointMode'] = mode
        self.update()
        
    def setShadowPen(self, pen):
        self.shadow = pen
        self.update()

    def setDownsampling(self, ds):
        if self.opts['downsample'] != ds:
            self.opts['downsample'] = ds
            self.xDisp = self.yDisp = None
            self.path = None
            self.update()

    def setData(self, x, y, copy=False):
        """For Qwt compatibility"""
        self.updateData(y, x, copy)
        
    def updateData(self, data, x=None, copy=False):
        #prof = debug.Profiler('PlotCurveItem.updateData', disabled=True)
        if isinstance(data, list):
            data = np.array(data)
        if isinstance(x, list):
            x = np.array(x)
        if not isinstance(data, np.ndarray) or data.ndim > 2:
            raise Exception("Plot data must be 1 or 2D ndarray (data shape is %s)" % str(data.shape))
        if x == None:
            if 'complex' in str(data.dtype):
                raise Exception("Can not plot complex data types.")
        else:
            if 'complex' in str(data.dtype)+str(x.dtype):
                raise Exception("Can not plot complex data types.")
        
        if data.ndim == 2:  ### If data is 2D array, then assume x and y values are in first two columns or rows.
            if x is not None:
                raise Exception("Plot data may be 2D only if no x argument is supplied.")
            ax = 0
            if data.shape[0] > 2 and data.shape[1] == 2:
                ax = 1
            ind = [slice(None), slice(None)]
            ind[ax] = 0
            y = data[tuple(ind)]
            ind[ax] = 1
            x = data[tuple(ind)]
        elif data.ndim == 1:
            y = data
        #prof.mark("data checks")
        self.prepareGeometryChange()
        if copy:
            self.yData = y.copy()
        else:
            self.yData = y
            
        if copy and x is not None:
            self.xData = x.copy()
        else:
            self.xData = x
        #prof.mark('copy')
        
        if x is None:
            self.xData = np.arange(0, self.yData.shape[0])

        if self.xData.shape != self.yData.shape:
            raise Exception("X and Y arrays must be the same shape--got %s and %s." % (str(x.shape), str(y.shape)))
        
        self.path = None
        self.xDisp = self.yDisp = None
        
        #prof.mark('set')
        self.update()
        #prof.mark('update')
        #self.emit(QtCore.SIGNAL('plotChanged'), self)
        self.sigPlotChanged.emit(self)
        #prof.mark('emit')
        #prof.finish()
        
    def generatePath(self, x, y):
        path = QtGui.QPainterPath()
        
        ## Create all vertices in path. The method used below creates a binary format so that all 
        ## vertices can be read in at once. This binary format may change in future versions of Qt, 
        ## so the original (slower) method is left here for emergencies:
        #path.moveTo(x[0], y[0])
        #for i in range(1, y.shape[0]):
        #    path.lineTo(x[i], y[i])
            
        ## Speed this up using >> operator
        ## Format is:
        ##    numVerts(i4)   0(i4)
        ##    x(f8)   y(f8)   0(i4)    <-- 0 means this vertex does not connect
        ##    x(f8)   y(f8)   1(i4)    <-- 1 means this vertex connects to the previous vertex
        ##    ...
        ##    0(i4)
        ##
        ## All values are big endian--pack using struct.pack('>d') or struct.pack('>i')
        
        #prof = debug.Profiler('PlotCurveItem.generatePath', disabled=True)
        
        n = x.shape[0]
        # create empty array, pad with extra space on either end
        arr = np.empty(n+2, dtype=[('x', '>f8'), ('y', '>f8'), ('c', '>i4')])
        #prof.mark('create empty')
        # write first two integers
        arr.data[12:20] = struct.pack('>ii', n, 0)
        # Fill array with vertex values
        arr[1:-1]['x'] = x
        arr[1:-1]['y'] = y
        arr[1:-1]['c'] = 1
        #prof.mark('fill array')
        # write last 0
        lastInd = 20*(n+1) 
        arr.data[lastInd:lastInd+4] = struct.pack('>i', 0)
        
        # create datastream object and stream into path
        buf = QtCore.QByteArray(arr.data[12:lastInd+4])  # I think one unnecessary copy happens here
        #prof.mark('create buffer')
        ds = QtCore.QDataStream(buf)
        #prof.mark('create dataStream')
        ds >> path
        #prof.mark('load path')
        #prof.finish()
        return path
        
    def boundingRect(self):
        (x, y) = self.getData()
        if x is None or y is None or len(x) == 0 or len(y) == 0:
            return QtCore.QRectF()
            
            
        if self.shadow is not None:
            lineWidth = (max(self.pen.width(), self.shadow.width()) + 1)
        else:
            lineWidth = (self.pen.width()+1)
            
        
        pixels = self.pixelVectors()
        if pixels is not None:
            xmin = x.min() - pixels[0].x() * lineWidth
            xmax = x.max() + pixels[0].x() * lineWidth
            ymin = y.min() - abs(pixels[1].y()) * lineWidth
            ymax = y.max() + abs(pixels[1].y()) * lineWidth
            return QtCore.QRectF(xmin, ymin, xmax-xmin, ymax-ymin)
        return QtCore.QRectF(0,0,0,0)
        
        
    def paint(self, p, opt, widget):
        #prof = debug.Profiler('PlotCurveItem.paint '+str(id(self)), disabled=True)
        if self.xData is None:
            return
        #if self.opts['spectrumMode']:
            #if self.specPath is None:
                
                #self.specPath = self.generatePath(*self.getData())
            #path = self.specPath
        #else:
        if self.path is None:
            self.path = self.generatePath(*self.getData())
        path = self.path
        #prof.mark('generate path')
            
        
        #sp = QtGui.QPen(self.shadow) if self.shadow is not None else None
        
        ## Copy pens and apply alpha adjustment
        cp = QtGui.QPen(self.pen) #self.pen is a color
        cp.setWidthF(1.2)
        c = cp.color()
        c.setAlphaF(0.7)
        cp.setColor(c)
        #for pen in (sp, cp):
        #    if pen is None:
        #        continue
        #    c = pen.color()
        #    c.setAlpha(c.alpha() * self.opts['alphaHint'])
        #    pen.setColor(c)
            #pen.setCosmetic(True)
            
        #if self.shadow is not None:
        #    p.setPen(sp)
        #    p.drawPath(path)
            
        if self.highlighted:
            c = cp.color()
            c.setAlphaF(1.)
            cp.setColor(c)
            cp.setWidthF(3.)
            #pen = QtGui.QPen(c.darker())
            #pen.setWidthF(cp.widthF()+.01)
            #p.setPen(pen)
        #else:
        p.setPen(cp)
        p.drawPath(path)
        #prof.mark('drawPath')
        
        #prof.finish()
        #p.setPen(QtGui.QPen(QtGui.QColor(255,0,0)))
        #p.drawRect(self.boundingRect())
        
        
    def free(self):
        self.xData = None  ## raw values
        self.yData = None
        self.xDisp = None  ## display values (after log / fft)
        self.yDisp = None
        self.path = None
        #del self.xData, self.yData, self.xDisp, self.yDisp, self.path
        
    def mousePressEvent(self, ev):
        #GraphicsObject.mousePressEvent(self, ev)
        if not self.clickable:
            ev.ignore()
        if ev.button() != QtCore.Qt.LeftButton:
            ev.ignore()
        self.mousePressPos = ev.pos()
        self.mouseMoved = False
        
    def mouseMoveEvent(self, ev):
        #GraphicsObject.mouseMoveEvent(self, ev)
        self.mouseMoved = True
        #print "move"
        
    def mouseReleaseEvent(self, ev):
        #GraphicsObject.mouseReleaseEvent(self, ev)
        if not self.mouseMoved:
            #self.setHighlighted(True) #does not work well
            #self.update()
            self.sigClicked.emit(self)
    
#    def hoverEnterEvent(self, ev):
#        self.setHighlighted(True)
#        self.update()
#        
#    def hoverLeaveEvent(self, ev):
#        self.setHighlighted(False)
#        self.update()        
       
class CurvePoint(QtGui.QGraphicsObject):
    """A GraphicsItem that sets its location to a point on a PlotCurveItem.
    The position along the curve is a property, and thus can be easily animated."""
    
    def __init__(self, curve, index=0, pos=None):
        """Position can be set either as an index referring to the sample number or
        the position 0.0 - 1.0"""
        
        QtGui.QGraphicsObject.__init__(self)
        #QObjectWorkaround.__init__(self)
        self.curve = weakref.ref(curve)
        self.setParentItem(curve)
        self.setProperty('position', 0.0)
        self.setProperty('index', 0)
        
        if hasattr(self, 'ItemHasNoContents'):
            self.setFlags(self.flags() | self.ItemHasNoContents)
        
        if pos is not None:
            self.setPos(pos)
        else:
            self.setIndex(index)
            
    def setPos(self, pos):
        self.setProperty('position', pos)
        
    def setIndex(self, index):
        self.setProperty('index', index)
        
    def event(self, ev):
        if not isinstance(ev, QtCore.QDynamicPropertyChangeEvent) or self.curve() is None:
            return False
            
        if ev.propertyName() == 'index':
            index = self.property('index').toInt()[0]
        elif ev.propertyName() == 'position':
            index = None
        else:
            return False
            
        (x, y) = self.curve().getData()
        if index is None:
            #print self.property('position').toDouble()[0], self.property('position').typeName()
            index = (len(x)-1) * clip(self.property('position').toDouble()[0], 0.0, 1.0)
            
        if index != int(index):  ## interpolate floating-point values
            i1 = int(index)
            i2 = clip(i1+1, 0, len(x)-1)
            s2 = index-i1
            s1 = 1.0-s2
            newPos = (x[i1]*s1+x[i2]*s2, y[i1]*s1+y[i2]*s2)
        else:
            index = int(index)
            i1 = clip(index-1, 0, len(x)-1)
            i2 = clip(index+1, 0, len(x)-1)
            newPos = (x[index], y[index])
            
        p1 = self.parentItem().mapToScene(QtCore.QPointF(x[i1], y[i1]))
        p2 = self.parentItem().mapToScene(QtCore.QPointF(x[i2], y[i2]))
        ang = np.arctan2(p2.y()-p1.y(), p2.x()-p1.x()) ## returns radians
        self.resetTransform()
        self.rotate(180+ ang * 180 / np.pi) ## takes degrees
        QtGui.QGraphicsItem.setPos(self, *newPos)
        return True
        
    def boundingRect(self):
        return QtCore.QRectF()
        
    def paint(self, *args):
        pass
    
    def makeAnimation(self, prop='position', start=0.0, end=1.0, duration=10000, loop=1):
        anim = QtCore.QPropertyAnimation(self, prop)
        anim.setDuration(duration)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setLoopCount(loop)
        return anim
        
        

class ArrowItem(QtGui.QGraphicsPolygonItem):
    def __init__(self, **opts):
        QtGui.QGraphicsPolygonItem.__init__(self)
        defOpts = {
            'style': 'tri',
            'pxMode': True,
            'size': 20,
            'angle': -150,
            'pos': (0,0),
            'width': 8,
            'tipAngle': 25,
            'baseAngle': 90,
            'pen': (200,200,200),
            'brush': (50,50,200),
        }
        defOpts.update(opts)
        
        self.setStyle(**defOpts)
        
        self.setPen(mkPen(defOpts['pen']))
        self.setBrush(mkBrush(defOpts['brush']))
        
        self.rotate(self.opts['angle'])
        self.moveBy(*self.opts['pos'])
    
    def setStyle(self, **opts):
        self.opts = opts
        
        if opts['style'] == 'tri':
            points = [
                QtCore.QPointF(0,0),
                QtCore.QPointF(opts['size'],-opts['width']/2.),
                QtCore.QPointF(opts['size'],opts['width']/2.),
            ]
            poly = QtGui.QPolygonF(points)
            
        else:
            raise Exception("Unrecognized arrow style '%s'" % opts['style'])
        
        self.setPolygon(poly)
        
        if opts['pxMode']:
            self.setFlags(self.flags() | self.ItemIgnoresTransformations)
        else:
            self.setFlags(self.flags() & ~self.ItemIgnoresTransformations)
        
    def paint(self, p, *args):
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        QtGui.QGraphicsPolygonItem.paint(self, p, *args)
        

class CurveArrow(CurvePoint):
    """Provides an arrow that points to any specific sample on a PlotCurveItem.
    Provides properties that can be animated."""
    
    def __init__(self, curve, index=0, pos=None, **opts):
        CurvePoint.__init__(self, curve, index=index, pos=pos)
        if opts.get('pxMode', True):
            opts['pxMode'] = False
            self.setFlags(self.flags() | self.ItemIgnoresTransformations)
        opts['angle'] = 0
        self.arrow = ArrowItem(**opts)
        self.arrow.setParentItem(self)
        
    def setStyle(self, **opts):
        return self.arrow.setStyle(**opts)
        
        

class ScatterPlotItem(GraphicsObject):
    
    #sigPointClicked = QtCore.Signal(object, object)
    sigClicked = QtCore.Signal(object, object)  ## self, points
    
    def __init__(self, spots=None, x=None, y=None, pxMode=True, pen='default', brush='default', size=5, identical=True, data=None):
        """
        Arguments:
            spots: list of dicts. Each dict specifies parameters for a single spot.
            x,y: array of x,y values. Alternatively, specify spots['pos'] = (x,y)
            pxMode: If True, spots are always the same size regardless of scaling
            identical: If True, all spots are forced to look identical. 
                       This can result in performance enhancement."""
        GraphicsObject.__init__(self)
        self.spots = []
        self.range = [[0,0], [0,0]]
        self.identical = identical
        self._spotPixmap = None
        
        if brush == 'default':
            self.brush = QtGui.QBrush(QtGui.QColor(100, 100, 150))
        else:
            self.brush = mkBrush(brush)
        
        if pen == 'default':
            self.pen = QtGui.QPen(QtGui.QColor(200, 200, 200))
        else:
            self.pen = mkPen(pen)
        
        self.size = size
        
        self.pxMode = pxMode
        if spots is not None or x is not None:
            self.setPoints(spots, x, y, data)
        
        self.highlighted = False
            
        #self.optimize = optimize
        #if optimize:
            #self.spotImage = QtGui.QImage(size, size, QtGui.QImage.Format_ARGB32_Premultiplied)
            #self.spotImage.fill(0)
            #p = QtGui.QPainter(self.spotImage)
            #p.setRenderHint(p.Antialiasing)
            #p.setBrush(brush)
            #p.setPen(pen)
            #p.drawEllipse(0, 0, size, size)
            #p.end()
            #self.optimizePixmap = QtGui.QPixmap(self.spotImage)
            #self.optimizeFragments = []
            #self.setFlags(self.flags() | self.ItemIgnoresTransformations)
            
    def setPxMode(self, mode):
        self.pxMode = mode
            
    def clear(self):
        for i in self.spots:
            i.setParentItem(None)
            s = i.scene()
            if s is not None:
                s.removeItem(i)
        self.spots = []
        

    def getRange(self, ax, percent):
        return self.range[ax]
        
    def setPoints(self, spots=None, x=None, y=None, data=None):
        self.clear()
        self.range = [[0,0],[0,0]]
        self.addPoints(spots, x, y, data)

    def addPoints(self, spots=None, x=None, y=None, data=None):
        xmn = ymn = xmx = ymx = None
        if spots is not None:
            n = len(spots)
        else:
            n = len(x)
        
        for i in xrange(n):
            if spots is not None:
                s = spots[i]
                pos = Point(s['pos'])
            else:
                s = {}
                pos = Point(x[i], y[i])
            if data is not None:
                s['data'] = data[i]
                
            size = s.get('size', self.size)
            if self.pxMode:
                psize = 0
            else:
                psize = size
            if xmn is None:
                xmn = pos[0]-psize
                xmx = pos[0]+psize
                ymn = pos[1]-psize
                ymx = pos[1]+psize
            else:
                xmn = min(xmn, pos[0]-psize)
                xmx = max(xmx, pos[0]+psize)
                ymn = min(ymn, pos[1]-psize)
                ymx = max(ymx, pos[1]+psize)
            #print pos, xmn, xmx, ymn, ymx
            brush = s.get('brush', self.brush)
            pen = s.get('pen', self.pen)
            pen.setCosmetic(True)
            data2 = s.get('data', None)
            item = self.mkSpot(pos, size, self.pxMode, brush, pen, data2, index=len(self.spots))
            self.spots.append(item)
            #if self.optimize:
                #item.hide()
                #frag = QtGui.QPainter.PixmapFragment.create(pos, QtCore.QRectF(0, 0, size, size))
                #self.optimizeFragments.append(frag)
        self.range = [[xmn, xmx], [ymn, ymx]]
                
    #def paint(self, p, *args):
        #if not self.optimize:
            #return
        ##p.setClipRegion(self.boundingRect())
        #p.drawPixmapFragments(self.optimizeFragments, self.optimizePixmap)

    def paint(self, *args):
        pass

    def spotPixmap(self):
        if not self.identical:
            return None
        if self._spotPixmap is None:
            self._spotPixmap = PixmapSpotItem.makeSpotImage(self.size, self.pen, self.brush)
        return self._spotPixmap

    def mkSpot(self, pos, size, pxMode, brush, pen, data, index=None):
        if pxMode:
            img = self.spotPixmap()
            item = PixmapSpotItem(size, brush, pen, data, image=img, index=index)
        else:
            item = SpotItem(size, pxMode, brush, pen, data, index=index)
        item.setParentItem(self)
        item.setPos(pos)
        #item.sigClicked.connect(self.pointClicked)
        return item
        
    def boundingRect(self):
        ((xmn, xmx), (ymn, ymx)) = self.range
        if xmn is None or xmx is None or ymn is None or ymx is None:
            return QtCore.QRectF()
        return QtCore.QRectF(xmn, ymn, xmx-xmn, ymx-ymn)
        return QtCore.QRectF(xmn-1, ymn-1, xmx-xmn+2, ymx-ymn+2)
        
    #def pointClicked(self, point):
        #self.sigPointClicked.emit(self, point)

    def points(self):
        return self.spots[:]

    def pointsAt(self, pos):
        """
        TODO:improve selection using binary search
        """
        x = pos.x()
        y = pos.y()
        pw = self.pixelWidth()
        ph = self.pixelHeight()
        pts = []
        for s in self.spots:
            sp = s.pos()
            ss = s.size
            sx = sp.x()
            sy = sp.y()
            s2x = s2y = ss * 0.5
            if self.pxMode:
                s2x *= pw
                s2y *= ph
            if x > sx-s2x and x < sx+s2x and y > sy-s2y and y < sy+s2y:
                pts.append(s)
                #print "HIT:", x, y, sx, sy, s2x, s2y
            #else:
                #print "No hit:", (x, y), (sx, sy)
                #print "       ", (sx-s2x, sy-s2y), (sx+s2x, sy+s2y)
        pts.sort(lambda a,b: cmp(b.zValue(), a.zValue()))
        return pts
            

    def mousePressEvent(self, ev):
        QtGui.QGraphicsItem.mousePressEvent(self, ev)
        if ev.button() == QtCore.Qt.LeftButton:
            pts = self.pointsAt(ev.pos())
            if len(pts) > 0:
                self.mouseMoved = False
                self.ptsClicked = pts
                ev.accept()
            else:
                #print "no spots"
                ev.ignore()
        else:
            ev.ignore()
        
    def mouseMoveEvent(self, ev):
        QtGui.QGraphicsItem.mouseMoveEvent(self, ev)
        self.mouseMoved = True
        pass
    
    def mouseReleaseEvent(self, ev):
        QtGui.QGraphicsItem.mouseReleaseEvent(self, ev)
        if not self.mouseMoved:
            #print self.ptsClicked
            self.sigClicked.emit(self, self.ptsClicked)


class SpotItem(QtGui.QGraphicsWidget):
    #sigClicked = QtCore.Signal(object)
    
    def __init__(self, size, pxMode, brush, pen, data, index=None):
        QtGui.QGraphicsWidget.__init__(self)
        self.pxMode = pxMode
            
        self.pen = pen
        self.brush = brush
        self.size = size
        self.index = index
        #s2 = size/2.
        self.path = QtGui.QPainterPath()
        self.path.addEllipse(QtCore.QRectF(-0.5, -0.5, 1, 1))
        if pxMode:
            #self.setCacheMode(self.DeviceCoordinateCache)   ## broken.
            self.setFlags(self.flags() | self.ItemIgnoresTransformations)
            self.spotImage = QtGui.QImage(size, size, QtGui.QImage.Format_ARGB32_Premultiplied)
            self.spotImage.fill(0)
            p = QtGui.QPainter(self.spotImage)
            p.setRenderHint(p.Antialiasing)
            p.setBrush(brush)
            p.setPen(pen)
            p.drawEllipse(0, 0, size, size)
            p.end()
            self.pixmap = QtGui.QPixmap(self.spotImage)
        else:
            self.scale(size, size)
        self.data = data
        
    def setBrush(self, brush):
        self.brush = mkBrush(brush)
        self.update()
        
    def setPen(self, pen):
        self.pen = mkPen(pen)
        self.update()
        
    def boundingRect(self):
        return self.path.boundingRect()
        
    def shape(self):
        return self.path
        
    def paint(self, p, *opts):
        if self.pxMode:
            p.drawPixmap(QtCore.QPoint(int(-0.5*self.size), int(-0.5*self.size)), self.pixmap)
        else:
            p.setPen(self.pen)
            p.setBrush(self.brush)
            p.drawPath(self.path)
        
    #def mousePressEvent(self, ev):
        #QtGui.QGraphicsItem.mousePressEvent(self, ev)
        #if ev.button() == QtCore.Qt.LeftButton:
            #self.mouseMoved = False
            #ev.accept()
        #else:
            #ev.ignore()

        
        
    #def mouseMoveEvent(self, ev):
        #QtGui.QGraphicsItem.mouseMoveEvent(self, ev)
        #self.mouseMoved = True
        #pass
    
    #def mouseReleaseEvent(self, ev):
        #QtGui.QGraphicsItem.mouseReleaseEvent(self, ev)
        #if not self.mouseMoved:
            #self.sigClicked.emit(self)
        
class PixmapSpotItem(QtGui.QGraphicsItem):
    #sigClicked = QtCore.Signal(object)
    
    def __init__(self, size, brush, pen, data, image=None, index=None):
        """This class draws a scale-invariant image centered at 0,0.
        If no image is specified, then an antialiased circle is constructed instead.
        It should be quite fast, but large spots will use a lot of memory."""
        
        QtGui.QGraphicsItem.__init__(self)
        self.pen = pen
        self.brush = brush
        self.size = size
        self.index = index
        self.setFlags(self.flags() | self.ItemIgnoresTransformations | self.ItemHasNoContents)
        if image is None:
            self.image = self.makeSpotImage(self.size, self.pen, self.brush)
        else:
            self.image = image
        self.pixmap = QtGui.QPixmap(self.image)
        #self.setPixmap(self.pixmap)
        self.data = data
        self.pi = QtGui.QGraphicsPixmapItem(self.pixmap, self)
        self.pi.setPos(-0.5*size, -0.5*size)
        
        #self.translate(-0.5, -0.5)
    def boundingRect(self):
        return self.pi.boundingRect()
        
    @staticmethod
    def makeSpotImage(size, pen, brush):
        img = QtGui.QImage(size+2, size+2, QtGui.QImage.Format_ARGB32_Premultiplied)
        img.fill(0)
        p = QtGui.QPainter(img)
        try:
            #p.setRenderHint(p.Antialiasing)
            p.setBrush(brush)
            p.setPen(pen)
            p.drawEllipse(1, 1, size, size)
        finally:
            p.end()  ## failure to end a painter properly causes crash.
        return img
        
        
        
    #def paint(self, p, *args):
        #p.setCompositionMode(p.CompositionMode_Plus)
        #QtGui.QGraphicsPixmapItem.paint(self, p, *args)
        
    #def setBrush(self, brush):
        #self.brush = mkBrush(brush)
        #self.update()
        
    #def setPen(self, pen):
        #self.pen = mkPen(pen)
        #self.update()
        
    #def boundingRect(self):
        #return self.path.boundingRect()
        
    #def shape(self):
        #return self.path
        
    #def paint(self, p, *opts):
        #if self.pxMode:
            #p.drawPixmap(QtCore.QPoint(int(-0.5*self.size), int(-0.5*self.size)), self.pixmap)
        #else:
            #p.setPen(self.pen)
            #p.setBrush(self.brush)
            #p.drawPath(self.path)
        
        

class ROIPlotItem(PlotCurveItem):
    """Plot curve that monitors an ROI and image for changes to automatically replot."""
    def __init__(self, roi, data, img, axes=(0,1), xVals=None, color=None):
        self.roi = roi
        self.roiData = data
        self.roiImg = img
        self.axes = axes
        self.xVals = xVals
        PlotCurveItem.__init__(self, self.getRoiData(), x=self.xVals, color=color)
        #roi.connect(roi, QtCore.SIGNAL('regionChanged'), self.roiChangedEvent)
        roi.sigRegionChanged.connect(self.roiChangedEvent)
        #self.roiChangedEvent()
        
    def getRoiData(self):
        d = self.roi.getArrayRegion(self.roiData, self.roiImg, axes=self.axes)
        if d is None:
            return
        while d.ndim > 1:
            d = d.mean(axis=1)
        return d
        
    def roiChangedEvent(self):
        d = self.getRoiData()
        self.updateData(d, self.xVals)




class UIGraphicsItem(GraphicsObject):
    """Base class for graphics items with boundaries relative to a GraphicsView widget"""
    def __init__(self, view, bounds=None):
        GraphicsObject.__init__(self)
        self._view = weakref.ref(view)
        if bounds is None:
            self._bounds = QtCore.QRectF(0, 0, 1, 1)
        else:
            self._bounds = bounds
        self._viewRect = self._view().rect()
        self._viewTransform = self.viewTransform()
        self.setNewBounds()
        #QtCore.QObject.connect(view, QtCore.SIGNAL('viewChanged'), self.viewChangedEvent)
        view.sigRangeChanged.connect(self.viewRangeChanged)
        
    def viewRect(self):
        """Return the viewport widget rect"""
        return self._view().rect()
    
    def viewTransform(self):
        """Returns a matrix that maps viewport coordinates onto scene coordinates"""
        if self._view() is None:
            return QtGui.QTransform()
        else:
            return self._view().viewportTransform()
        
    def boundingRect(self):
        if self._view() is None:
            self.bounds = self._bounds
        else:
            vr = self._view().rect()
            tr = self.viewTransform()
            if vr != self._viewRect or tr != self._viewTransform:
                #self.viewChangedEvent(vr, self._viewRect)
                self._viewRect = vr
                self._viewTransform = tr
                self.setNewBounds()
        #print "viewRect", self._viewRect.x(), self._viewRect.y(), self._viewRect.width(), self._viewRect.height()
        #print "bounds", self.bounds.x(), self.bounds.y(), self.bounds.width(), self.bounds.height()
        return self.bounds

    def setNewBounds(self):
        bounds = QtCore.QRectF(
            QtCore.QPointF(self._bounds.left()*self._viewRect.width(), self._bounds.top()*self._viewRect.height()),
            QtCore.QPointF(self._bounds.right()*self._viewRect.width(), self._bounds.bottom()*self._viewRect.height())
        )
        bounds.adjust(0.5, 0.5, 0.5, 0.5)
        self.bounds = self.viewTransform().inverted()[0].mapRect(bounds)
        self.prepareGeometryChange()

    def viewRangeChanged(self):
        """Called when the view widget is resized"""
        self.boundingRect()
        self.update()
        
    def unitRect(self):
        return self.viewTransform().inverted()[0].mapRect(QtCore.QRectF(0, 0, 1, 1))

    def paint(self, *args):
        pass




class LabelItem(QtGui.QGraphicsWidget):
    def __init__(self, text, parent=None, **args):
        QtGui.QGraphicsWidget.__init__(self, parent)
        self.item = QtGui.QGraphicsTextItem(self)
        self.opts = args
        if 'color' not in args:
            self.opts['color'] = 'CCC'
        else:
            if isinstance(args['color'], QtGui.QColor):
                self.opts['color'] = colorStr(args['color'])[:6]
        self.sizeHint = {}
        self.setText(text)
        
            
    def setAttr(self, attr, value):
        """Set default text properties. See setText() for accepted parameters."""
        self.opts[attr] = value
        
    def setText(self, text, **args):
        """Set the text and text properties in the label. Accepts optional arguments for auto-generating
        a CSS style string:
           color:   string (example: 'CCFF00')
           size:    string (example: '8pt')
           bold:    boolean
           italic:  boolean
           """
        self.text = text
        opts = self.opts.copy()
        for k in args:
            opts[k] = args[k]
        
        optlist = []
        if 'color' in opts:
            optlist.append('color: #' + opts['color'])
        if 'size' in opts:
            optlist.append('font-size: ' + opts['size'])
        if 'bold' in opts and opts['bold'] in [True, False]:
            optlist.append('font-weight: ' + {True:'bold', False:'normal'}[opts['bold']])
        if 'italic' in opts and opts['italic'] in [True, False]:
            optlist.append('font-style: ' + {True:'italic', False:'normal'}[opts['italic']])
        full = "<span style='%s'>%s</span>" % ('; '.join(optlist), text)
        #print full
        self.item.setHtml(full)
        self.updateMin()
        
    def resizeEvent(self, ev):
        c1 = self.boundingRect().center()
        c2 = self.item.mapToParent(self.item.boundingRect().center()) # + self.item.pos()
        dif = c1 - c2
        self.item.moveBy(dif.x(), dif.y())
        #print c1, c2, dif, self.item.pos()
        
    def setAngle(self, angle):
        self.angle = angle
        self.item.resetTransform()
        self.item.rotate(angle)
        self.updateMin()
        
    def updateMin(self):
        bounds = self.item.mapRectToParent(self.item.boundingRect())
        self.setMinimumWidth(bounds.width())
        self.setMinimumHeight(bounds.height())
        #print self.text, bounds.width(), bounds.height()
        
        #self.sizeHint = {
            #QtCore.Qt.MinimumSize: (bounds.width(), bounds.height()),
            #QtCore.Qt.PreferredSize: (bounds.width(), bounds.height()),
            #QtCore.Qt.MaximumSize: (bounds.width()*2, bounds.height()*2),
            #QtCore.Qt.MinimumDescent: (0, 0)  ##?? what is this?
        #}
            
        
    #def sizeHint(self, hint, constraint):
        #return self.sizeHint[hint]
        




class ScaleItem(QtGui.QGraphicsWidget):
    def __init__(self, orientation, pen=None, linkView=None, parent=None):
        """GraphicsItem showing a single plot axis with ticks, values, and label.
        Can be configured to fit on any side of a plot, and can automatically synchronize its displayed scale with ViewBox items.
        Ticks can be extended to make a grid."""
        QtGui.QGraphicsWidget.__init__(self, parent)
        self.label = QtGui.QGraphicsTextItem(self)
        self.orientation = orientation
        if orientation not in ['left', 'right', 'top', 'bottom']:
            raise Exception("Orientation argument must be one of 'left', 'right', 'top', or 'bottom'.")
        if orientation in ['left', 'right']:
            #self.setMinimumWidth(25)
            #self.setSizePolicy(QtGui.QSizePolicy(
                #QtGui.QSizePolicy.Minimum,
                #QtGui.QSizePolicy.Expanding
            #))
            self.label.rotate(-90)
        #else:
            #self.setMinimumHeight(50)
            #self.setSizePolicy(QtGui.QSizePolicy(
                #QtGui.QSizePolicy.Expanding,
                #QtGui.QSizePolicy.Minimum
            #))
        #self.drawLabel = False
        
        self.labelText = ''
        self.labelUnits = ''
        self.labelUnitPrefix=''
        self.labelStyle = {'color': '#000'}
        
        self.textHeight = 18
        self.tickLength = 10
        self.scale = 1.0
        self.autoScale = True
            
        self.setRange(0, 1)
        
        if pen is None:
            pen = QtGui.QPen(QtGui.QColor(100, 100, 100))
        self.setPen(pen)
        
        self.linkedView = None
        if linkView is not None:
            self.linkToView(linkView)
            
        self.showLabel(False)
        
        self.grid = False
        self.setCacheMode(self.DeviceCoordinateCache)
            
    def close(self):
        self.scene().removeItem(self.label)
        self.label = None
        self.scene().removeItem(self)
        
    def setGrid(self, grid):
        """Set the alpha value for the grid, or False to disable."""
        self.grid = grid
        self.update()
        
        
    def resizeEvent(self, ev=None):
        #s = self.size()
        
        ## Set the position of the label
        nudge = 5
        br = self.label.boundingRect()
        p = QtCore.QPointF(0, 0)
        if self.orientation == 'left':
            p.setY(int(self.size().height()/2 + br.width()/2))
            p.setX(-nudge)
            #s.setWidth(10)
        elif self.orientation == 'right':
            #s.setWidth(10)
            p.setY(int(self.size().height()/2 + br.width()/2))
            p.setX(int(self.size().width()-br.height()+nudge))
        elif self.orientation == 'top':
            #s.setHeight(10)
            p.setY(-nudge)
            p.setX(int(self.size().width()/2. - br.width()/2.))
        elif self.orientation == 'bottom':
            p.setX(int(self.size().width()/2. - br.width()/2.))
            #s.setHeight(10)
            p.setY(int(self.size().height()-br.height()+nudge))
        #self.label.resize(s)
        self.label.setPos(p)
        
    def showLabel(self, show=True):
        #self.drawLabel = show
        self.label.setVisible(show)
        if self.orientation in ['left', 'right']:
            self.setWidth()
        else:
            self.setHeight()
        if self.autoScale:
            self.setScale()
        
    def setLabel(self, text=None, units=None, unitPrefix=None, **args):
        if text is not None:
            self.labelText = text
            self.showLabel()
        if units is not None:
            self.labelUnits = units
            self.showLabel()
        if unitPrefix is not None:
            self.labelUnitPrefix = unitPrefix
        if len(args) > 0:
            self.labelStyle = args
        self.label.setHtml(self.labelString())
        self.resizeEvent()
        self.update()
            
    def labelString(self):
        if self.labelUnits == '':
            if self.scale == 1.0:
                units = ''
            else:
                units = u'(x%g)' % (1.0/self.scale)
        else:
            #print repr(self.labelUnitPrefix), repr(self.labelUnits)
            units = u'(%s%s)' % (self.labelUnitPrefix, self.labelUnits)
            
        s = u'%s %s' % (self.labelText, units)
        
        style = ';'.join(['%s: "%s"' % (k, self.labelStyle[k]) for k in self.labelStyle])
        
        return u"<span style='%s'>%s</span>" % (style, s)
        
    def setHeight(self, h=None):
        if h is None:
            h = self.textHeight + self.tickLength
            if self.label.isVisible():
                h += self.textHeight
        self.setMaximumHeight(h)
        self.setMinimumHeight(h)
        
        
    def setWidth(self, w=None):
        if w is None:
            w = self.tickLength + 40
            if self.label.isVisible():
                w += self.textHeight
        self.setMaximumWidth(w)
        self.setMinimumWidth(w)
        
    def setPen(self, pen):
        self.pen = pen
        self.update()
        
    def setScale(self, scale=None):
        if scale is None:
            #if self.drawLabel:  ## If there is a label, then we are free to rescale the values 
            if self.label.isVisible():
                d = self.range[1] - self.range[0]
                #pl = 1-int(log10(d))
                #scale = 10 ** pl
                (scale, prefix) = siScale(d / 2.)
                if self.labelUnits == '' and prefix in ['k', 'm']:  ## If we are not showing units, wait until 1e6 before scaling.
                    scale = 1.0
                    prefix = ''
                self.setLabel(unitPrefix=prefix)
            else:
                scale = 1.0
        
        
        if scale != self.scale:
            self.scale = scale
            self.setLabel()
            self.update()
        
    def setRange(self, mn, mx):
        if mn in [np.nan, np.inf, -np.inf] or mx in [np.nan, np.inf, -np.inf]:
            raise Exception("Not setting range to [%s, %s]" % (str(mn), str(mx)))
        self.range = [mn, mx]
        if self.autoScale:
            self.setScale()
        self.update()
        
    def linkToView(self, view):
        if self.orientation in ['right', 'left']:
            if self.linkedView is not None and self.linkedView() is not None:
                #view.sigYRangeChanged.disconnect(self.linkedViewChanged)
                ## should be this instead?
                self.linkedView().sigYRangeChanged.disconnect(self.linkedViewChanged)
            self.linkedView = weakref.ref(view)
            view.sigYRangeChanged.connect(self.linkedViewChanged)
            #signal = QtCore.SIGNAL('yRangeChanged')
        else:
            if self.linkedView is not None and self.linkedView() is not None:
                #view.sigYRangeChanged.disconnect(self.linkedViewChanged)
                ## should be this instead?
                self.linkedView().sigXRangeChanged.disconnect(self.linkedViewChanged)
            self.linkedView = weakref.ref(view)
            view.sigXRangeChanged.connect(self.linkedViewChanged)
            #signal = QtCore.SIGNAL('xRangeChanged')
            
        
    def linkedViewChanged(self, view, newRange):
        self.setRange(*newRange)
        
    def boundingRect(self):
        if self.linkedView is None or self.linkedView() is None or self.grid is False:
            return self.mapRectFromParent(self.geometry())
        else:
            return self.mapRectFromParent(self.geometry()) | self.mapRectFromScene(self.linkedView().mapRectToScene(self.linkedView().boundingRect()))
        
    def paint(self, p, opt, widget):
        p.setPen(self.pen)
        
        #bounds = self.boundingRect()
        bounds = self.mapRectFromParent(self.geometry())
        
        if self.linkedView is None or self.linkedView() is None or self.grid is False:
            tbounds = bounds
        else:
            tbounds = self.mapRectFromScene(self.linkedView().mapRectToScene(self.linkedView().boundingRect()))
        
        if self.orientation == 'left':
            p.drawLine(bounds.topRight(), bounds.bottomRight())
            tickStart = tbounds.right()
            tickStop = bounds.right()
            tickDir = -1
            axis = 0
        elif self.orientation == 'right':
            p.drawLine(bounds.topLeft(), bounds.bottomLeft())
            tickStart = tbounds.left()
            tickStop = bounds.left()
            tickDir = 1
            axis = 0
        elif self.orientation == 'top':
            p.drawLine(bounds.bottomLeft(), bounds.bottomRight())
            tickStart = tbounds.bottom()
            tickStop = bounds.bottom()
            tickDir = -1
            axis = 1
        elif self.orientation == 'bottom':
            p.drawLine(bounds.topLeft(), bounds.topRight())
            tickStart = tbounds.top()
            tickStop = bounds.top()
            tickDir = 1
            axis = 1
        
        ## Determine optimal tick spacing
        #intervals = [1., 2., 5., 10., 20., 50.]
        #intervals = [1., 2.5, 5., 10., 25., 50.]
        intervals = [1., 2., 10., 20., 100.]
        dif = abs(self.range[1] - self.range[0])
        if dif == 0.0:
            return
        #print "dif:", dif
        pw = 10 ** (np.floor(np.log10(dif))-1)
        for i in range(len(intervals)):
            i1 = i
            if dif / (pw*intervals[i]) < 10:
                break
        
        textLevel = i1  ## draw text at this scale level
        
        #print "range: %s   dif: %f   power: %f  interval: %f   spacing: %f" % (str(self.range), dif, pw, intervals[i1], sp)
        
        #print "  start at %f,  %d ticks" % (start, num)
        
        
        if axis == 0:
            xs = -bounds.height() / dif
        else:
            xs = bounds.width() / dif
            
        tickPositions = set() # remembers positions of previously drawn ticks
        ## draw ticks and text
        ## draw three different intervals, long ticks first
        for i in reversed([i1, i1+1, i1+2]):
            if i > len(intervals):
                continue
            ## spacing for this interval
            sp = pw*intervals[i]
            
            ## determine starting tick
            start = np.ceil(self.range[0] / sp) * sp
            
            ## determine number of ticks
            num = int(dif / sp) + 1
            
            ## last tick value
            last = start + sp * num
            
            ## Number of decimal places to print
            maxVal = max(abs(start), abs(last))
            places = max(0, 1-int(np.log10(sp*self.scale)))
        
            ## length of tick
            h = min(self.tickLength, (self.tickLength*3 / num) - 1.)
            
            ## alpha
            a = min(255, (765. / num) - 1.)
            
            if axis == 0:
                offset = self.range[0] * xs - bounds.height()
            else:
                offset = self.range[0] * xs
            
            for j in range(num):
                v = start + sp * j
                x = (v * xs) - offset
                p1 = [0, 0]
                p2 = [0, 0]
                p1[axis] = tickStart
                p2[axis] = tickStop + h*tickDir
                p1[1-axis] = p2[1-axis] = x
                
                if p1[1-axis] > [bounds.width(), bounds.height()][1-axis]:
                    continue
                if p1[1-axis] < 0:
                    continue
                p.setPen(QtGui.QPen(QtGui.QColor(100, 100, 100, a)))
                # draw tick only if there is none
                tickPos = p1[1-axis]
                if tickPos not in tickPositions:
                    p.drawLine(Point(p1), Point(p2))
                    tickPositions.add(tickPos)
                if i == textLevel:
                    if abs(v) < .001 or abs(v) >= 10000:
                        vstr = "%g" % (v * self.scale)
                    else:
                        vstr = ("%%0.%df" % places) % (v * self.scale)
                        
                    textRect = p.boundingRect(QtCore.QRectF(0, 0, 100, 100), QtCore.Qt.AlignCenter, vstr)
                    height = textRect.height()
                    self.textHeight = height
                    if self.orientation == 'left':
                        textFlags = QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter
                        rect = QtCore.QRectF(tickStop-100, x-(height/2), 100-self.tickLength, height)
                    elif self.orientation == 'right':
                        textFlags = QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter
                        rect = QtCore.QRectF(tickStop+self.tickLength, x-(height/2), 100-self.tickLength, height)
                    elif self.orientation == 'top':
                        textFlags = QtCore.Qt.AlignCenter|QtCore.Qt.AlignBottom
                        rect = QtCore.QRectF(x-100, tickStop-self.tickLength-height, 200, height)
                    elif self.orientation == 'bottom':
                        textFlags = QtCore.Qt.AlignCenter|QtCore.Qt.AlignTop
                        rect = QtCore.QRectF(x-100, tickStop+self.tickLength, 200, height)
                    
                    p.setPen(QtGui.QPen(QtGui.QColor(100, 100, 100)))
                    p.drawText(rect, textFlags, vstr)
                    #p.drawRect(rect)
        
        ## Draw label
        #if self.drawLabel:
            #height = self.size().height()
            #width = self.size().width()
            #if self.orientation == 'left':
                #p.translate(0, height)
                #p.rotate(-90)
                #rect = QtCore.QRectF(0, 0, height, self.textHeight)
                #textFlags = QtCore.Qt.AlignCenter|QtCore.Qt.AlignTop
            #elif self.orientation == 'right':
                #p.rotate(10)
                #rect = QtCore.QRectF(0, 0, height, width)
                #textFlags = QtCore.Qt.AlignCenter|QtCore.Qt.AlignBottom
                ##rect = QtCore.QRectF(tickStart+self.tickLength, x-(height/2), 100-self.tickLength, height)
            #elif self.orientation == 'top':
                #rect = QtCore.QRectF(0, 0, width, height)
                #textFlags = QtCore.Qt.AlignCenter|QtCore.Qt.AlignTop
                ##rect = QtCore.QRectF(x-100, tickStart-self.tickLength-height, 200, height)
            #elif self.orientation == 'bottom':
                #rect = QtCore.QRectF(0, 0, width, height)
                #textFlags = QtCore.Qt.AlignCenter|QtCore.Qt.AlignBottom
                ##rect = QtCore.QRectF(x-100, tickStart+self.tickLength, 200, height)
            #p.drawText(rect, textFlags, self.labelString())
            ##p.drawRect(rect)
        
    def show(self):
        
        if self.orientation in ['left', 'right']:
            self.setWidth()
        else:
            self.setHeight()
        QtGui.QGraphicsWidget.show(self)
        
    def hide(self):
        if self.orientation in ['left', 'right']:
            self.setWidth(0)
        else:
            self.setHeight(0)
        QtGui.QGraphicsWidget.hide(self)

    def wheelEvent(self, ev):
        if self.linkedView is None or self.linkedView() is None: return
        if self.orientation in ['left', 'right']:
            self.linkedView().wheelEvent(ev, axis=1)
        else:
            self.linkedView().wheelEvent(ev, axis=0)
        ev.accept()



class ViewBox(QtGui.QGraphicsWidget):
    
    sigYRangeChanged = QtCore.Signal(object, object)
    sigXRangeChanged = QtCore.Signal(object, object)
    sigRangeChangedManually = QtCore.Signal(object)
    sigRangeChanged = QtCore.Signal(object, object)
    sigClick=QtCore.Signal(QtCore.QPointF)
    
    """Box that allows internal scaling/panning of children by mouse drag. Not compatible with GraphicsView having the same functionality."""
    def __init__(self, minX, maxX, maxY, parent=None, border=None):# minX, maxX, maxY,
        QtGui.QGraphicsWidget.__init__(self, parent)
        #self.gView = view
        #self.showGrid = showGrid
        
        ## separating targetRange and viewRange allows the view to be resized
        ## while keeping all previously viewed contents visible
        self.minX = minX
        self.maxX = maxX
        self.maxY = maxY
        
        self.targetRange = [[0,1], [0,1]]   ## child coord. range visible [[xmin, xmax], [ymin, ymax]]
        self.viewRange = [[0,1], [0,1]]     ## actual range viewed
        
        self.wheelScaleFactor = -1.0 / 8.0
        self.aspectLocked = False
        self.setFlag(QtGui.QGraphicsItem.ItemClipsChildrenToShape)
        #self.setFlag(QtGui.QGraphicsItem.ItemClipsToShape)
        #self.setCacheMode(QtGui.QGraphicsItem.DeviceCoordinateCache)
        
        #self.childGroup = QtGui.QGraphicsItemGroup(self)
        self.childGroup = ItemGroup(self)
        self.currentScale = Point(1, 1)
        
        self.yInverted = False
        #self.invertY()
        self.setZValue(-100)
        #self.picture = None
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))
        
        self.border = border
        self.hasMoved = False
        
        self.showHorizontalLine = False
        self.hLinePos = [0., 0., 0.]
        
        self.mouseEnabled = [True, True]
    
    def setMouseEnabled(self, x, y):
        self.mouseEnabled = [x, y]
    
    def addItem(self, item):
        if item.zValue() < self.zValue():
            item.setZValue(self.zValue()+1)
        item.setParentItem(self.childGroup)
        #print "addItem:", item, item.boundingRect()
        
    def removeItem(self, item):
        self.scene().removeItem(item)
        
    def resizeEvent(self, ev):
        #self.setRange(self.range, padding=0)
        self.updateMatrix()
        

    def viewRect(self):
        try:
            vr0 = self.viewRange[0]
            vr1 = self.viewRange[1]
            return QtCore.QRectF(vr0[0], vr1[0], vr0[1]-vr0[0], vr1[1] - vr1[0])
        except:
            print "make qrectf failed:", self.viewRange
            raise
    
    def targetRect(self):  
        """Return the region which has been requested to be visible. 
        (this is not necessarily the same as the region that is *actually* visible)"""
        try:
            tr0 = self.targetRange[0]
            tr1 = self.targetRange[1]
            return QtCore.QRectF(tr0[0], tr1[0], tr0[1]-tr0[0], tr1[1] - tr1[0])
        except:
            print "make qrectf failed:", self.targetRange
            raise
    
    def invertY(self, b=True):
        self.yInverted = b
        self.updateMatrix()
        
    def setAspectLocked(self, lock=True, ratio=1):
        """If the aspect ratio is locked, view scaling is always forced to be isotropic.
        By default, the ratio is set to 1; x and y both have the same scaling.
        This ratio can be overridden (width/height), or use None to lock in the current ratio.
        """
        if not lock:
            self.aspectLocked = False
        else:
            vr = self.viewRect()
            currentRatio = vr.width() / vr.height()
            if ratio is None:
                ratio = currentRatio
            self.aspectLocked = ratio
            if ratio != currentRatio:  ## If this would change the current range, do that now
                #self.setRange(0, self.viewRange[0][0], self.viewRange[0][1])
                self.updateMatrix()
        
    def childTransform(self):
        m = self.childGroup.transform()
        m1 = QtGui.QTransform()
        m1.translate(self.childGroup.pos().x(), self.childGroup.pos().y())
        return m*m1
    

    def viewScale(self):
        vr = self.viewRect()
        #print "viewScale:", self.range
        xd = vr.width()
        yd = vr.height()
        if xd == 0 or yd == 0:
            print "Warning: 0 range in view:", xd, yd
            return np.array([1,1])
        
        #cs = self.canvas().size()
        cs = self.boundingRect()
        scale = np.array([cs.width() / xd, cs.height() / yd])
        #print "view scale:", scale
        return scale

    def scaleBy(self, s, center=None):
        """Scale by s around given center point (or center of view)"""
        #print "scaleBy", s, center
        #if self.aspectLocked:
            #s[0] = s[1]
        scale = Point(s)
        if self.aspectLocked is not False:
            scale[0] = self.aspectLocked * scale[1]
            
            
        #xr, yr = self.range
        vr = self.viewRect()
        if center is None:
            center = Point(vr.center())
            #xc = (xr[1] + xr[0]) * 0.5
            #yc = (yr[1] + yr[0]) * 0.5
        else:
            center = Point(center)
            #(xc, yc) = center
        
        #x1 = xc + (xr[0]-xc) * s[0]
        #x2 = xc + (xr[1]-xc) * s[0]
        #y1 = yc + (yr[0]-yc) * s[1]
        #y2 = yc + (yr[1]-yc) * s[1]
        tl = center + (vr.topLeft()-center) * scale
        br = center + (vr.bottomRight()-center) * scale
    
        
        #print xr, xc, s, (xr[0]-xc) * s[0], (xr[1]-xc) * s[0]
        #print [[x1, x2], [y1, y2]]
        
        #if not self.aspectLocked:
            #self.setXRange(x1, x2, update=False, padding=0)
        #self.setYRange(y1, y2, padding=0)
        #print self.range
        
        self.setRange(QtCore.QRectF(tl, br), padding=0)
        
    def translateBy(self, t, viewCoords=False):
        t = t.astype(np.float)
        #print "translate:", t, self.viewScale()
        if viewCoords:  ## scale from pixels
            t /= self.viewScale()
        #xr, yr = self.range
        
        vr = self.viewRect()
        #trans = vr.translated(Point(t))
        #tl = trans.topLeft()
        #br = trans.bottomRight()
        
#        if tl.x() < self.minX - (self.minX/2):# or br.x() > self.maxX or br.x() < self.minX or tl.x() > self.maxX:        
#            return            
#            #tl.setX(self.minX)
#            #br.setX(vr.bottomRight().x())
#        if br.x() > self.maxX + (self.maxX/2):
#            return            
#            #br.setX(self.maxX)
#            #tl.setX(vr.topLeft().x())
#        if tl.y() > self.maxY/2:
#            return            
#            #tl.setX(self.maxX)
#        if br.y() < self.maxY/2:
#            return
        #if tl.y() > self.maxY or br.y() < 0. or br.y() > self.maxY or tl.y() < 0.:
            #return            
        #    tl.setY(self.maxY)
        #    br.setY(0.)
        #trans.setBottomRight(br)
        #trans.setTopLeft(tl)
            #tr.setY(0.)
        #print xr, yr, t
        #self.setXRange(xr[0] + t[0], xr[1] + t[0], update=False, padding=0)
        #self.setYRange(yr[0] + t[1], yr[1] + t[1], padding=0)
        self.setRange(vr.translated(Point(t)), padding=0)#, padding=0)
        
    def wheelEvent(self, ev, axis=None):
        mask = np.array(self.mouseEnabled, dtype=np.float)
        if axis is not None and axis >= 0 and axis < len(mask):
            mv = mask[axis]
            mask[:] = 0
            mask[axis] = mv
        s = ((mask * 0.02) + 1) ** (ev.delta() * self.wheelScaleFactor) # actual scaling factor
        # scale 'around' mouse cursor position
        center = Point(self.childGroup.transform().inverted()[0].map(ev.pos()))
        self.scaleBy(s, center)
        #self.emit(QtCore.SIGNAL('rangeChangedManually'), self.mouseEnabled)
        self.sigRangeChangedManually.emit(self.mouseEnabled)
        ev.accept()

    def mouseMoveEvent(self, ev):
        p=self.childGroup.transform().inverted()[0].map(ev.pos())
        QtGui.QToolTip.showText(QtGui.QCursor.pos(), ", ".join([str(np.round(p.x(),2)), str(np.round(p.y(), 2))]))        
        QtGui.QGraphicsWidget.mouseMoveEvent(self, ev)
    
        pos = np.array([ev.pos().x(), ev.pos().y()])
        dif = pos - self.mousePos
        dif *= -1
        self.mousePos = pos
        
        ## Ignore axes if mouse is disabled
        mask = np.array(self.mouseEnabled, dtype=np.float)
        
        ## Scale or translate based on mouse button
        if ev.buttons() == QtCore.Qt.LeftButton and not ev.modifiers():
            if not self.yInverted:
                mask *= np.array([1, -1])
            tr = dif*mask
            self.translateBy(tr, viewCoords=True)
            #self.emit(QtCore.SIGNAL('rangeChangedManually'), self.mouseEnabled)
            self.sigRangeChangedManually.emit(self.mouseEnabled)
            ev.accept()
            
        elif ev.buttons() == QtCore.Qt.RightButton and not ev.modifiers():
            if self.aspectLocked is not False:
                mask[0] = 0
            dif = ev.screenPos() - ev.lastScreenPos()
            dif = np.array([dif.x(), dif.y()])
            dif[0] *= -1
            s = ((mask * 0.02) + 1) ** dif
            #print mask, dif, s
            center = Point(self.childGroup.transform().inverted()[0].map(ev.buttonDownPos(QtCore.Qt.RightButton)))
            self.scaleBy(s, center)
            #self.emit(QtCore.SIGNAL('rangeChangedManually'), self.mouseEnabled)
            self.sigRangeChangedManually.emit(self.mouseEnabled)
            ev.accept()
        elif ev.buttons() == QtCore.Qt.LeftButton and ev.modifiers():# == QtCore.Qt.Key_Control:             
             if self.showHorizontalLine:
                 p=self.childGroup.transform().inverted()[0].map(ev.pos())
                 self.hLinePos[1] = p.x()
                 self.update()
        else:
            ev.ignore()
        self.hasMoved = False
    
    def mousePressEvent(self, ev):
        self.sigClick.emit(self.childGroup.transform().inverted()[0].map(ev.pos()))
        QtGui.QGraphicsWidget.mousePressEvent(self, ev)
        
        self.mousePos = np.array([ev.pos().x(), ev.pos().y()])
        self.pressPos = self.mousePos.copy()
        self.hasMoved = True
        
        if ev.buttons() == QtCore.Qt.LeftButton and ev.modifiers():# == QtCore.Qt.Key_Control:
            self.showHorizontalLine = True
            #print "x, y start position", ev.pos().x(), ev.pos().y()
            p=self.childGroup.transform().inverted()[0].map(ev.pos())
            self.hLinePos[0] = p.x()
            self.hLinePos[2] = p.y()
        ev.accept()
        
    def mouseReleaseEvent(self, ev):
        QtGui.QGraphicsWidget.mouseReleaseEvent(self, ev)
        pos = np.array([ev.pos().x(), ev.pos().y()])
        #if sum(abs(self.pressPos - pos)) < 3:  ## Detect click
            #if ev.button() == QtCore.Qt.RightButton:
                #self.ctrlMenu.popup(self.mapToGlobal(ev.pos()))
        self.mousePos = pos
        if self.showHorizontalLine:
        #    self.hLinePos[1] = ev.pos().x()
            self.emit(QtCore.SIGNAL('showDiffOrSpectra(PyQt_PyObject)'), self.hLinePos)
        self.showHorizontalLine = False
        self.hLinePos = [0]*3
        ev.accept()
        
    def setRange(self, ax, min=None, max=None, padding=0.02, update=True):
        if isinstance(ax, QtCore.QRectF):
            changes = {0: [ax.left(), ax.right()], 1: [ax.top(), ax.bottom()]}
            #if self.aspectLocked is not False:
                #sbr = self.boundingRect()
                #if sbr.width() == 0 or (ax.height()/ax.width()) > (sbr.height()/sbr.width()):
                    #chax = 0
                #else:
                    #chax = 1
                    
                
                    
            
        elif ax in [1,0]:
            changes = {ax: [min,max]}
            #if self.aspectLocked is not False:
                #ax2 = 1 - ax
                #ratio = self.aspectLocked
                #r2 = self.range[ax2]
                #d = ratio * (max-min) * 0.5
                #c = (self.range[ax2][1] + self.range[ax2][0]) * 0.5
                #changes[ax2] = [c-d, c+d]
           
        else:
            print ax
            raise Exception("argument 'ax' must be 0, 1, or QRectF.")
        
        
        changed = [False, False]
        for ax, range in changes.iteritems():
            min, max = range
            if min == max:   ## If we requested 0 range, try to preserve previous scale. Otherwise just pick an arbitrary scale.
                dy = self.viewRange[ax][1] - self.viewRange[ax][0]
                if dy == 0:
                    dy = 1
                min -= dy*0.5
                max += dy*0.5
                padding = 0.0
            if any(np.isnan([min, max])) or any(np.isinf([min, max])):
                raise Exception("Not setting range [%s, %s]" % (str(min), str(max)))
                
            p = (max-min) * padding
            min -= p
            max += p
            
            if self.targetRange[ax] != [min, max]:
                self.targetRange[ax] = [min, max]
                changed[ax] = True
            
        if update:
            self.updateMatrix(changed)
            
        
            
            
    def setYRange(self, min, max, update=True, padding=0.02):
        self.setRange(1, min, max, update=update, padding=padding)
        
    def setXRange(self, min, max, update=True, padding=0.02):
        self.setRange(0, min, max, update=update, padding=padding)

    def autoRange(self, padding=0.02):
        br = self.childGroup.childrenBoundingRect()
        self.setRange(br, padding=padding)


    def updateMatrix(self, changed=None):
        if changed is None:
            changed = [False, False]
        #print "udpateMatrix:"
        #print "  range:", self.range
        tr = self.targetRect()
        bounds = self.boundingRect()
        #vr = self.viewRect() 
        ## set viewRect, given targetRect and possibly aspect ratio constraint
        if self.aspectLocked is False or bounds.height() == 0:
#            targetRange = [self.targetRange[0][:], self.targetRange[1][:]]
#            if self.targetRange[0][0] < self.minX:
#                 return                 
#                 #targetRange = self.viewRange
##                self.targetRange[0][0] = self.minX
##                self.targetRange[0][1] = self.maxX
##                
#            if self.targetRange[0][1] > self.maxX:
#               return 
#                #targetRange = self.viewRange
##                self.targetRange[0][0] = self.minX
##                
#            if self.targetRange[1][1] > self.maxY:
#                return                
#                #targetRange = self.viewRange
##                self.targetRange[1][1] = self.maxY
##                self.targetRange[1][0] = -self.maxY
###                
#            if self.targetRange[1][0] < -self.maxY:
#                return                
#                #targetRange = self.viewRange
##                self.targetRange[1][0] = -self.maxY
##                self.targetRange[1][1] = self.maxY
            self.viewRange = [self.targetRange[0][:], self.targetRange[1][:]]

        else:
            viewRatio = bounds.width() / bounds.height()
            targetRatio = self.aspectLocked * tr.width() / tr.height()
            if targetRatio > viewRatio:  
                ## target is wider than view
                dy = 0.5 * (tr.width() / (self.aspectLocked * viewRatio) - tr.height())
                if dy != 0:
                    changed[1] = True
                self.viewRange = [self.targetRange[0][:], [self.targetRange[1][0] - dy, self.targetRange[1][1] + dy]]
            else:
                dx = 0.5 * (tr.height() * viewRatio * self.aspectLocked - tr.width())
                if dx != 0:
                    changed[0] = True
                self.viewRange = [[self.targetRange[0][0] - dx, self.targetRange[0][1] + dx], self.targetRange[1][:]]
        
        
        vr = self.viewRect()
        translate = Point(vr.center())
        #print "  bounds:", bounds
        if vr.height() == 0 or vr.width() == 0:
            return
        scale = Point(bounds.width()/vr.width(), bounds.height()/vr.height())
        #print "  scale:", scale
        m = QtGui.QTransform()
        
        ## First center the viewport at 0
        self.childGroup.resetTransform()
        center = self.transform().inverted()[0].map(bounds.center())
        #print "  transform to center:", center
        if self.yInverted:
            m.translate(center.x(), -center.y())
            #print "  inverted; translate", center.x(), center.y()
        else:
            m.translate(center.x(), center.y())
            #print "  not inverted; translate", center.x(), -center.y()
            
        ## Now scale and translate properly
        if not self.yInverted:
            scale = scale * Point(1, -1)
        m.scale(scale[0], scale[1])
        st = translate
        m.translate(-st[0], -st[1])
        self.childGroup.setTransform(m)
        self.currentScale = scale
        
        
        if changed[0]:
            self.sigXRangeChanged.emit(self, tuple(self.viewRange[0]))
        if changed[1]:
            self.sigYRangeChanged.emit(self, tuple(self.viewRange[1]))
        if any(changed):
            self.sigRangeChanged.emit(self, self.viewRange)
            


    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.size().width(), self.size().height())
        
    def paint(self, p, opt, widget):
        if self.border is not None:
            bounds = self.boundingRect()
            p.setPen(self.border)
            #p.fillRect(bounds, QtGui.QColor(0, 0, 0))
            p.drawRect(bounds)
        if self.showHorizontalLine:
            p.drawLine(QtCore.QPoint(self.hLinePos[0], self.hLinePos[2]),
                       QtCore.QPoint(self.hLinePos[1], self.hLinePos[2]))
            self.update()


class InfiniteLine(GraphicsObject):
    
    sigDragged = QtCore.Signal(object)
    sigPositionChangeFinished = QtCore.Signal(object)
    sigPositionChanged = QtCore.Signal(object)
    
    def __init__(self, view, pos=0, angle=90, pen=None, movable=False, bounds=None):
        GraphicsObject.__init__(self)
        self.bounds = QtCore.QRectF()   ## graphicsitem boundary
        
        if bounds is None:              ## allowed value boundaries for orthogonal lines
            self.maxRange = [None, None]
        else:
            self.maxRange = bounds
        self.setMovable(movable)
        self.view = weakref.ref(view)
        self.p = [0, 0]
        self.setAngle(angle)
        self.setPos(pos)
            
            
        self.hasMoved = False

        
        if pen is None:
            pen = QtGui.QPen(QtGui.QColor(200, 200, 100))
        self.setPen(pen)
        self.currentPen = self.pen
        #self.setFlag(self.ItemSendsScenePositionChanges)
        #for p in self.getBoundingParents():
            #QtCore.QObject.connect(p, QtCore.SIGNAL('viewChanged'), self.updateLine)
        #QtCore.QObject.connect(self.view(), QtCore.SIGNAL('viewChanged'), self.updateLine)
        self.view().sigRangeChanged.connect(self.updateLine)
      
    def setMovable(self, m):
        self.movable = m
        self.setAcceptHoverEvents(m)
        
      
    def setBounds(self, bounds):
        self.maxRange = bounds
        self.setValue(self.value())
        
    def hoverEnterEvent(self, ev):
        self.currentPen = QtGui.QPen(QtGui.QColor(255, 0,0))
        self.update()
        ev.ignore()

    def hoverLeaveEvent(self, ev):
        self.currentPen = self.pen
        self.update()
        ev.ignore()
        
    def setPen(self, pen):
        self.pen = pen
        self.currentPen = self.pen
        
    def setAngle(self, angle):
        """Takes angle argument in degrees."""
        self.angle = ((angle+45) % 180) - 45   ##  -45 <= angle < 135
        self.updateLine()
        
    def setPos(self, pos):
        if type(pos) in [list, tuple]:
            newPos = pos
        elif isinstance(pos, QtCore.QPointF):
            newPos = [pos.x(), pos.y()]
        else:
            if self.angle == 90:
                newPos = [pos, 0]
            elif self.angle == 0:
                newPos = [0, pos]
            else:
                raise Exception("Must specify 2D coordinate for non-orthogonal lines.")
            
        ## check bounds (only works for orthogonal lines)
        if self.angle == 90:
            if self.maxRange[0] is not None:    
                newPos[0] = max(newPos[0], self.maxRange[0])
            if self.maxRange[1] is not None:
                newPos[0] = min(newPos[0], self.maxRange[1])
        elif self.angle == 0:
            if self.maxRange[0] is not None:
                newPos[1] = max(newPos[1], self.maxRange[0])
            if self.maxRange[1] is not None:
                newPos[1] = min(newPos[1], self.maxRange[1])
            
            
        if self.p != newPos:
            self.p = newPos
            self.updateLine()
            #self.emit(QtCore.SIGNAL('positionChanged'), self)
            self.sigPositionChanged.emit(self)

    def getXPos(self):
        return self.p[0]
        
    def getYPos(self):
        return self.p[1]
        
    def getPos(self):
        return self.p

    def value(self):
        if self.angle%180 == 0:
            return self.getYPos()
        elif self.angle%180 == 90:
            return self.getXPos()
        else:
            return self.getPos()
                
    def setValue(self, v):
        self.setPos(v)

    ## broken in 4.7
    #def itemChange(self, change, val):
        #if change in [self.ItemScenePositionHasChanged, self.ItemSceneHasChanged]:
            #self.updateLine()
            #print "update", change
            #print self.getBoundingParents()
        #else:
            #print "ignore", change
        #return GraphicsObject.itemChange(self, change, val)
                
    def updateLine(self):

        #unit = QtCore.QRect(0, 0, 10, 10)
        #if self.scene() is not None:
            #gv = self.scene().views()[0]
            #unit = gv.mapToScene(unit).boundingRect()
            ##print unit
            #unit = self.mapRectFromScene(unit)
            ##print unit
        
        vr = self.view().viewRect()
        #vr = self.viewBounds()
        if vr is None:
            return
        #print 'before', self.bounds
        
        if self.angle > 45:
            m = np.tan((90-self.angle) * np.pi / 180.)
            y2 = vr.bottom()
            y1 = vr.top()
            x1 = self.p[0] + (y1 - self.p[1]) * m
            x2 = self.p[0] + (y2 - self.p[1]) * m
        else:
            m = np.tan(self.angle * np.pi / 180.)
            x1 = vr.left()
            x2 = vr.right()
            y2 = self.p[1] + (x1 - self.p[0]) * m
            y1 = self.p[1] + (x2 - self.p[0]) * m
        #print vr, x1, y1, x2, y2
        self.prepareGeometryChange()
        self.line = (QtCore.QPointF(x1, y1), QtCore.QPointF(x2, y2))
        self.bounds = QtCore.QRectF(self.line[0], self.line[1])
        ## Stupid bug causes lines to disappear:
        if self.angle % 180 == 90:
            px = self.pixelWidth()
            #self.bounds.setWidth(1e-9)
            self.bounds.setX(x1 + px*-5)
            self.bounds.setWidth(px*10)
        if self.angle % 180 == 0:
            px = self.pixelHeight()
            #self.bounds.setHeight(1e-9)
            self.bounds.setY(y1 + px*-5)
            self.bounds.setHeight(px*10)

        #QtGui.QGraphicsLineItem.setLine(self, x1, y1, x2, y2)
        #self.update()
        
    def boundingRect(self):
        #self.updateLine()
        #return QtGui.QGraphicsLineItem.boundingRect(self)
        #print "bounds", self.bounds
        return self.bounds
    
    def paint(self, p, *args):
        w,h  = self.pixelWidth()*5, self.pixelHeight()*5*1.1547
        #self.updateLine()
        l = self.line
        
        p.setPen(self.currentPen)
        #print "paint", self.line
        p.drawLine(l[0], l[1])
        
        p.setBrush(QtGui.QBrush(self.currentPen.color()))
        p.drawConvexPolygon(QtGui.QPolygonF([
            l[0] + QtCore.QPointF(-w, 0),
            l[0] + QtCore.QPointF(0, h),
            l[0] + QtCore.QPointF(w, 0),
        ]))
        
        #p.setPen(QtGui.QPen(QtGui.QColor(255,0,0)))
        #p.drawRect(self.boundingRect())
        
    def mousePressEvent(self, ev):
        if self.movable and ev.button() == QtCore.Qt.LeftButton:
            ev.accept()
            self.pressDelta = self.mapToParent(ev.pos()) - QtCore.QPointF(*self.p)
        else:
            ev.ignore()
            
    def mouseMoveEvent(self, ev):
        self.setPos(self.mapToParent(ev.pos()) - self.pressDelta)
        #self.emit(QtCore.SIGNAL('dragged'), self)
        self.sigDragged.emit(self)
        self.hasMoved = True

    def mouseReleaseEvent(self, ev):
        if self.hasMoved and ev.button() == QtCore.Qt.LeftButton:
            self.hasMoved = False
            #self.emit(QtCore.SIGNAL('positionChangeFinished'), self)
            self.sigPositionChangeFinished.emit(self)
            


class LinearRegionItem(GraphicsObject):
    
    sigRegionChangeFinished = QtCore.Signal(object)
    sigRegionChanged = QtCore.Signal(object)
    
    """Used for marking a horizontal or vertical region in plots."""
    def __init__(self, view, orientation="vertical", vals=[0,1], brush=None, movable=True, bounds=None):
        GraphicsObject.__init__(self)
        self.orientation = orientation
        if hasattr(self, "ItemHasNoContents"):  
            self.setFlag(self.ItemHasNoContents)
        self.rect = QtGui.QGraphicsRectItem(self)
        self.rect.setParentItem(self)
        self.bounds = QtCore.QRectF()
        self.view = weakref.ref(view)
        self.setBrush = self.rect.setBrush
        self.brush = self.rect.brush
        
        if orientation[0] == 'h':
            self.lines = [
                InfiniteLine(view, QtCore.QPointF(0, vals[0]), 0, movable=movable, bounds=bounds), 
                InfiniteLine(view, QtCore.QPointF(0, vals[1]), 0, movable=movable, bounds=bounds)]
        else:
            self.lines = [
                InfiniteLine(view, QtCore.QPointF(vals[0], 0), 90, movable=movable, bounds=bounds), 
                InfiniteLine(view, QtCore.QPointF(vals[1], 0), 90, movable=movable, bounds=bounds)]
        #QtCore.QObject.connect(self.view(), QtCore.SIGNAL('viewChanged'), self.updateBounds)
        self.view().sigRangeChanged.connect(self.updateBounds)
        
        for l in self.lines:
            l.setParentItem(self)
            #l.connect(l, QtCore.SIGNAL('positionChangeFinished'), self.lineMoveFinished)
            l.sigPositionChangeFinished.connect(self.lineMoveFinished)
            #l.connect(l, QtCore.SIGNAL('positionChanged'), self.lineMoved)
            l.sigPositionChanged.connect(self.lineMoved)
            
        if brush is None:
            brush = QtGui.QBrush(QtGui.QColor(0, 0, 255, 50))
        self.setBrush(brush)
        self.setMovable(movable)
            
    def setBounds(self, bounds):
        for l in self.lines:
            l.setBounds(bounds)
        
    def setMovable(self, m):
        for l in self.lines:
            l.setMovable(m)
        self.movable = m

    def boundingRect(self):
        return self.rect.boundingRect()
            
    def lineMoved(self):
        self.updateBounds()
        #self.emit(QtCore.SIGNAL('regionChanged'), self)
        self.sigRegionChanged.emit(self)
            
    def lineMoveFinished(self):
        #self.emit(QtCore.SIGNAL('regionChangeFinished'), self)
        self.sigRegionChangeFinished.emit(self)
        
            
    def updateBounds(self):
        vb = self.view().viewRect()
        vals = [self.lines[0].value(), self.lines[1].value()]
        if self.orientation[0] == 'h':
            vb.setTop(min(vals))
            vb.setBottom(max(vals))
        else:
            vb.setLeft(min(vals))
            vb.setRight(max(vals))
        if vb != self.bounds:
            self.bounds = vb
            self.rect.setRect(vb)
        
    def mousePressEvent(self, ev):
        if not self.movable:
            ev.ignore()
            return
        for l in self.lines:
            l.mousePressEvent(ev)  ## pass event to both lines so they move together
        #if self.movable and ev.button() == QtCore.Qt.LeftButton:
            #ev.accept()
            #self.pressDelta = self.mapToParent(ev.pos()) - QtCore.QPointF(*self.p)
        #else:
            #ev.ignore()
            
    def mouseReleaseEvent(self, ev):
        for l in self.lines:
            l.mouseReleaseEvent(ev)
            
    def mouseMoveEvent(self, ev):
        #print "move", ev.pos()
        if not self.movable:
            return
        self.lines[0].blockSignals(True)  # only want to update once
        for l in self.lines:
            l.mouseMoveEvent(ev)
        self.lines[0].blockSignals(False)
        #self.setPos(self.mapToParent(ev.pos()) - self.pressDelta)
        #self.emit(QtCore.SIGNAL('dragged'), self)

    def getRegion(self):
        if self.orientation[0] == 'h':
            r = (self.bounds.top(), self.bounds.bottom())
        else:
            r = (self.bounds.left(), self.bounds.right())
        return (min(r), max(r))

    def setRegion(self, rgn):
        self.lines[0].setValue(rgn[0])
        self.lines[1].setValue(rgn[1])


class VTickGroup(QtGui.QGraphicsPathItem):
    def __init__(self, xvals=None, yrange=None, pen=None, relative=False, view=None):
        QtGui.QGraphicsPathItem.__init__(self)
        if yrange is None:
            yrange = [0, 1]
        if xvals is None:
            xvals = []
        if pen is None:
            pen = (200, 200, 200)
        self.ticks = []
        self.xvals = []
        if view is None:
            self.view = None
        else:
            self.view = weakref.ref(view)
        self.yrange = [0,1]
        self.setPen(pen)
        self.setYRange(yrange, relative)
        self.setXVals(xvals)
        self.valid = False
        
    def setPen(self, pen):
        pen = mkPen(pen)
        QtGui.QGraphicsPathItem.setPen(self, pen)

    def setXVals(self, vals):
        self.xvals = vals
        self.rebuildTicks()
        self.valid = False
        
    def setYRange(self, vals, relative=False):
        self.yrange = vals
        self.relative = relative
        if self.view is not None:
            if relative:
                #QtCore.QObject.connect(self.view, QtCore.SIGNAL('viewChanged'), self.rebuildTicks)
                #QtCore.QObject.connect(self.view(), QtCore.SIGNAL('viewChanged'), self.rescale)
                self.view().sigRangeChanged.connect(self.rescale)
            else:
                try:
                    #QtCore.QObject.disconnect(self.view, QtCore.SIGNAL('viewChanged'), self.rebuildTicks)
                    #QtCore.QObject.disconnect(self.view(), QtCore.SIGNAL('viewChanged'), self.rescale)
                    self.view().sigRangeChanged.disconnect(self.rescale)
                except:
                    pass
        self.rebuildTicks()
        self.valid = False
            
    def rescale(self):
        #print "RESCALE:"
        self.resetTransform()
        #height = self.view.size().height()
        #p1 = self.mapFromScene(self.view.mapToScene(QtCore.QPoint(0, height * (1.0-self.yrange[0]))))
        #p2 = self.mapFromScene(self.view.mapToScene(QtCore.QPoint(0, height * (1.0-self.yrange[1]))))
        #yr = [p1.y(), p2.y()]
        vb = self.view().viewRect()
        p1 = vb.bottom() - vb.height() * self.yrange[0]
        p2 = vb.bottom() - vb.height() * self.yrange[1]
        yr = [p1, p2]
        
        #print "  ", vb, yr
        self.translate(0.0, yr[0])
        self.scale(1.0, (yr[1]-yr[0]))
        #print "  ", self.mapRectToScene(self.boundingRect())
        self.boundingRect()
        self.update()
            
    def boundingRect(self):
        #print "--request bounds:"
        b = QtGui.QGraphicsPathItem.boundingRect(self)
        #print "  ", self.mapRectToScene(b)
        return b
            
    def yRange(self):
        #if self.relative:
            #height = self.view.size().height()
            #p1 = self.mapFromScene(self.view.mapToScene(QtCore.QPoint(0, height * (1.0-self.yrange[0]))))
            #p2 = self.mapFromScene(self.view.mapToScene(QtCore.QPoint(0, height * (1.0-self.yrange[1]))))
            #return [p1.y(), p2.y()]
        #else:
            #return self.yrange
            
        return self.yrange
            
    def rebuildTicks(self):
        self.path = QtGui.QPainterPath()
        yrange = self.yRange()
        #print "rebuild ticks:", yrange
        for x in self.xvals:
            #path.moveTo(x, yrange[0])
            #path.lineTo(x, yrange[1])
            self.path.moveTo(x, 0.)
            self.path.lineTo(x, 1.)
        self.setPath(self.path)
        self.valid = True
        self.rescale()
        #print "  done..", self.boundingRect()
        
    def paint(self, *args):
        if not self.valid:
            self.rebuildTicks()
        #print "Paint", self.boundingRect()
        QtGui.QGraphicsPathItem.paint(self, *args)
        

class GridItem(UIGraphicsItem):
    """Class used to make square grids in plots. NOT the grid used for running scanner sequences."""
    
    def __init__(self, view, bounds=None, *args):
        UIGraphicsItem.__init__(self, view, bounds)
        #QtGui.QGraphicsItem.__init__(self, *args)
        self.setFlag(QtGui.QGraphicsItem.ItemClipsToShape)
        #self.setCacheMode(QtGui.QGraphicsItem.DeviceCoordinateCache)
        
        self.picture = None
        
        
    def viewRangeChanged(self):
        self.picture = None
        UIGraphicsItem.viewRangeChanged(self)
        #self.update()
        
    def paint(self, p, opt, widget):
        #p.setPen(QtGui.QPen(QtGui.QColor(100, 100, 100)))
        #p.drawRect(self.boundingRect())
        
        ## draw picture
        if self.picture is None:
            #print "no pic, draw.."
            self.generatePicture()
        p.drawPicture(0, 0, self.picture)
        #print "draw"
        
        
    def generatePicture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter()
        p.begin(self.picture)
        
        dt = self.viewTransform().inverted()[0]
        vr = self.viewRect()
        unit = self.unitRect()
        dim = [vr.width(), vr.height()]
        lvr = self.boundingRect()
        ul = np.array([lvr.left(), lvr.top()])
        br = np.array([lvr.right(), lvr.bottom()])
        
        texts = []
        
        if ul[1] > br[1]:
            x = ul[1]
            ul[1] = br[1]
            br[1] = x
        for i in range(2, -1, -1):   ## Draw three different scales of grid
            
            dist = br-ul
            nlTarget = 10.**i
            d = 10. ** np.floor(np.log10(abs(dist/nlTarget))+0.5)
            ul1 = np.floor(ul / d) * d
            br1 = np.ceil(br / d) * d
            dist = br1-ul1
            nl = (dist / d) + 0.5
            for ax in range(0,2):  ## Draw grid for both axes
                ppl = dim[ax] / nl[ax]
                c = np.clip(3.*(ppl-3), 0., 30.)
                linePen = QtGui.QPen(QtGui.QColor(255, 255, 255, c)) 
                textPen = QtGui.QPen(QtGui.QColor(255, 255, 255, c*2)) 
                
                bx = (ax+1) % 2
                for x in range(0, int(nl[ax])):
                    p.setPen(linePen)
                    p1 = np.array([0.,0.])
                    p2 = np.array([0.,0.])
                    p1[ax] = ul1[ax] + x * d[ax]
                    p2[ax] = p1[ax]
                    p1[bx] = ul[bx]
                    p2[bx] = br[bx]
                    p.drawLine(QtCore.QPointF(p1[0], p1[1]), QtCore.QPointF(p2[0], p2[1]))
                    if i < 2:
                        p.setPen(textPen)
                        if ax == 0:
                            x = p1[0] + unit.width()
                            y = ul[1] + unit.height() * 8.
                        else:
                            x = ul[0] + unit.width()*3
                            y = p1[1] + unit.height()
                        texts.append((QtCore.QPointF(x, y), "%g"%p1[ax]))
        tr = self.viewTransform()
        tr.scale(1.5, 1.5)
        p.setWorldTransform(tr.inverted()[0])
        for t in texts:
            x = tr.map(t[0])
            p.drawText(x, t[1])
        p.end()

class ScaleBar(UIGraphicsItem):
    def __init__(self, view, size, width=.1, color=(100, 100, 255)):
        self.size = size
        UIGraphicsItem.__init__(self, view)
        self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        #self.pen = QtGui.QPen(QtGui.QColor(*color))
        #self.pen.setWidthF(width)
        #self.pen.setCosmetic(True)
        #self.pen2 = QtGui.QPen(QtGui.QColor(0,0,0))
        #self.pen2.setWidth(width+2)
        #self.pen2.setCosmetic(True)
        self.brush = QtGui.QBrush(QtGui.QColor(*color))
        self.pen = QtGui.QPen(QtGui.QColor(0,0,0))
        #self.pen.setWidthF(0.1)        
        self.width = width
        
    def paint(self, p, opt, widget):
        rect = self.boundingRect()
        unit = self.unitRect()
        y = rect.bottom() + (rect.top()-rect.bottom()) * 0.02
        y1 = y + unit.height()*self.width
        x = rect.right() + (rect.left()-rect.right()) * 0.02
        x1 = x - self.size
        
        
        p.setPen(self.pen)
        p.setBrush(self.brush)
        rect = QtCore.QRectF(
            QtCore.QPointF(x1, y1), 
            QtCore.QPointF(x, y)
        )
        p.translate(x1, y1)
        p.scale(rect.width(), rect.height())
        p.drawRect(0, 0, 1, 1)
        
        alpha = np.clip(((self.size/unit.width()) - 40.) * 255. / 80., 0, 255)
        p.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, alpha)))
        for i in range(1, 10):
            #x2 = x + (x1-x) * 0.1 * i
            x2 = 0.1 * i
            p.drawLine(QtCore.QPointF(x2, 0), QtCore.QPointF(x2, 1))
        

    def setSize(self, s):
        self.size = s
        
class ColorScaleBar(UIGraphicsItem):
    def __init__(self, view, size, offset):
        self.size = size
        self.offset = offset
        UIGraphicsItem.__init__(self, view)
        self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        self.brush = QtGui.QBrush(QtGui.QColor(200,0,0))
        self.pen = QtGui.QPen(QtGui.QColor(0,0,0))
        self.labels = {'max': 1, 'min': 0}
        self.gradient = QtGui.QLinearGradient()
        self.gradient.setColorAt(0, QtGui.QColor(0,0,0))
        self.gradient.setColorAt(1, QtGui.QColor(255,0,0))
        
    def setGradient(self, g):
        self.gradient = g
        self.update()
        
    def setIntColorScale(self, minVal, maxVal, *args, **kargs):
        colors = [intColor(i, maxVal-minVal, *args, **kargs) for i in range(minVal, maxVal)]
        g = QtGui.QLinearGradient()
        for i in range(len(colors)):
            x = float(i)/len(colors)
            g.setColorAt(x, colors[i])
        self.setGradient(g)
        if 'labels' not in kargs:
            self.setLabels({str(minVal/10.): 0, str(maxVal): 1})
        else:
            self.setLabels({kargs['labels'][0]:0, kargs['labels'][1]:1})
        
    def setLabels(self, l):
        """Defines labels to appear next to the color scale"""
        self.labels = l
        self.update()
        
    def paint(self, p, opt, widget):
        rect = self.boundingRect()   ## Boundaries of visible area in scene coords.
        unit = self.unitRect()       ## Size of one view pixel in scene coords.
        
        ## determine max width of all labels
        labelWidth = 0
        labelHeight = 0
        for k in self.labels:
            b = p.boundingRect(QtCore.QRectF(0, 0, 0, 0), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, str(k))
            labelWidth = max(labelWidth, b.width())
            labelHeight = max(labelHeight, b.height())
            
        labelWidth *= unit.width()
        labelHeight *= unit.height()
        
        textPadding = 2  # in px
        
        if self.offset[0] < 0:
            x3 = rect.right() + unit.width() * self.offset[0]
            x2 = x3 - labelWidth - unit.width()*textPadding*2
            x1 = x2 - unit.width() * self.size[0]
        else:
            x1 = rect.left() + unit.width() * self.offset[0]
            x2 = x1 + unit.width() * self.size[0]
            x3 = x2 + labelWidth + unit.width()*textPadding*2
        if self.offset[1] < 0:
            y2 = rect.top() - unit.height() * self.offset[1]
            y1 = y2 + unit.height() * self.size[1]
        else:
            y1 = rect.bottom() - unit.height() * self.offset[1]
            y2 = y1 - unit.height() * self.size[1]
        self.b = [x1,x2,x3,y1,y2,labelWidth]
            
        ## Draw background
        p.setPen(self.pen)
        p.setBrush(QtGui.QBrush(QtGui.QColor(255,255,255,100)))
        rect = QtCore.QRectF(
            QtCore.QPointF(x1 - unit.width()*textPadding, y1 + labelHeight/2 + unit.height()*textPadding), 
            QtCore.QPointF(x3, y2 - labelHeight/2 - unit.height()*textPadding)
        )
        p.drawRect(rect)
        
        
        ## Have to scale painter so that text and gradients are correct size. Bleh.
        p.scale(unit.width(), unit.height())
        
        ## Draw color bar
        self.gradient.setStart(0, y1/unit.height())
        self.gradient.setFinalStop(0, y2/unit.height())
        p.setBrush(self.gradient)
        rect = QtCore.QRectF(
            QtCore.QPointF(x1/unit.width(), y1/unit.height()), 
            QtCore.QPointF(x2/unit.width(), y2/unit.height())
        )
        p.drawRect(rect)
        
        
        ## draw labels
        p.setPen(QtGui.QPen(QtGui.QColor(0,0,0)))
        tx = x2 + unit.width()*textPadding
        lh = labelHeight/unit.height()
        for k in self.labels:
            y = y1 + self.labels[k] * (y2-y1)
            p.drawText(QtCore.QRectF(tx/unit.width(), y/unit.height() - lh/2.0, 1000, lh), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, str(k))
            




class BarPlot(QtGui.QGraphicsItem):
    def __init__(self, parent=None, scene=None):
        QtGui.QGraphicsItem.__init__(self, parent, scene)
        self.setFlag(0x1)
        self.width = 0;
        self.height = 0;
        self.barwidth=10;
        self.yvalues, self.labels, self.colors=[],[],[]

    def boundingRect(self):
        return(QtCore.QRectF(0,0,self.width,self.height))

    def clear(self):
        self.yvalues, self.labels, self.colors=[],[],[]


    def setPeakGroup(self, group):
        if not group:
            print "Error not critic: can not set group in BarPlot"
            print "usually found in chroma mode..."
            return
        self.clear()
        if self.scene():
            self.width = self.scene().width()*0.20;
            self.barwidth = self.scene().height()*0.75/len(group);
            if (self.barwidth<3):self.barwidth=3;
            if (self.barwidth>15):self.barwidth=15;
            self.height = len(self.yvalues)*self.barwidth;
        for peak in group:
            if peak:
                self.labels.append(peak.sample.shortName());
                self.colors.append(QtGui.QColor.fromRgbF(*(peak.sample.color+(.7,))))
                self.yvalues.append(peak.area if peak.area else float(peak.height))
            else:
                self.labels.append("");
                self.colors.append(QtCore.Qt.gray);
                self.yvalues.append(0);



    def paint(self, painter, options, widget):

        visibleSamplesCount = len(self.yvalues)
        if (visibleSamplesCount == 0): 
            return
        if (not self.scene()): 
            return
        maxYvalue=max(self.yvalues)	
        maxBarHeight = self.scene().width()*0.25;
        if ( maxBarHeight < 10 ): 
            maxBarHeight=10;
        if ( maxBarHeight > 200 ): 
            maxBarHeight=200;
        barSpacer=1;
        font=QtGui.QFont("Helvetica", 8);
        fontsize = self.barwidth*0.8;
        if (fontsize < 1 ): fontsize=1; 
        font.setPointSizeF(fontsize);
        painter.setFont(font);
        fm=QtGui.QFontMetrics(font);
        lagendShift = fm.size(0,"100e+10").width();
        color = QtGui.QColor.fromRgbF(0.2,0.2,0.2,1.0);
        brush=QtGui.QBrush(color);
        legendX = 0;
        legendY = 0;
        title="Peak Area"
        painter.drawText(legendX-lagendShift,legendY-1,title);
        for i, value in enumerate(self.yvalues):#(int i=0; i < _yvalues.size(); i++ ) {
            posX = legendX;
            posY = legendY + i*self.barwidth;
            width = self.barwidth;
            height = value / maxYvalue * maxBarHeight;
            painter.setPen(QtCore.Qt.black);       
            if (value == 0 ): 
                painter.setPen(QtCore.Qt.gray);
            brush.setColor(self.colors[i]);
            brush.setStyle(QtCore.Qt.SolidPattern);
            painter.setBrush(brush);
            painter.drawRect(posX+3,posY,height,width);
            painter.drawText(posX+6,posY+self.barwidth-2, self.labels[i]);
            numType='g';
            numPrec=2;
            if (maxYvalue < 10000 ): numType='f'; numPrec=0;
            if (maxYvalue < 1000 ): numType='f';  numPrec=1;
            if (maxYvalue < 100 ):  numType='f'; numPrec=2;
            if (maxYvalue < 1 ): numType='f'; numPrec=3;
            if (value > 0):
                value = QtCore.QString.number(value,numType,numPrec);
                painter.drawText(posX-lagendShift,posY+self.barwidth-2,value);
            if ( posY+self.barwidth > self.height): 
                self.height = posY+self.barwidth+barSpacer;
        painter.setPen(QtCore.Qt.black);      
        painter.setBrush(QtCore.Qt.NoBrush);
        painter.drawLine(legendX,legendY,legendX,legendY+self.height);
        self.width = lagendShift+maxBarHeight;


class Line(QtGui.QGraphicsItem):
    def __init__(self, x, y, color, parent=None, scene=None):
        QtGui.QGraphicsItem.__init__(self, parent, scene)
        self.x=x
        self.y=y        
        self.highlighted=False;
        self.setAcceptsHoverEvents(True);
        self.line = QtGui.QPolygonF([QtCore.QPointF(x_, y_) for x_, y_ in izip(x, y)])
        self.fixEnds()
        #self.path=QtGui.QPainterPath(self.boundingRect())
        self.color=color
        self.pen = QtGui.QPen(self.color)
        self.brush = QtGui.QBrush(self.color)
    
    
    def setHighlighted(self, boolean):
        self.highlighted=boolean
    
    
    def boundingRect(self):
        return self.line.boundingRect()


    def paint(self, painter, options, widget=None):
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        if self.highlighted: #or self.isSelected(): 
            c = QtGui.QColor(self.color)
            c.setAlphaF(.75) #only the contour
            painter.setBrush(QtGui.QBrush(c))
            pen=QtGui.QPen(c.darker());
            pen.setWidth(self.pen.width()+.8)
            painter.setPen(pen)
        else:
           painter.setOpacity(.5)
        painter.drawPolygon(self.line)  


    def shape(self):
        path=QtGui.QPainterPath()
        path.addPolygon(self.line)
        return path

#===============================================================================
# napporte pas grand chose les hoverenterev
#===============================================================================
#    def hoverEnterEvent(self, event ):
#        QtGui.QGraphicsItem.hoverEnterEvent(self, event)
#        #self.highlighted=True
#        self.setZValue(self.zValue()+1000)
#        self.scene().update()
#
#
#    def hoverLeaveEvent (self, event):
#        QtGui.QGraphicsItem.hoverLeaveEvent(self, event)
#        #self.highlighted=False
#        self.setZValue(self.zValue()-1000)
#        self.scene().update()
    
#    def mousePressEvent(self, ev):
#        if ev.button() == QtCore.Qt.LeftButton:
#           self.highlighted= not(self.highlighted)
          
    def getData(self):
        return self.x, self.y
    
    def updateData(self, y, x):
        self.y=y
        self.x=x
        self.line=QtGui.QPolygonF([QtCore.QPointF(x_, y_) for x_, y_ in izip(self.x, self.y)])
        #self.sceneObj.update()

    def fixEnds(self): 
        if(len(self.line)< 2):
            return
        if not self.scene(): 
            return
        p1 = self.line[0]
        p2 = self.line[len(self.line)-1]
        a=QtCore.QPointF( p1.x() ,0)
        b=QtCore.QPointF( p2.x(), 0)
        #self.line.__setitem__(0,a);
        self.line.insert(0,a)        
        self.line.append(b)

    def getRange(self, ax, frac=1.):
        print "getRange called"
        x, y = self.getData()
        if x is None or len(x) == 0:
            return (0, 1)
        if ax == 0:
            d = x
        elif ax == 1:
            d = y
        if frac >= 1.:
            return (min(d), max(d))
        elif frac <= 0.0:
            raise Exception("Value for parameter 'frac' must be > 0. (got %s)" % str(frac))
        else:
            return (scipy.stats.scoreatpercentile(d, 50 - (frac * 50)), 
                    scipy.stats.scoreatpercentile(d, 50 + (frac * 50)))

class SpectrumItem(QtGui.QGraphicsItem):
    
    def __init__(self, spectrum, centroid=True, parent=None, scene=None, **kw):
        QtGui.QGraphicsItem.__init__(self, parent, scene)
        self.spectrum=spectrum
        self.x=self.spectrum.x_data
        self.y=self.spectrum.y_data
        self.color=kw.get('color', QtCore.Qt.blue)
        self.centroid=centroid
        self.highlighted = False
        
        if not self.centroid:
            self.line=QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in zip(self.x, self.y)])
        
        #get the baseline...
        #from core.MetObjects import MSAbstractTypes
        #self.baseline=MSAbstractTypes.computeBaseLine(self.y, quantile=65, order=2, smooth=True)
    
    
    def setHighlighted(self, b):
        self.highlighted = b
    
    def boundingRect(self):
        """
        TODO: resolve that bug
        
        """
        if self.centroid:
            #minX, maxX=min(self.x), max(self.x)
            #minY, maxY=min(self.y), max(self.y)
            return QtCore.QRectF(QtCore.QPointF(-1e9, 1e9), QtCore.QPointF(1e9, -1e9))
#            if all([y_ <= 0 for y_ in self.y]):
#                return  QtCore.QRectF(minX, minY, maxX-minX, minY)  
#            else:
#                return  QtCore.QRectF(minX, maxY, maxX-minX, maxY)
        else:
            return self.line.boundingRect()
   
    
    def paint(self, painter, options, widget=None):
        if self.centroid:        
            from itertools import izip
            if self.spectrum.sample is not None:
                bluePen=QtGui.QPen(QtGui.QColor.fromRgbF(*(self.spectrum.sample.color+(1.,))))
            else:
                bluePen=QtGui.QPen(QtCore.Qt.blue)
            bluePen.setWidth(0.5)
            #bluePen.setWidthF(.1)
            if self.highlighted:
                #bluePen.setWidthF(bluePen.widthF()+1.)
                c = bluePen.color().darker()
                c.setAlphaF(0.5)
                bluePen.setColor(c)
            #redPen=QtGui.QPen(QtCore.Qt.red)
            #redPen.setWidthF(.05)#TODO: resolve that screening bug            
            painter.setPen(bluePen)
            #c=0
            for x, y in izip(self.x, self.y):
                #if self.baseline[c] > y:
                #    painter.setPen(redPen)
                #else:
                painter.drawLine(x, 0, x, y)
                #c+=1
            #painter.setPen(redPen)
            #painter.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in zip(self.x, self.baseline)]))
        else:
            painter.setPen(QtGui.QPen(self.color))
            painter.drawPolyline(self.line)
    
    def getData(self):
        return (self.x, self.y)
    
    def updateData(self, y, x):
        self.y=y;self.x=x
        if not self.centroid:
            self.line=QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in zip(self.x, self.y)])
        self.scene().update()
            
    def getRange(self, ax, frac=1.):
        if self.x is None or len(self.x) == 0:
            return (0, 1)
        if ax == 0:
            d = self.x
        elif ax == 1:
            d = self.y
        if frac >= 1.:
            return (min(d), max(d))
        elif frac <= 0.0:
            raise Exception("Value for parameter 'frac' must be > 0. (got %s)" % str(frac))
        else:
            return (scipy.stats.scoreatpercentile(d, 50 - (frac * 50)), 
                    scipy.stats.scoreatpercentile(d, 50 + (frac * 50)))



class PeakArrowItem(ArrowItem):
    """
    Item for xcms peak
    
    """
    def __init__(self, peak, **k):
        ArrowItem.__init__(self, **k)
        self.setAcceptsHoverEvents(True)
        self.peak = peak
        self.highlighted=False    
        #tooltip
        string="<p><b>Peak informations</b></p>"
        string+="<p><b> RT:</b>"+str(self.peak.rt)+"</p>"
        string+="<p><b> RTmin:</b>"+str(self.peak.rtmin)+'</p>'
        string+="<p><b> RTmax:</b>"+str(self.peak.rtmax)+'</p>'
        string+="<p><b> Area:</b>"+str(self.peak.area)+'</p>'
        string+="<p><b> Height:</b>"+str(self.peak.height)+'</p>'
        string+="<p><b> SN:</b>"+str(self.peak.sn)+'</p>'
        string+="<p><b> Peak Status:</b>"
        string+="good" if self.peak.isGood else "bad"+"</p>"
        self.setToolTip(string)

        
    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.RightButton:
            e.ignore()
        self.highlighted=not self.highlighted
        QtGui.QApplication.instance().emit(QtCore.SIGNAL('highlightRequested'), self.highlighted)
    
    def mouseDoubleClickEvent(self, e):
        pkl=QtGui.QApplication.instance().model.peakGroup(self.peak)
        t=""
        t+="\t".join([p.sample.shortName() for p in pkl])
        t+='\n'
        t+='\t'.join([str(p.rt) for p in pkl])+'\n'
        t+='\t'.join([str(p.rtmin) for p in pkl])+'\n'
        t+='\t'.join([str(p.rtmax) for p in pkl])+'\n'
        t+='\t'.join([str(p.area) for p in pkl])+'\n'
        t+='\t'.join([str(p.height) for p in pkl])+'\n'
        QtGui.QApplication.instance().clipboard().setText(t)
        QtGui.QApplication.instance().view.showInformationMessage("Infomation", 
                                                                  'Peak@%s copied to clipboard'%str(self.peak))
    def hoverEnterEvent(self, e):
        pkl=QtGui.QApplication.instance().model.peakGroup(self.peak.mass(), self.peak.rt) 
        QtGui.QApplication.instance().emit(QtCore.SIGNAL('updateBarPlot'), pkl)

    def paint(self, p, *args):
        if self.highlighted:
            p.setBrush(QtGui.QBrush(self.opts['brush'].darker()))
        ArrowItem.paint(self, p, *args)
    
    def boundingRect(self):
        return self.polygon().boundingRect()
        




class PeakIndicator(QtGui.QGraphicsObject):
    
    pixmap=os.path.normcase('gui/icons/1downarrow.png')
    flag=os.path.normcase('gui/icons/flag_green.png')
    
    def __init__(self, peak, icon='', parent=None):    
        QtGui.QGraphicsObject.__init__(self, parent)
        self.setAcceptsHoverEvents(True)
        self.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations)
        self.peak=peak
        self.pixmapItem=QtGui.QGraphicsPixmapItem(QtGui.QPixmap(self.flag if icon \
                                                                == 'flags'else self.pixmap))

        self.highlighted=False
        
        #tooltip
        string="<p><b>Peak informations</b></p>"
        string+="<p><b> RT:</b>"+str(self.peak.rt)+"</p>"
        string+="<p><b> RTmin:</b>"+str(self.peak.rtmin)+'</p>'
        string+="<p><b> RTmax:</b>"+str(self.peak.rtmax)+'</p>'
        string+="<p><b> Area:</b>"+str(self.peak.area)+'</p>'
        string+="<p><b> Height:</b>"+str(self.peak.height)+'</p>'
        string+="<p><b> SN:</b>"+str(self.peak.sn)+'</p>'
        string+="<p><b> Peak Status:</b>"
        string+="good" if self.peak.isGood else "bad"+"</p>"
        self.setToolTip(string)
    
    def boundingRect(self):
        """must be overriden"""
        return self.pixmapItem.boundingRect()
    
    
    def paint(self, painter, options, widget=None):
        """must be overriden"""
        self.pixmapItem.paint(painter, options, widget)
        
    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.RightButton:
            e.ignore()
            
        self.highlighted=not self.highlighted
        self.emit(QtCore.SIGNAL('highlightRequested'), self.highlighted)
    
    def mouseDoubleClickEvent(self, e):
        pkl=QtGui.QApplication.instance().model.peakGroup(self.peak)
        t=""
        t+="\t".join([p.sample.shortName() for p in pkl])
        t+='\n'
        t+='\t'.join([str(p.rt) for p in pkl])+'\n'
        t+='\t'.join([str(p.rtmin) for p in pkl])+'\n'
        t+='\t'.join([str(p.rtmax) for p in pkl])+'\n'
        t+='\t'.join([str(p.area) for p in pkl])+'\n'
        t+='\t'.join([str(p.height) for p in pkl])+'\n'
        QtGui.QApplication.instance().clipboard().setText(t)
        QtGui.QApplication.instance().view.showInformationMessage("Infomation", 
                                                                  'Peak@%s copied to clipboard'%str(self.peak))
    def hoverEnterEvent(self, e):
        pkl=QtGui.QApplication.instance().model.nonXCMSPeakGroup(self.peak.mass(), self.peak.rt)
        self.emit(QtCore.SIGNAL('updateBarPlot'), pkl)


        

class TinyPlot(QtGui.QGraphicsItem):
    
    def __init__(self, data=None, title=None, parent=None, scene=None):
        QtGui.QGraphicsItem.__init__(self, parent, scene)
        #self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.data=data
        self.width=100.
        self.height= -100.

    
    def boundingRect(self):
        return QtCore.QRectF(0,0,self.width,self.height)
    
    
    def paint(self, painter, options, widget=None):
        painter.setPen(QtCore.Qt.black)
        painter.drawLine(QtCore.QPointF(0.,0.), QtCore.QPointF(self.width, 0.))
        painter.drawLine(QtCore.QPointF(0.,0.), QtCore.QPointF(0., self.height))
        d=self.mapToPlot(self.data)
        for el in d:
            #if el is None:
            #    continue
            #painter.setPen(QtGui.QColor.fromRgbF(*(el.sample.color+(1.,))))
            painter.setPen(QtCore.Qt.red)
            painter.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in zip(el.x_data, el.y_data)]))
        painter.setPen(QtCore.Qt.black)
        painter.drawText(QtCore.QPointF(50., -110.), "bonsoir paris")
        
    
    def mapToPlot(self, data):
        mappedData=[]
        for d in data:
            a=A(d.x_data, (d.y_data* -100) /d.y_data.max())
            mappedData.append(a)
        return mappedData



if __name__ == '__main__':
    class A(object):
        def __init__(self, x, y):
            self.x_data=x;self.y_data =y
    
    from PyQt4 import QtOpenGL
    import sys
    app=QtGui.QApplication(sys.argv)
    
    scene=QtGui.QGraphicsScene()
    scene.setItemIndexMethod(QtGui.QGraphicsScene.BspTreeIndex);
    #widget=QtGui.QGraphicsWidget()
    #layout=QtGui.QGraphicsGridLayout()
    
    x=np.linspace(0,100,100)
    y=np.linspace(0,100,100)
    a=A(x, y)
    t1=TinyPlot([a])
    t2=TinyPlot([a])
    t3=TinyPlot([a])
    #t1.scale(1,-1)
    #t2.scale(1,-1)
    #t3.scale(1,-1)
    scene.addItem(t1)
    scene.addItem(t2)
    scene.addItem(t3)
    t1.setPos(QtCore.QPointF(10, 20))
    t2.setPos(QtCore.QPointF(t1.width+10, 0))
    t3.setPos(QtCore.QPointF(t1.width*2+20,0))
    #layout.addItem(t1, 0,0)
    #layout.addItem(t2, 0,1)
    #widget.setLayout(layout)
    
    #scene.addItem(widget)
    
    view=QtGui.QGraphicsView()
    view.setViewport(QtOpenGL.QGLWidget())
    view.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop);
    view.setScene(scene)
    #view.fitInView(t1, mode=QtCore.Qt.IgnoreAspectRatio)
    view.show()
    sys.exit(app.exec_())
    
        
        