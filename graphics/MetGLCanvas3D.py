#-*-coding:utf8-*-

import math

from OpenGL.GL import *
#from OpenGL.GLU import *
#from OpenGL.GLUT import *
#from OpenGL.GL.shaders import *
from PyQt4.QtOpenGL import QGLWidget, QGL, QGLFormat
from PyQt4.QtGui import (QFont, QCursor, QSplitter, QWidget, QImage, QGridLayout, QPixmap, QLabel, QBrush,
                         QPainter, QLinearGradient, QColor)
from PyQt4.QtCore import (Qt, QPoint, QPointF)
from numpy import array
from utils.decorators import check



class MSGLCanvas3D(QGLWidget):
    """Canvas GL plotting in 3 dimensions spectra"""
    
        
    corner=100.0
    near=0.0
    far=600.0
    zoom= 1.5
    xrot=220
    yrot = 220
    zrot=0
    trans_x =0.0
    trans_y = 0.0    

    
    def __init__(self, vertexes, colors, parent=None, **kw):#vertexes, colors, texturePath='graphics/Texture-Example.jpg', parent=None):#spl, peak=None, parent=None):
        """
        Constructor, initialization
        kw:
            -texturePath:pathway to the file to text
            -textures: coord textures to apply
            -parent:the parent widget
        """
        QGLWidget.__init__(self, parent)
        self.setFormat(QGLFormat(QGL.SampleBuffers))
        self.setMinimumSize(500,300)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        
