#!/usr/bin/python
# -*- coding: utf-8 -*-



#This file is part of metMS software.
#Copyright: Fabien Jourdan, Fabien Létisse, Marc Dubois
#MetMS is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published 
#by the Free Software Foundation, either version 3 of the License, 
#or (at your option) any later version.

#MetMS is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with MetMS. If not, see <http://www.gnu.org/licenses/>.


#naming conventions(for developers):
#all modules of this software start with the key-word 'Met'. So on, all 
#classes name start with the prefix 'MS'. We use 'CapitalizeWords' for 
#classes' name and 'mixedCase' for methods' name; variables and attributes, 
#how we are used to.
#in order keeping a readable code we strongly encourage developpers to 
#avoid to prefix private attributes with two underscores (namespaces conflicts). 

"""Entry point of the application"""
__version__ = "$Revision:1"
__author__ =('marco', 'cram@hotmail.fr')



import os
import os.path as path
import sys
import getopt
import sip
#sip.setapi('QString', 2)
#sip.setapi('QVariant', 2)

"""test requirements third pary library"""
try:
    from PyQt4.QtGui import QApplication, QPixmap, QIcon, QUndoStack, QSplashScreen
    from PyQt4.QtCore import SIGNAL, QSettings, QSize, QPoint
    from PyQt4.QtOpenGL import QGLFormat
    from PyQt4.QtCore import Qt
except ImportError: 
    print ("PyQt is not properly installed")
    sys.exit(1)


try:
    import psyco
    psyco.full()
    psyco_support = 1
except ImportError:
    psyco_support = 0


