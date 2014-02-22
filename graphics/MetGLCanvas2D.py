#!usr/bin/python

__verion__ = '$Revision1'
__author__ =('marco', 'cram@hotmail.fr')

"""Soon be deprecated, will be replaced by mayavi2 widget
DEPRECATED MODULE
"""

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from PyQt4.QtGui import (QToolTip, QFont, QApplication, QCursor, QMatrix, QSplitter, QVBoxLayout,
                        QHBoxLayout, QPushButton, QTableView, QComboBox, QWidget)
from PyQt4.QtCore import Qt, QPoint, QPointF
from PyQt4.QtOpenGL import QGLWidget, QGLFormat, QGL, QGLShader, QGLShaderProgram
from numpy import array, log10
#from utils import MetHelperFunctions



class MSGLCanvas2D(QGLWidget):
    """
    Canvas GL plotting in 2 dimensions
    """
    
    
    MAX = 100.
    
    
    corner_=100.0
    zoom_= 1.5
    xrot_=220
    yrot_ = 220
    trans_x_ =0.0
    trans_y_ = 0.0
    
    
    def __init__(self, data, parent=None, **kw):
        """
        Constructor, initialization
        """
        
        QGLWidget.__init__(self, parent)
        self.setFormat(QGLFormat(QGL.SampleBuffers))
        self.setMinimumSize(500,300)#300
        self.setMouseTracking(True) 
        self.setFocusPolicy(Qt.StrongFocus)
        
        self.data=data
        vertexes=[]
        colors=[]
        from utils.misc import IceAndFire
        maxY=max(map(max, [log10(el.y_data) for el in data]))
        maxX=max(map(max, [el.x_data for el in data]))
        rtmax=max([z.rtmin for z in data])
        for el in data:
            for i, x in enumerate(el.x_data):
                c=IceAndFire.getQColor(log10(el.y_data[i])/maxY)
                colors.append(c)
                vertexes.append([(x*2*self.corner_)/maxX, (el.rt*2*self.corner_)/rtmax])
        from OpenGL.arrays.vbo import VBO
        
        self.vertexes= VBO(array(vertexes,'f'))
        self.colors=VBO(array(colors,'f'))
        
        self.mode = "None" # "ZOOMING", "PANNING", "NONE"
        self.lastpos = QPoint()
        
        self.counter_trans_x = 0
        self.counter_trans_y = 0

        
        self.defaultColors = {'ticks':(0.,0.,0.,0.),
                              'axes':(0.,0.,0.,0.),
                              'curves':(0.,0.,1.,0.),
                              'backgroundColor':(1.,1.,1.,1.)
                              }
     
        #self.axes=self.drawAxes()
        self.transformationMatrix = self.setupTransformationMatrix(self.width(), 
                                                                   self.height())
    
    
 
                                 
        
    def setupTransformationMatrix(self,w, h):
        """
        use a matrix to translate in the gl landmark
        """
        
        m = QMatrix()
        m.translate(-w/2, h/2)
        m.scale(300./w, 300./h)
        print w, h, w/300., 1-((h/300)-1)
        #m.scale((self.width()*100)/300, -(self.height()*100)/300)
        #self.currentSize.x = w
        #self.currentSize.y = h        
        return m


    
    def inGLCoordinate(self, point):
        return self.transformationMatrix.map(point)        
        
    
    
    def resizeGL(self, w, h):
        """
        called when window is being resized
        """
    
        glViewport(0,0, w, h)    
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(-self.corner_*self.zoom_, 
                   self.corner_*self.zoom_, 
                   -self.corner_*self.zoom_, 
                   self.corner_*self.zoom_)

        #self.transformationMatrix = self.setupTransformationMatrix(w, h)
        
        glMatrixMode(GL_MODELVIEW)
    
    
    def initializeGL(self):
        """needed, initialize GL parameters"""
        
        #glClearColor(1.,1.,1.,1.)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_POINT_SMOOTH)
        glHint (GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLoadIdentity() #model view by default
        
#        self.grid_lines = self.drawGridLines()
#        self.ticks =self.drawAxisTick()
#        self.axes = self.drawAxes()

    
    
    def paintGL(self):
        """Draw the scene, needed, called each time glDraw"""
        
        glClear(GL_COLOR_BUFFER_BIT)
        glTranslated(self.trans_x_, self.trans_y_, 0.)
        #addition
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(-self.corner_*self.zoom_, 
                    self.corner_*self.zoom_,    
                    -self.corner_*self.zoom_, 
                    self.corner_*self.zoom_)
        glMatrixMode(GL_MODELVIEW)
        #end addition
        #glCallList(self.grid_lines)
        #glCallList(self.ticks)
        #glCallList(self.axes)
        glLineWidth(30.0)
        self.scatterPlot()
#        if self.flags == "chrom":
#            self.drawAxisLegend("retention time[s]", "intensity[%]")
#            glCallList(self.lines)
#        elif self.flags == "spectrum":
#            self.drawAxisLegend("m/z", "intensity")
        
    
    
    
    def drawAxes(self, width=2., colour=(0.,0.,0.)):
        """
        Draw Axes 
        """
        #width must be a float
        axes = glGenLists(1)
        glNewList(axes, GL_COMPILE)
        glLineWidth(width)
        glColor(colour[0],colour[1],colour[2])
        glBegin(GL_LINES)
        #x_achse
        glVertex2d(-self.corner_, -self.corner_)
        glVertex2d( self.corner_, -self.corner_)
        #y-achse
        glVertex2d(-self.corner_, -self.corner_)
        glVertex2d( -self.corner_, self.corner_)
        glEnd()
        glEndList()
        return axes
        
    
    def drawLegends(self, pos):
        """
        draw legend at the specified position
        """
        pass
    
    
    
   
        
    
    
    def drawAxisLegend(self, x_label, y_label):
        """
        Draw Axis Legend
        """
        font =QFont("Typewriter")                        
        #RT axis legend
        font.setPixelSize(12)
        self.renderText(self.corner_, -self.corner_-20.0, 0., x_label)# font
        self.renderText(-self.corner_-20.0, self.corner_, 0., y_label, font)
    
    
    
    
            
            
    def resetTranslations(self):            
        """
        reset the different translation to 0
        """
        self.trans_x_ =0.
        self.trans_y_ =0.
        self.counter_trans_x=0.
        self.counter_trans_y=0.
    
    
    
    def normalizeAngle(self,angle):
            while (angle < 0):
                    angle += 360 * 16
            while (angle > 360 * 16):
                    angle -= 360 * 16


########DRAWING METHODS##################################################

    def drawLine(self, point_, point):
        glBegin(GL_LINES)
        glVertex2d(point_.x(), point_.y())
        glVertex2d(point.x(), point.y())
        glEnd()
    
    def drawRect(self, p_1, p_2, p_3=None, p_4 = None):
        pass
    
    def drawOnePoint(self, point, colour= Qt.yellow):
        pass
    
    def scatterPlot(self):
        """ Draw Data (x, y)"""
        if self.vertexes is not None and self.colors is not None:
            self.vertexes.bind()
            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointerf(self.vertexes)
            self.colors.bind()                  
            glEnableClientState(GL_COLOR_ARRAY)
            glColorPointerf(self.colors)
            glDrawArrays(GL_LINES, 0, len(self.vertexes))
            self.vertexes.unbind()
            self.colors.unbind()
            #self.textures.unbind()
            glDisableClientState(GL_VERTEX_ARRAY)
            glDisableClientState(GL_COLOR_ARRAY)
    
    def spectrumPlot(self, points):
        pass
    
    def histogramPlot(self, points, bin = 5.):
        pass
        
    def barPlot(points, width =2.):pass

    


########MOUSE AND KEYBOARDS EVENTS###########################################################################
    
    
    def wheelEvent(self, event):
        if event.delta() >0:
            self.zoom_ -= .05    
        else:
            self.zoom_ += .05
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(-self.corner_*self.zoom_, 
                   self.corner_*self.zoom_, 
                   -self.corner_*self.zoom_, 
                   self.corner_*self.zoom_)
        self.updateGL()
        glMatrixMode(GL_MODELVIEW)
        event.accept()
            
    
    
    
    def keyPressEvent(self,  event):
        if event.key() == Qt.Key_Plus:
            self.zoom_ -= .1
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluOrtho2D(-self.corner_*self.zoom_, 
                       self.corner_*self.zoom_,    
                       -self.corner_*self.zoom_, 
                       self.corner_*self.zoom_)
            glMatrixMode(GL_MODELVIEW)

        if event.key() == Qt.Key_Minus:
                self.zoom_ += .1
                glMatrixMode(GL_PROJECTION) #// You had GL_MODELVIEW
                glLoadIdentity()
                gluOrtho2D(-self.corner_*self.zoom_, self.corner_*self.zoom_, -self.corner_*self.zoom_, self.corner_*self.zoom_)
                glMatrixMode(GL_MODELVIEW)
                
        if event.key() == Qt.Key_Up:
                self.trans_y_ += 2
                self.counter_trans_y +=2
                
        if event.key() == Qt.Key_Down:
                self.trans_y_ -=2
                self.counter_trans_y -=2
                
        if event.key() == Qt.Key_Left:
                self.trans_x_ -=2
                self.counter_trans_x -=2
                
        if event.key() == Qt.Key_Right:
                self.trans_x_ +=2
                self.counter_trans_x +=2
        
        
        if event.key() == Qt.Key_Z:
            self.mode= "ZOOMING"
            if self.counter_trans_x < 0 and self.counter_trans_y < 0:
                while self.counter_trans_x < 0 and self.counter_trans_y < 0:
                    self.trans_x_ = self.counter_trans_x
                    self.trans_y_ = self.counter_trans_y                    
                    self.updateGL()
                    self.counter_trans_x += 1
                    self.counter_trans_y += 1
                    
            if self.counter_trans_x > 0 and self.counter_trans_y < 0:
                while self.counter_trans_x < 0 and self.counter_trans_y < 0:
                    self.trans_x_ = self.counter_trans_x
                    self.trans_y_ = self.counter_trans_y                    
                    self.updateGL()
                    self.counter_trans_x -= 1
                    self.counter_trans_y += 1
            
            if self.counter_trans_x < 0 and self.counter_trans_y > 0:
                while self.counter_trans_x < 0 and self.counter_trans_y < 0:
                    self.trans_x_ = self.counter_trans_x
                    self.trans_y_ = self.counter_trans_y                    
                    self.updateGL()
                    self.counter_trans_x += 1
                    self.counter_trans_y -= 1
    
            if self.counter_trans_x < 0 and self.counter_trans_y > 0:
                while self.counter_trans_x < 0 and self.counter_trans_y < 0:
                    self.trans_x_ = self.counter_trans_x
                    self.trans_y_ = self.counter_trans_y                    
                    self.updateGL()
                    self.counter_trans_x -= 1
                    self.counter_trans_y -= 1
                    
            if self.zoom_ != 1.5:    
                self.zoom = 1.5
                #self.updateGL()
        self.updateGL()
        self.resetTranslations()    
        
    
    def mousePressEvent(self, event):
        if self.mode == "ZOOMING":
            self.mode = "None"
            self.computeSelection()
        else: 
            self.lastpos = QPoint(event.pos())
            self.setCursor(QCursor(Qt.ClosedHandCursor))
        
        
        #if event.buttons() ==  Qt.RightButton:
        #    self.mode = "PANNING"
            
    def computeSelection(self):
        print "selected"

    
    
    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastpos.x()
        dy = event.y() - self.lastpos.y()
        
        if self.mode == "ZOOMING":
            font = QFont("Typewriter")
            self.renderText(-self.corner_ -30.0, self.corner_, 0., "ZOOMING MODE ACTIVATED", font)
            self.updateGL()
            glColor(0., 0., 1., .5)
            XMAX = 900.; XMIN = 180.
            pointer_x = (self.lastpos.x()*200.)/XMAX
            norm_dx = (dx*200.)/XMAX
            """
            if pointer_x > 100. or pointer_x < 100. \
                or norm_dx >100. or norm_dx<-100.:
                event.ignore()
            """

            
            glBegin(GL_QUADS)
            glVertex2d(pointer_x, -100.)
            glVertex2d(pointer_x+ norm_dx, -100.)
            glVertex2d(pointer_x+ norm_dx, 100.)
            glVertex2d(pointer_x, 100.)
            glEnd()
            
            self.updateGL()#update for seeing the rectangle
            
        mapping = self.mapFromGlobal
        cursorPos = self.inGLCoordinate(mapping(self.cursor().pos()))        
        QToolTip.showText(self.cursor().pos(),
                          "x:"+str(cursorPos.x())+ \
                          ", y:"+str(cursorPos.y())
                          )

        if self.mode == "None":      
            if event.buttons()== Qt.LeftButton:
                self.trans_y_ -= dy/5
                self.counter_trans_y -= dy/5
                self.trans_x_ += dx/5
                self.counter_trans_x += dx/5
            self.lastpos = QPoint(event.pos())
            self.glDraw()
            self.resetTranslations()        

    
    def mouseReleaseEvent(self, event):
        self.setCursor(QCursor(Qt.ArrowCursor))




"""
import visvis as vv
from visvis import Point, Pointset


class MSVisVisWidget(QWidget):
    
    def __init__(self, data, **kw):
        try:
            QWidget.__init__(self, kw['parent'])        
        except KeyError:
            QWidget.__init__(self)
        self.setMinimumSize(500,300)
        print type(data[0]), len(data[0].x_data)
        self.data = data
        
        try:
            self.flags = kw['flags']
            self.model =kw['model']
        except KeyError:
            self.flags ='chroma'
            
        self.figure = vv.backends.backend_qt4.Figure(self)  
        #self.figure = vv.backends.backend_qt4.Figure(self)        
        #self.addWidget(self.figure._widget)
        
        #keep a reference to the axis        
        
        #self.axesBinding()
        
        if self.flags == 'chroma' or self.flags=='peak':
            self.spectra = []
        
        self._active = None      
        self._lastpos =None
        #to store data line        
        self._lines =[]
        
        #finally plot
        self.plot()
    
        layout=QVBoxLayout(self)
        layout.addWidget(self.figure._widget)
        if self.flags == 'peak':
            lst_combo = ["associated spectrum", "3D view"]
            self.table = QTableView(self)
            self.table.setModel(self.model)
            self.table.resizeRowsToContents()
            self.table.resizeColumnsToContents()
            self.table.setMaximumHeight(50)
            layout.addWidget(self.table)
            hl =  QHBoxLayout()
            self.button= QPushButton("plot")
            self.combobox =QComboBox(self)
            for el in lst_combo:
                self.combobox.addItem(el)
            hl.addWidget(self.combobox)
            hl.addWidget(self.button)
            layout.addLayout(hl)
        h = QHBoxLayout()
        self.prec = QPushButton("<", self)
        self.suc = QPushButton(">", self)
        h.addWidget(self.prec)
        h.addStretch(200)
        h.addWidget(self.suc)
        layout.addLayout(h)
        

    def plot(self, **kwargs):
        self.axes = vv.gca()
        self.axes.axis.showGrid = True
        self.axes.cameraType = '2d'
        for element in self.data:
            line = vv.plot(element.x_data, element.y_data, lw=1.5, ms='.', mw=0.5)
            self.lineBinding(line)
        
            if self.flags=='chroma' or self.flags=='peak':
                legend = "chrom@%s"%str(element.transition)
                x_axis = 'retention time'
            elif self.flags=='spectra':
               x_axis = 'm/z'
               legend = "spec@%s"%str(element.rt_min)
            line.title = legend
            vv.legend(legend)
            vv.xlabel(x_axis)
            vv.ylabel('relative intensity')
            self._lines.append(line)
       
    
    def lineBinding(self, line, **kwargs):
        line.eventEnter.Bind(self.highLightOn)
        line.eventLeave.Bind(self.highLightOff)
        line.hitTest = True
    
    
    def axesBinding(self):
        self.axes.eventMouseDown.Bind(self.picker)
        self.axes.eventMotion.Bind(self.onMotion)
        self.axes.eventMouseDown.Bind(self.onDown)
        self.axes.eventMouseUp.Bind(self.onUp)
        
        
    def picker(self, event):
        print 'screen: %i, %i   world: %2.2f, %2.2f' % (event.x, event.y, event.x2d, event.y2d)
    
    
    
    def onMotion(self, event):
        if self._lastpos is not None:
            dx = event.x2d - self._lastpos[0]
            line = vv.plot(array([self._lastpos[0], dx]), array([self._lastpos[1], self._lastpos[1]]))
            self._lines.append(line)            
            self.axes.Draw(fast=True)
            #return True
        QToolTip.showText(QCursor.pos(), "x:"+str(int(event.x2d))+\
                            ", y:"+str(int(event.y2d)))
        self.axes.Draw(fast=True)
        return True
    
    def onUp(self, event):
        self._lastpos=None
        self._lines[-1].Destroy()
        self.axes.Draw(fast=True)
    
    def onDown(self, event):
        if self._active:
            if event.button == 2:            
                # Store location
                self._lastpos = (event.x2d, event.y2d)
            # Prevent dragging by indicating the event needs no further handling
    
    
    def onKey(self, event):
        if event.text.lower()== 's':
            self._active = True
        
    
    def highLightOn(self, event):
        event.owner.lc='r'
        event.owner.Draw(fast=True)
        
    
    def highLightOff(self, event):
        event.owner.lc='b'
        event.owner.Draw(fast=True)
    
"""