#        if not 'texturePath'in kw.keys() and not 'textures' in kw.keys():
#            pass
#            #print ('Could not apply texture, no coordinates')
#        else:
#            try:
#                self._imageID = self.loadImage(kw.get('texturePath'))
#                self.textures = textures
#            except OSError:
#                print ('Could not apply texture, no coordinates')
            
        
        self.vertexes = vertexes
        self.colors = colors

        #self.axes=None
        self.zoom_mode = False
        self.pan_mode = True
        #self.axes = self.makeAxes()

        self.parameters={'axes_color':'b',
                        'axes_line_width':3.,
                        'draw_line_width':1.,
                        'colormap':True,
                        'fish_eye':False,
                        'cell_shading':False}
        self.lastpos = QPoint()

       
    
    def loadImage(self, imageName):		
        im = open(imageName)
        try:
            ix, iy, image = im.size[0], im.size[1], im.tostring("raw", "RGBA", 0, -1)
        except SystemError:
            ix, iy, image = im.size[0], im.size[1], im.tostring("raw", "RGBX", 0, -1)
        ID = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, ID)
        glPixelStorei(GL_UNPACK_ALIGNMENT,1)
        glTexImage2D(GL_TEXTURE_2D, 0, 3, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
        return ID
    
    
    def setupTexture(self):
        glEnable(GL_TEXTURE_2D)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
        glBindTexture(GL_TEXTURE_2D, self.imageID)
        
    
    
    def texturesCalc(self):
        from OpenGL.arrays.vbo import VBO
        basis = [[0.,0.], [0.,1.]]
        hola =[]        
        
        length = len(self.vertexes)
        for i in range(length/2):
            hola+=basis
        return VBO(array(hola))
    
    
    def recalcVertexesAndColors(self, colormap, **kwargs):
        pass
    
    def resizeGL(self, w, h):
        """called when window is being resized"""
        glViewport(0,0, w, h)     
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-self.corner*self.zoom, 
                self.corner*self.zoom, 
                -self.corner*self.zoom, 
                self.corner*self.zoom , 
                self.near, 
                self.far)
        #gluPerspective(70,w/h, 1,1000)
        glMatrixMode(GL_MODELVIEW)
        
    
    def initializeGL(self):
        """opengl options"""
        #glClearColor(1., 1., 1., 1.)
        #glClearColor(0.,0.,0.)
        glEnable(GL_DEPTH_TEST)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        #glEnable(GL_POINT_SMOOTH)
        #glHint (GL_LINE_SMOOTH_HINT, GL_NICEST)#
        #glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)

        #glCullFace(GL_BACK)
        #glEnable(GL_LIGHTING)
        #glLightfv(GL_LIGHT0, GL_DIFFUSE,(0.8, 0.8, 0.8, 1))
        #glEnable(GL_LIGHT0)
        #glEnable(GL_COLOR_MATERIAL)
        #glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
        #self.shader = compileProgram(vertex_shader, frag_shader)#vertex_shader)#shader
        #self.drawAxisLegend()

    
   
    
    
    
    
    def paintGL(self):
        """needed, called each time glDraw"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslated(0.0, 0.0,-3.0*self.corner)
        glRotated(self.xrot / 16.0, 1.0, 0.0, 0.0)
        glRotated(self.yrot / 16.0, 0.0, 1.0, 0.0)
        glRotated(self.zrot/16.0, 0.0, 0.0, 1.0)
        glTranslated(self.trans_x, self.trans_y, 3.0*self.corner)
        #testing
        #glEnable(GL_DEPTH_TEST)
        #glEnable(GL_BLEND)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
      
        #self.setupTexture()
        #self.textures = self.texturesCalc()
        self.drawScene()
        #if self.zoom_mode:
        #    self.drawQuad()
        
    
    def renderTextModes(self):
        self.renderText(10, 10, 'mode:%s'%"zoom" if self.zoom_mode else 'mode:%s'%"pan", font=QFont())
        self.renderText(10, 20, 'selection mode:%s'%str(False), font=QFont())
        
    def drawScene(self):
        #
        self.renderTextModes()
        glLineWidth(1.)
        #glUseProgram(self.shader)
        if self.vertexes is not None and self.colors is not None:
            self.vertexes.bind()
            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointerf(self.vertexes)
            self.colors.bind()                  
            glEnableClientState(GL_COLOR_ARRAY)
            glColorPointerf(self.colors)
            """        
            self.textures.bind()
            glEnableClientState(GL_TEXTURE_COORD_ARRAY)
            glTexCoordPointerf(self.textures)
            """
            glDrawArrays(GL_LINES, 0, len(self.vertexes))
            
            self.vertexes.unbind()
            self.colors.unbind()
            #self.textures.unbind()
            glDisableClientState(GL_VERTEX_ARRAY)
            glDisableClientState(GL_COLOR_ARRAY)
            #glDisableClientState(GL_TEXTURE_COORD_ARRAY)
            #glUseProgram(0)
        #glUseProgram(0)
        #if hasattr(self, 'axes'):
        #glCallList(self.axes)
        #glCallList(self.surface)
        #self.drawAxisLegend()

    
    
    def makeAxes(self):
        """Draw Axes """
        glLineWidth(2.0)
        glColor(0.,0.,1.)
        lspectr = glGenLists(1)
        glNewList(lspectr,GL_COMPILE)
        glBegin(GL_LINES)
        #glEnable(GL_LINE_STIPPLE)
        #glLineStipple(1, 1)
        glVertex3d(self.corner, -self.corner, -self.near-2*self.corner)
        glVertex3d(self.corner, self.corner, -self.near-2*self.corner)

        glVertex3d(self.corner, -self.corner, -self.far+2*self.corner)
        glVertex3d(self.corner, +self.corner, -self.far+2*self.corner)
        

        glVertex3d(-self.corner, -self.corner, -self.far+2*self.corner)
        glVertex3d(-self.corner, +self.corner, -self.far+2*self.corner)
        
        glVertex3d(-self.corner, +self.corner, -self.far+2*self.corner)
        glVertex3d(self.corner, +self.corner, -self.far+2*self.corner)
        
        
        glVertex3d(+self.corner, +self.corner, -self.far+2*self.corner)
        glVertex3d(+self.corner, +self.corner, -self.near-2*self.corner)
        #glDisable(GL_LINE_STIPPLE)
        
        glVertex3d(+self.corner, -self.corner, -self.far+2*self.corner)
        glVertex3d(+self.corner, -self.corner, -self.near-2*self.corner)
        
        glVertex3d(-self.corner, -self.corner, -self.far+2*self.corner)
        glVertex3d(self.corner, -self.corner, -self.far+2*self.corner)

        glEnd()
        glEndList()        
        return lspectr
    
    
    
    def drawAxisLegend(self):
        
        """Draw Axis Legend"""
        
        font = QFont("Typewriter")
        font.setPixelSize(10)
                
        #RT axis legend
        font.setPixelSize(12)
        self.qglColor(Qt.blue)
        mz_label = "retention time [s]";rt_label = "m/z"
        self.renderText(0.0,  -self.corner-20.0,  -self.near-2*self.corner+20.0, rt_label, font)
        self.renderText(-self.corner-20.0, -self.corner-20.0, -self.near-3*self.corner, mz_label, font)
        self.renderText(-self.corner-20.0, self.corner+10.0, -self.near-2*self.corner+20.0, "intensity %", font)
        font.setPixelSize(10)
        
#        #for rt number
#        for i in xrange (0,len(self.rtList), 100):
#            text = str(math.ceil(((self.rtList[i][0])*self.max_rt )/ self.max_rt))
#            self.renderText(-self.corner, 
#                            -self.corner -5.0, 
#                            -self.near-2*self.corner - self.rtList[i][0], 
#                            text, 
#                            font)
        
#        for i in xrange (0, len(self.massList[0]), 100):
#            text = str(math.ceil(((self.massList[0][i])*self.max_mass )/ 2*self.corner))
#            self.renderText( self.corner, 
#                             self.corner -5.0, 
#                            -self.near-2*self.corner - self.massList[0][i], 
#                            text, 
#                            font)
#        #for mz number

    def resetTranslations(self):
        
        """reset the different translation to 0"""
        
        self.trans_x =0.
        self.trans_y =0.
    
   
    def normalizeAngle(self,angle):
        """taken from qt documentation"""
        
        while (angle < 0):
            angle += 360 * 16
        while (angle > 360 * 16):
            angle -= 360 * 16
        return angle
    


    def computeSelection(self):pass
    


#===============================================================================
#              MOUSE AND KEYBOARDS EVENTS
#===============================================================================
    def wheelEvent(self, event):
        if event.delta() >0:
            self.zoom -= .05
            
        else:
            self.zoom += .05
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-self.corner*self.zoom, 
                self.corner*self.zoom,    
                -self.corner*self.zoom, 
                self.corner*self.zoom , 
                self.near, 
                self.far)
        glMatrixMode(GL_MODELVIEW)
        self.updateGL()
        event.accept()
        
    
    
    def keyPressEvent(self,  event):
        if event.key() == Qt.Key_Minus:
            self.zoom -= .1
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(-self.corner*self.zoom, 
                    self.corner*self.zoom, 
                    -self.corner*self.zoom, 
                    self.corner*self.zoom , 
                    self.near, 
                    self.far)
            glMatrixMode(GL_MODELVIEW)

        if event.key() == Qt.Key_Plus:
            self.zoom += .1
            glMatrixMode(GL_PROJECTION) #// You had GL_MODELVIEW
            glLoadIdentity()
            glOrtho(-self.corner*self.zoom, 
                    self.corner*self.zoom,    
                    -self.corner*self.zoom, 
                    self.corner*self.zoom , 
                    self.near, 
                    self.far)
            glMatrixMode(GL_MODELVIEW)
        
        
        if event.key() ==Qt.Key_Z:
            #store all values
            self.zoom_mode = True
            
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            font = QFont("Typewriter")
            self.renderText(0.,0.,0., "zooming mode", font)
            #little animation
            #a = -5
            #count = 0 
            if  self.yrot < 1444:
                while self.yrot < 1444:#and self.xrot < ref_rotx_:
                    #count += 1
                    self.xrot -=20
                    self.yrot +=20
                    #if self.zoom > a:
                    #    self.zoom-=1
                    self.updateGL()
                    
            elif self.yrot > 1444:
                while self.yrot <1444 :#and self.xrot < ref_rotx_:
                    #count += 1
                    self.xrot -=20
                    self.yrot -=20
                    #if self.zoom > a:
                    #    self.zoom-=1
                    self.updateGL()
            """
            count_ = 0
            tmp = self.xrot
            while  tmp < 1422:
                count_+=1
                tmp += 1
            b = count / count_
            count__ = 0
            """            
            while self.xrot < 1422:
                #count__+=1
                self.xrot+= 20
                #if self.zoom < 1: #and count__%b == 0:
                #    self.zoom+=1
                self.updateGL()


        if event.key() == Qt.Key_Up:
            self.trans_y +=10
        if event.key() == Qt.Key_Down:
            self.trans_y -=10
        if event.key() == Qt.Key_Left:
            self.trans_x -=10
        if event.key() == Qt.Key_Right:
            self.trans_x +=10
            
        self.updateGL()
        
    

    def mousePressEvent(self, event):
        self.lastpos = QPoint(event.pos())
#        modelview, projection =[], []
#        z =1
#        x, y =event.x(), event.y()
#        projection =glGetDoublev(GL_PROJECTION_MATRIX)
#        modelview= glGetDoublev(GL_MODELVIEW_MATRIX)
#        viewport=glGetIntegerv(GL_VIEWPORT)
#        glReadPixels( x, viewport[3]-y, 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT, z )
#        objx, objy, objz =gluUnProject( x, viewport[3]-y, z, modelview, projection, viewport)
#        print objx, objy, objz
        
        
    def mouseMoveEvent(self, event):
        
        dx = event.x() - self.lastpos.x()
        dy = event.y() - self.lastpos.y()
        
        if not self.zoom_mode:  
            if event.buttons() == Qt.LeftButton:
                a = self.normalizeAngle(self.xrot + 8 * dy)
                b = self.normalizeAngle(self.yrot + 8 * dx)
                self.xrot= a#self.xrot + 8 * dy
                self.yrot= b#self.yrot + 8 * dx
                
            if event.buttons()== Qt.RightButton:
                self.setCursor(QCursor(Qt.ClosedHandCursor))
                self.trans_y -= dy/5
                self.trans_x += dx/5
                
            self.lastpos = QPoint(event.pos())
            self.updateGL()
        
            
            
    def drawQuad(self):
        '''change to accept arguments pass'''
        glColor( 0., 0., 1.)
        glLineWidth(4.0)
        pointer_x = self.lastpos.x()/200.#self.corner
        pointer_y = self.lastpos.y()/200.#/(self.corner)
        norm_dx = dx/200.#/(self.corner)
        norm_dy = dy/200.#/(self.corner)
        #print -self.corner, pointer_x, pointer_y, norm_dx, norm_dy
        glBegin(GL_QUADS)
        glVertex3f(-self.corner + pointer_x, 
                   -self.corner + pointer_y, 
                   -self.near+2*self.corner)
        
        glVertex3f(-self.corner + pointer_x+ norm_dx, 
                   -self.corner + pointer_y,
                   -self.near+2*self.corner)
                   
        glVertex3f(-self.corner + pointer_x+ norm_dx, 
                   -self.corner + pointer_y + norm_dy,
                   -self.near+2*self.corner)
        
        glVertex3f(-self.corner + pointer_x, 
                   -self.corner + pointer_y,
                   -self.near+2*self.corner)
        glEnd()
        self.lastpos = QPoint(event.pos())
        #redraw eachtime mouse 's moving
        self.updateGL()   
    
    
    
    
        
    def mouseReleaseEvent(self, event):
        self.setCursor(QCursor(Qt.ArrowCursor))
        if self.zoom_mode:
            self.computeSelection()
        self.zoom_mode = False
    
    
    def closeEvent(self, event):
        self.releaseKeyboard()


    
#    def paintEvent(self, event):see overpainting example pyqt



class MSGradient(QWidget):
    def __init__(self, parent=None, **kw):
        QWidget.__init__(self, parent)
        self.setMaximumSize(1000, 50)
    def paintEvent(self, ev):
        """
        IceAndFire = Colormap("IceAndFire",
                      (0.00, (0.0, 0.0, 1.0)),
                      (0.25, (0.0, 0.5, 1.0)),
                      (0.50, (1.0, 1.0, 1.0)),
                      (0.75, (1.0, 1.0, 0.0)),
                      (1.00, (1.0, 0.0, 0.0)))
        """
        painter=QPainter()
        painter.begin(self)
        g = QLinearGradient(0,0,self.width(), self.height())
        g.setColorAt(0., QColor.fromRgbF(0.0, 0.0, 1.0))
        g.setColorAt(0.25, QColor.fromRgbF(0.0, 0.5, 1.0))
        g.setColorAt(0.5, QColor.fromRgbF(1.0, 1., 1.0))
        g.setColorAt(0.75, QColor.fromRgbF(1.0, 1., 0.))
        g.setColorAt(1., QColor.fromRgbF(1.0, 0., 0.))
        painter.setBrush(QBrush(g))
        painter.fillRect(0, 0, self.width(), self.height(), g)
        painter.end()


class Test(QWidget):
    def __init__(self, vertexes, colors, colormap=None, parent=None):
        from graphics.pyqtgraph.GradientWidget import BlackWhiteSlider

        QWidget.__init__(self, parent)
        v=QGridLayout(self)
        v.addWidget(MSGLCanvas3D(vertexes, colors, parent=self),0,0)
        #v.addWidget(BlackWhiteSlider(self),0,1)