class metMS(QApplication):
    """metms application object"""
    
    VERSION_STR = '0.3.4'
    APPLICATION_NAME_STR = 'MetMS'         
    psyco_ = psyco_support
    
    def __init__(self, argv):
        """
        Constructor
        @load a config dictionnary
        
        """
        QApplication.__init__(self, argv)
        self.settings=QSettings()
        #for e in self.settings.allKeys():
        #    print str(e)
        self.connect(self, SIGNAL('lastWindowClosed()'), self.goodbye)
        
        self.undoStack = QUndoStack(self)
        self.useGL = self.checkGL()
        self.lowMemory = False
        self.multiCore = False
        #self.modelView = 'Samples View'
        #self.showSplash=self.settings.value('showSplash', True).toBool()
        from gui.MetBaseGui import MSSplashScreen
        self.splash = MSSplashScreen(QPixmap(path.normcase("gui/icons/Tux-G2.png")), Qt.WindowStaysOnTopHint)
        self.splash.show()
        #self.splash.setMask(pixmap.mask())        
        self.splash.showMessage((u'Starting now...'), Qt.AlignCenter | Qt.AlignBottom, Qt.black)
        self.processEvents()
        self.controllers = {}
        self.metmsconfig=self.loadConfiguration()
        
    
    def checkGL(self):
        gl_support = True
        if not sys.platform.startswith("linux"):
            #causes a segmetnation fault
            if not QGLFormat.hasOpenGL():
                gl_support=False            
        return gl_support  
           
    
    def buildGui(self):
        
        STEP=4
        #if self.showSplash:
        self.splash.showMessage((u'Loading core objects...'), Qt.AlignCenter|Qt.AlignBottom, Qt.black)
        from core.MetObjects import  MSSampleList
        self.model = MSSampleList()
        
        from pluginmanager.MetPluginFactory import MSPluginManager
        self.pluginManager = MSPluginManager(self)
        plugs=self.pluginManager.getAvailablePlugins()
        
        
        self.splash.showMessage((u'Loading task manager...'), Qt.AlignCenter|Qt.AlignBottom, Qt.black)
        from controller.MetBaseControl import MSTaskManager
        self.taskManager = MSTaskManager()
        self.splash.setValue(100./STEP)
            
        #if self.showSplash:
        self.splash.showMessage((u'Loading gui files...'), Qt.AlignCenter|Qt.AlignBottom, Qt.black)
        from gui.MetMainGui import MSMainWindow
        self.view=MSMainWindow(plugs)
        
        def closeEvent(e):
            self.writeSettings()
            e.accept()
            
        self.view.closeEvent=closeEvent
        self.view.setWindowIcon(QIcon(QPixmap(path.normcase("gui/icons/deluge.png"))))
        self.view.setWindowTitle(u' '.join([self.APPLICATION_NAME_STR, self.VERSION_STR]))
        self.splash.setValue(2*(100./STEP))
      
        #if self.showSplash:
        self.splash.showMessage((u'Loading controllers...'), Qt.AlignCenter|Qt.AlignBottom, Qt.black)
        from controller.MetDockWidgetControl import MSDockController
        from controller.MetMenuBarControl import MSMenuController
        from controller.MetMdiControl import MSMdiAreaController
        
        self.menuControl = MSMenuController(self.model, self.view)
        self.dockControl = MSDockController(self.model, self.view)
        self.mdiControl = MSMdiAreaController(self.model, self.view)
        
        self.splash.setValue(3*(100./STEP))
       
        #if self.showSplash:
        #self.splash.showMessage((u'Loading plugins...'), Qt.AlignCenter|Qt.AlignBottom, Qt.black)
        

        #the following allow to delete threads and controllers
        #it is very important ;)
        #self.connect(self, SIGNAL('deleteLastController()'), self.taskManager.deleteController)
        self.splash.setValue(4*(100./STEP))
        
        
        self.splash.showMessage((u'Loading last parameters...'), Qt.AlignCenter|Qt.AlignBottom, Qt.black)
        if self.settings.value("fullScreen", True).toBool():
            self.view.showMaximized()
        else:
            self.view.resize(self.settings.value("size", QSize(600,600)).toSize())
            self.view.move(self.settings.value("pos", QPoint(200,200)).toPoint())
            
        self.view.show()
        self.splash.finish(self.view)

            
    def goodbye(self):
        try:
            self.view.shell.exit_interpreter()
            #settings=QSettings('INRA/INSA', '-'.join([self.APPLICATION_NAME_STR, self.VERSION_STR]))
            #settings.setValue("internalShell", self.shell.isVisible())
        except AttributeError:
            pass

        
   
    def writeSettings(self):
        settings=QSettings('INRA/INSA', '-'.join([self.APPLICATION_NAME_STR, self.VERSION_STR]))
        settings.setValue("fullScreen", self.view.isMaximized())
        if not self.view.isMaximized():
            settings.setValue("pos", self.view.pos())
            settings.setValue("size", self.view.size())
        settings.setValue("RecentFiles", self.view.recentFiles)
        
   
   
         
    
    def options(self, config):
        """
        parsing command  line arguments
        """        
        def usage():
            print ("Available options:")
            print ("--nogl: allow openGl usage for drawing default: on")
            print ("--webyo: will use a private web browser default:on")
            print ("--shell: add an internal widget default:off")
        
        try:
            opts, args = getopt.getopt(sys.argv[1:],'x', ['gl-disabled', 'help', 'h','nogl', 'shell', 
                                       'nosplash', 't=', 'tulip=', 'lowMemory', 'lowM', 'multiCore', 'multiM'])
        except getopt.GetoptError, err:
            print str(err)
            usage()
            sys.exit(2)
        
        for o, a in opts:
            if o in ("-gl-disabled", "--gl-disabled", "-nogl", "--nogl"):
                if self.gl_support:
                   config['useGL'] = 0
                else:
                    print ("Can not use OpenGL display, no support found\nPlease remove the '--gl' option")
                    sys.exit(1)
            elif o in ("-h", "--help"):
                usage()
                sys.exit()
            elif o in ("--webyo"):
                self.usedWebyo = 1
            elif o in ("--shell", "-shell"):
                config['internalShell']=True
            elif o in ("--nosplash"):
                config["showSplash"]=False
            elif o in ('--tulip', '-t'):
                if sys.platform.startswith('linux'):
                    if not os.environ['LD_LIBRARY_PATH']:
                        os.environ['LD_LIBRARY_PATH']+=a
                        from subprocess import Popen
                        p = Popen('python metms.py --shell', shell=True)
                        sys.exit(1)
                else:
                    print("You must add tulip_dir/lib in your path environment variable")
            elif o in ('--lowM', '-lowM', '--lowMemory', '-lowMemory'):
                self.lowMemory = True
            elif o in ('--multiCore', '--multiC'):
                self.multiCore = True
            else:
               usage()
               sys.exit()
        
    def loadConfiguration(self):
        from config.config import metmsconfig
        self.options(metmsconfig.config)#override configuration
        return metmsconfig.config
                    
    def deleteController(self):
        """
        deletion of threads and controllers
        test if one thread is finished then delete 
        his controller
        
        """
        toDelete=[c for c in self.controllers.iterkeys() if self.controllers[c].isFinished()]
        for c in toDelete:
            sip.delete(self.controllers[c])
            del self.controllers[c]
    
                
    def currentModelChanged(self):
        self.emit(SIGNAL('modelChanged'), self.model)
        


if __name__== "__main__":
    instance = metMS(sys.argv)
    instance.buildGui()
    sys.exit(instance.exec_())
