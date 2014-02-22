#-*- coding: utf-8 -*-


__version__ ="0.1"
__contributors__=('Marco')


import os.path as path
import imp, sys
import platform     

from PyQt4.QtCore import SIGNAL, QT_VERSION_STR, PYQT_VERSION_STR, QMimeData
from PyQt4.QtGui import (QStandardItemModel, QMenu, QKeySequence,QAction, QIcon, 
                        QPixmap, QMainWindow, QToolTip, QMessageBox, QColor, 
                        QDockWidget, QWidget, QBrush, QToolBox, QTabWidget,
                        QVBoxLayout, QPushButton, QCursor, QProgressBar, 
                        QMdiSubWindow, QApplication, QAbstractItemView, QImage, QToolBar,
                        QToolButton, QCompleter, QDoubleSpinBox, QFormLayout, QCheckBox,
                        QLabel, QTableView, QSizePolicy, QDrag, QTreeWidget)
from PyQt4.QtCore import Qt, QSize, QSettings

from spyderlib.widgets.internalshell import InternalShell

from gui.MetBaseGui import (MSToDropTreeView, MSToDropTableView, MSDragFromTableView,
                            MSMdiArea, MSCompoundTreeView, MSTreeItemDelegate, MSPipelineToolBar)
#from controller.MetBaseControl import MSDialogController, WithPointerToQApp



style='''
        QTreeView::branch:has-siblings:!adjoins-item {
         border-image: url(vline.png) 0;
     }

     QTreeView::branch:has-siblings:adjoins-item {
         border-image: url(branch-more.png) 0;
     }

     QTreeView::branch:!has-children:!has-siblings:adjoins-item {
         border-image: url(branch-end.png) 0;
     }

     QTreeView::branch:has-children:!has-siblings:closed,
     QTreeView::branch:closed:has-children:has-siblings {
             border-image: none;
             image: url(branch-closed.png);
     }

     QTreeView::branch:open:has-children:!has-siblings,
     QTreeView::branch:open:has-children:has-siblings  {
             border-image: none;
             image: url(branch-open.png);
     }'''
stylesheet='''
QToolBar {
     background: qlineargradient(x1: 0, y1:1, x2: 1, y2: 1,
                stop: 0 #a6a6a6, stop: 0.08 #7f7f7f,
                stop: 0.39999 #717171, stop: 0.4 #626262,
                stop: 0.9 #4c4c4c, stop: 1 #333333);
 }
 QToolButton { /* all types of tool button */
     color: white;
}
'''

#------------------------------------------------------------------------------
#Ipython support
#from IPython.utils.localinterfaces import LOCAL_IPS
#from IPython.frontend.qt.console.qtconsoleapp import IPythonQtConsoleApp
#
#
#class IPythonApp(IPythonQtConsoleApp):
#    def init_qt_elements(self):
#        # Create the widget.
#        local_kernel = (not self.existing) or self.ip in LOCAL_IPS
#        self.widget = self.widget_factory(config=self.config,
#                                          local_kernel=local_kernel)
#        self.widget.kernel_manager = self.kernel_manager
#        
#def create_widget(argv=None):
#    app = IPythonApp()
#    app.initialize(argv)
#    return app.widget


class MSMainWindow(QMainWindow):
    """Gui of the main window"""
    
    #MAX_RECENT_FILES = 10
    #start putting links spyder numpy scipy et tutti quanti
    links=('http://numpy.scipy.org/',
           'http://packages.python.org/spyder/',
           'http://www.riverbankcomputing.co.uk/software/pyqt/intro')
    
    pluginPath=path.normcase('pluginmanager/plugins/')    
    
    def __init__(self, availablePlugins):
        """
        Constructor with all the models needed setup menus
        
        """
        QMainWindow.__init__(self)
        self.setDockOptions(QMainWindow.VerticalTabs | QMainWindow.AnimatedDocks)
        self.plugins = availablePlugins
        self.pluginsInst=[]   
        settings=QSettings('INRA/INSA', '-'.join([QApplication.instance().APPLICATION_NAME_STR, 
                                                  QApplication.instance().VERSION_STR]))  
        self.recentFiles = list(settings.value("RecentFiles").toStringList())
        self.setStyleSheet(stylesheet)
        self.pipeline = MSPipelineToolBar("Pipeline toolbar", parent=self)
        self.addToolBar(0x1,self.pipeline)
        
        self._setupModels()
        self._setupUi()        
        self._setupMenus()

    def _setupModels(self):
        """
        Warning:Causes segfault when horizontal labels set to True
        
        on aura peu etre a la fin un model par sampleList c'est ce qui parait
        le plus logique
        
        """        
        #drag and drop table sample
        self.sampleModel = QStandardItemModel(self)      
        self.sampleModel.setHorizontalHeaderLabels(["Sample", "Class"])
        #treeView1
        self.spectraModel = QStandardItemModel(self)
        #treeview2
        self.peakModel = QStandardItemModel(self)
        #treeview3
        self.clusterModel = QStandardItemModel(self)
 
    def _setupMenus(self):
        #file
        self.fileMenu = QMenu('&File')
        self.fileMenu.setTearOffEnabled(True)
        self.op=QMenu("&Open...",self.fileMenu)
        self.op.setIcon(QIcon(path.normcase("gui/icons/fileopen.png")))
        
        open_=QAction("&Open rawfiles", self)
        open_.setToolTip("Open an mzXML or netCDF file")
        open_.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_O))
        open_icon=QIcon(path.normcase("gui/icons/fileopen.png"))
        open_.setIcon(open_icon)
        self.op.addAction(open_)
        
        load_=QAction("&Open projects...", self)
        load_.setToolTip("load binary file containing saved objects")
        load_.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_S))
        load_icon=QIcon(QPixmap(path.normcase("gui/icons/project_open.png")))
        load_.setIcon(load_icon)
        self.op.addAction(load_)
        
        self.fileMenu.addMenu(self.op)
        
        save_=QAction("&Save...", self)
        save_.setToolTip("save the actual application model")
        save_.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_S))
        save_icon=QIcon(path.normcase("gui/icons/save_all.png"))
        save_.setIcon(save_icon)
        self.fileMenu.addAction(save_)
        
        pkl = QAction("&load a peaklist", self) #TODO:load peaklist
        pkl.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_P))
        pkl.setToolTip("load a peaklist and process it")
        pkl.setIcon(QIcon(path.normcase("gui/icons/featuredetect.png")))
        self.fileMenu.addAction(pkl)
        
        convert_=QAction("&Convert...", self)
        convert_.setEnabled(False)
        convert_.setToolTip("Convert a .wiff file if Analyst(c) is installed")        
        convert_icon=QIcon(path.normcase("gui/icons/goto.png"))
        convert_.setIcon(convert_icon)
        self.fileMenu.addAction(convert_)
        
        a = self.fileMenu.addAction(QIcon(path.normcase("gui/icons/process.png")), "&Launch a batch")
        a.setEnabled(False)
        
        b = self.fileMenu.addAction(QIcon(path.normcase("gui/icons/process.png")), "&Merge")
        b.setToolTip("Merge MRM file")
        #b.setEnabled(False)
        
        self.fileMenu.addSeparator()
#        
#        for i in xrange(self.MAX_RECENT_FILES):
#            a = QAction('', self)
#            a.setVisible(False)
#            self.fileMenu.addAction(a)
#        
#        for i in xrange(min(self.MAX_RECENT_FILES, len(self.recentFiles))):
#            self.fileMenu.actions()[5+i].setVisible(True)
#            self.fileMenu.actions()[5+i].setText(self.recentFiles[i].split('/')[-1])
            
        
        exit_action =QAction("&Exit", self)
        exit_action.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Q))
        exit_action.setIcon(QIcon(QPixmap(path.normcase('gui/icons/exit.png'))))
        self.fileMenu.addAction(exit_action)
        
        self.menuBar().addMenu(self.fileMenu)
        
        self.editMenu=QMenu("&Edit")
        self.editMenu.setTearOffEnabled(True)
        self.editMenu.addAction(QIcon(path.normcase('gui/icons/edit_undo.png')), '&Undo...')
        self.editMenu.addAction(QIcon(path.normcase('gui/icons/edit_redo.png')), '&Redo...')
        self.editMenu.actions()[0].setEnabled(False)
        self.editMenu.actions()[1].setEnabled(False)
        self.editMenu.addSeparator()
        self.editMenu.addAction(QIcon(path.normcase('gui/icons/run.png')), '&Preferences')
        self.exportMenu = QMenu("&Export...")
        self.exportMenu.setIcon(QIcon(path.normcase('gui/icons/file_export.png')))
        self.exportMenu.addAction("&Peaklist")        
        self.exportMenu.addAction("&Clusters intensity matrix")
        self.editMenu.addMenu(self.exportMenu)        
        self.menuBar().addMenu(self.editMenu)
        
        
        #view
        self.viewMenu =QMenu("&View")
        self.viewMenu.setTearOffEnabled(True)
        self.viewMenu.addAction(QIcon(path.normcase('gui/icons/window_duplicate')),
                                "&Cascade View", 
                                self.mdiArea.cascadeSubWindows, 
                                QKeySequence(Qt.CTRL + Qt.Key_K))
        self.viewMenu.addAction(QIcon(path.normcase('gui/icons/view_icon')),
                                "&Title View", 
                                self.mdiArea.tileSubWindows, 
                                QKeySequence(Qt.CTRL + Qt.Key_N))
        self.viewMenu.addAction(QIcon(path.normcase("gui/icons/stop_process.png")),
                                "&Close all subWindows",
                                self.mdiArea.closeAllSubWindows,
                                QKeySequence(Qt.CTRL+Qt.Key_W))
        
        self.plotting =QMenu("&Plotting...")
        self.plotting.setIcon(QIcon(QPixmap(path.normcase("gui/icons/plot.png"))))
        self.plotting.addAction("&3D Plot")
        #self.plotting.addAction("&Cytoscape web")
        self.plotting.addAction("&Spectrogram Plot")
        
        #self.multiplePlot = QAction("&Visualize Raw/Treated Data", self)
        #self.multiplePlot.setCheckable(True)
        #self.multiplePlot.setEnabled(False)
        #self.sub_plot_.addAction(self.multiplePlot)
       
        self.viewMenu.addMenu(self.plotting)
        self.viewMenu.addSeparator()
        self.show_hide=QMenu("&Show/Hide")
        m=self.createPopupMenu()
        m.setTitle("&Show/Hide")
        self.viewMenu.addMenu(m)
        #self.pref = QMenu("&Preferences")
       
        #self.pref.addAction(self.multiplePlot)
        #self.viewMenu.addMenu(self.pref)
        self.menuBar().addMenu(self.viewMenu)

        #algorithm
        self.algoMenu= QMenu("&Algorithm")
        self.algoMenu.setTearOffEnabled(True)
        self.preProcessing=QMenu("&PreProcessing(experimental)")
        self.preProcessing.addAction("&Smoothing raw data...")
        self.preProcessing.addAction("&Cut off raw data...")
        self.preProcessing.addAction('&Calibration (mz dimension)')
        self.preProcessing.addAction("&Resize sample...")
        
        self.algoMenu.addMenu(self.preProcessing)
        
        self.peakPickingMenu = QMenu("&Peack Picking & Alignement(XCMS)", self)
        self.peakPickingMenu.setIcon(QIcon(path.normcase("gui/icons/pickedpeakicon.png")))
        
        matched = QAction("&MatchedFiltered", self)
        matched.setIcon(QIcon(path.normcase('gui/icons/RLogo')))
        matched.setToolTip("Peak Detection and Integration using MatchedFiltered algorithm")
        self.peakPickingMenu.addAction(matched)        
        
        centwave=QAction("&CentWave", self)
        centwave.setIcon(QIcon(path.normcase('gui/icons/RLogo')))
        centwave.setToolTip("Peak Detection and Integration using CentWave algorithm")
        self.peakPickingMenu.addAction(centwave)
        #peak_.setShortcut(.QKeySequence(CTRL + Key_P))
       # peak_icon=.QIcon(.QPixmap(path.normcase("gui/icons/pickedpeakicon.png")))
        #peak_.setIcon(peak_icon)
        self.algoMenu.addMenu(self.peakPickingMenu)
        
        self.alignment = QMenu("&Alignment")
        self.alignment.setIcon(QIcon(path.normcase('gui/icons/format_indent_more.png')))
        self.alignment.addAction("&Polynomial fitting(exp)")
        self.alignment.addAction("&DynamicTimeWarping")
        self.alignment.addAction("&ObiWarp")
        self.alignment.actions()[2].setEnabled(False)
        self.algoMenu.addMenu(self.alignment)
        
        self.algoMenu.addAction("Normalization")
        
        clust_ =  QAction("&Clustering", self)
        clust_.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_L))
        clust_icon=QIcon(QPixmap(path.normcase("gui/icons/cluster.png")))
        clust_.setIcon(clust_icon)
        self.algoMenu.addAction(clust_)
        
        id_ =  QAction("&Identification", self)
        id_.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_I))
        id_.setToolTip("Try to identify peaks with several methods")
        id_.setIcon(QIcon(QPixmap(path.normcase("gui/icons/findcompound.png"))))
        self.algoMenu.addAction(id_)
        self.menuBar().addMenu(self.algoMenu)        
        
     
        
        #tools
        self.toolsMenu =QMenu("&Tools")
        self.toolsMenu.setTearOffEnabled(True)
        web =  QAction("&Web Browser", self)
        web.setIcon(QIcon(QPixmap(path.normcase("gui/icons/applications_internet.png"))))
        self.toolsMenu.addAction(web)
        #cyto = QAction("&cytoscape", self)
        #cyto_icon =QIcon(QPixmap(path.normcase("gui/icons/cytoscape.jpeg")))
        #cyto.setIcon(cyto_icon)
        #self.toolsMenu.addAction(cyto)
        editor = QAction("&Editor", self)
        editor.setIcon(QIcon(QPixmap(path.normcase("gui/icons/document_sign.png"))))
        self.toolsMenu.addAction(editor)
        pet=QAction("&Short Periodic Table", self)  
        pet.setIcon(QIcon(QPixmap(path.normcase("gui/icons/pet.jpg"))))
        self.toolsMenu.addAction(pet)
        self.menuBar().addMenu(self.toolsMenu)
        
        #plugins
        self.pluginMenu = QMenu('&Plugins')
        self.pluginMenu.setTearOffEnabled(True)
        instPl=  QAction("&Install a plugin", self)
        instPl.setIcon(QIcon(path.normcase('gui/icons/pluginInstall.png')))
        self.pluginMenu.addAction(instPl)
        self.launchingMenu = QMenu("&Launch PLugins", self)
        self.launchingMenu.setIcon(QIcon(path.normcase('gui/icons/plugin')))
        
        for plug in self.plugins:
            #fullname="".join([self.pluginPath, str(plug)])
            mod=imp.load_source(self.__module__, plug)
            if mod.autoActivation:
                qApp=QApplication.instance()
                name=getattr(mod, 'className')
                cls=getattr(mod, name)
                p=cls(qApp.model, self, parent=self)                
                #p=qApp.pluginManager.loadPlugin(qApp.model, self, plug.split('/')[-1])
                self.pluginsInst.append(p)
            else:
                self.launchingMenu.addAction(plug.split('/')[-1])
        self.pluginMenu.addMenu(self.launchingMenu)
        self.pluginMenu.addAction(QIcon(path.normcase("gui/icons/process_stop.png")),
                                        "&Remove loaded Plugin")
        self.menuBar().addMenu(self.pluginMenu)
        
        #about
        self.aboutMenu= QMenu("&About")
        self.aboutMenu.setTearOffEnabled(True)
        metms = QAction(QIcon(path.normcase('gui/icons/deluge.png')), "&about metMS...", self)
        self.aboutMenu.addAction(metms)
        
        pyqt =  QAction("&about PyQt4...", self)
        pyqt_icon =QIcon(QPixmap(path.normcase("gui/icons/logo_QT4.png")))
        pyqt.setIcon(pyqt_icon)
        self.aboutMenu.addAction(pyqt)
        metms =  QAction("&metMS Documentation", self)
        metms_icon =QIcon(QPixmap(path.normcase("gui/icons/deluge.png")))
        metms.setIcon(metms_icon)
        self.aboutMenu.addAction(metms)
        self.menuBar().addMenu(self.aboutMenu)
        

    def _setupUi(self, background=None):
        """        
        Make the GUI
        
        """
        #mdi
        self.mdiArea = MSMdiArea(self)
        self.mdiArea.setBackground(QBrush(QPixmap(path.normcase('gui/icons/blac2.png'))))#QColor(Qt.blue).darker()))
        self.setCentralWidget(self.mdiArea)
        
        
        #sample dock widget
        self.sampleDockWidget = QDockWidget("Samples", self)
        #sampleWidget = QWidget()
        self.sampleTableView = MSDragFromTableView()
        self.sampleTableView.setModel(self.sampleModel)
        self.sampleTableView.setSelectionBehavior(1)
        self.sampleTableView.verticalHeader().hide()
        self.sampleTableView.verticalHeader().setDefaultSectionSize(15)        
        self.sampleTableView.horizontalHeader().setDefaultSectionSize(150)
        

        self.sampleDockWidget.setWidget(self.sampleTableView)#sampleWidget)
        self.sampleDockWidget.visible=True
        
        
        #workflow dock
        self.workflowDockWidget = QDockWidget("Visualizer", self)
        self.workflowDockWidget.visible = True

        a=QWidget(self)
        v=QVBoxLayout(a)
        q=QToolBar()
        #self.workingSample = QLabel("Working Sample:None")
        #q.addWidget(self.workingSample)
        q.addWidget(QLabel("ppm :"))
        self.ppmEditer=QDoubleSpinBox()
        self.usePpm=QCheckBox("use ?")  
        q.addWidget(self.ppmEditer)
        q.addWidget(self.usePpm)
        
        q.addSeparator()
        
        self.removeButton=QToolButton(self)
        self.removeButton.setIcon(QIcon(path.normcase("gui/icons/delete.png")))           
        q.addWidget(self.removeButton)
        
        self.markAsGood=QAction(QIcon(path.normcase("gui/icons/button_ok.png")),"mark peak as good", self)
        self.markAsBad=QAction(QIcon(path.normcase("gui/icons/stop.png")), "mark peak as bad", self)
        self.hideItem = QAction(QIcon(path.normcase("gui/icons/list_remove.png")), "Hide Item", self)
        
        q.addAction(self.markAsGood)
        q.addAction(self.markAsBad)
        q.addAction(self.hideItem)
        v.addWidget(q)        
        
        
        self.tabWidget = QTabWidget()
        self.tab = QWidget()
        verticalLayout = QVBoxLayout(self.tab)
        self.treeView = MSToDropTableView()
        self.treeView.verticalHeader().setDefaultSectionSize(20)
        
        self.treeView.setModel(self.spectraModel)
        self.spectraLabel = QLabel("Sample: None")
        verticalLayout.addWidget(self.treeView)
        verticalLayout.addWidget(self.spectraLabel)
        self.tabWidget.addTab(self.tab, QIcon(path.normcase("gui/icons/spectrumicon.png")),"Spectra")
        
        self.tab_2 = QWidget()
        verticalLayout_4 = QVBoxLayout(self.tab_2)
        self.treeView_2 = MSToDropTableView()#MSTreeView(self.tab_2)# QTableView(self)#
        self.treeView_2.verticalHeader().setDefaultSectionSize(20)
        self.treeView_2.setModel(self.peakModel)
        self.peakLabel = QLabel("Sample: None")
        verticalLayout_4.addWidget(self.treeView_2)
        verticalLayout_4.addWidget(self.peakLabel)
        self.tabWidget.addTab(self.tab_2,QIcon(path.normcase("gui/icons/peakicon.png")), "Peaks List")
        
        self.tab_3 = QWidget()
        verticalLayout_5 = QVBoxLayout(self.tab_3)
        self.treeView_3 = MSToDropTreeView()
        self.treeView_3.setAnimated(True)
        self.treeView_3.setModel(self.clusterModel)
        self.clusterLabel = QLabel("Sample: None")
        verticalLayout_5.addWidget(self.treeView_3)
        verticalLayout_5.addWidget(self.clusterLabel)
        self.tabWidget.addTab(self.tab_3, QIcon(path.normcase("gui/icons/clustering.png")), "Clusters")
        
        self.tabWidget.setCurrentIndex(0)
        
        for l in (self.spectraLabel, self.peakLabel, self.clusterLabel):
            l.setAutoFillBackground(True)
            
        v.addWidget(self.tabWidget)
        self.workflowDockWidget.setWidget(a)
        self.addDockWidget(Qt.DockWidgetArea(0x2),self.workflowDockWidget)        
        
                
        from gui.MetBaseGui import MSIsoCalculator
        self.isoCalc = MSIsoCalculator(self)
        self.isoCalcDockWidget=QDockWidget('isotopes calculation', self)
        self.isoCalcDockWidget.setWidget(self.isoCalc)
        self.addDockWidget(Qt.DockWidgetArea(0x2), self.isoCalcDockWidget)
        self.isoCalcDockWidget.setVisible(False)
        self.isoCalcDockWidget.visible=False
        
        from gui.MetBaseGui import FormulaGenerator
        self.generator=FormulaGenerator(self)
        self.generatorDockWidget=QDockWidget('formula generator', self)
        self.generatorDockWidget.setWidget(self.generator)
        self.addDockWidget(Qt.DockWidgetArea(0x2), self.generatorDockWidget)
        self.generatorDockWidget.setVisible(False)
        self.generatorDockWidget.visible=False
        
        self.compoundTreeView = MSCompoundTreeView(self)
        self.compoundDockWidget = QDockWidget("Compounds", self)
        self.compoundDockWidget.setWidget(self.compoundTreeView)
        self.addDockWidget(Qt.DockWidgetArea(0x2),self.compoundDockWidget)
        self.compoundDockWidget.setVisible(False)
        self.compoundDockWidget.visible=False
        
        self.comparativeTableView = QTableView(self)
        self.comparativeTableView.horizontalHeader().setStretchLastSection(True)
        self.comparativeTableView.verticalHeader().setDefaultSectionSize(20)
        self.comparativeDock = QDockWidget("Comparative View", self)
        self.comparativeDock.setWidget(self.comparativeTableView)
        self.addDockWidget(Qt.DockWidgetArea(0x8), self.comparativeDock)
        self.comparativeDock.setVisible(False)
        self.comparativeDock.visible = False
        
        self.tabifyDockWidget(self.compoundDockWidget, self.isoCalcDockWidget)
        self.tabifyDockWidget(self.isoCalcDockWidget, self.workflowDockWidget )
        self.tabifyDockWidget(self.workflowDockWidget, self.generatorDockWidget)
        #set the end
        
        #WARNING: possible that the internal shell widget cause random segfault
        #with the error of QObject::killTimers...? not sure !
        self.shell = QWidget()#InternalShell(namespace={'metms': QApplication.instance()}, 
                     #              parent=self, 
                     #              multithreaded=False)
        self.shellDock = QDockWidget("Python Shell", self)
        self.shellDock.setWindowIcon(QIcon(path.normcase('gui/icons/stop.png')))
        self.shellDock.setWidget(self.shell)
        self.shellDock.setMinimumWidth(255)
        self.shellDock.visible=True
        self.addDockWidget(0x2, self.shellDock)

        self.addDockWidget(0x2, self.sampleDockWidget)
        self.tabifyDockWidget(self.shellDock, self.sampleDockWidget)
        
        self.pb = QProgressBar(self)
        self.pb.setMaximumWidth(245)
        
        self.stopProcess = QToolButton(self)
        self.stopProcess.setIcon(QIcon(path.normcase("gui/icons/process_stop.png")))        
        m = QMenu()
        #self.connect(m, SIGNAL('triggered(QAction*'), QApplication.instance().taskManager.abortByName)
        self.stopProcess.setMenu(m)
        self.stopProcess.setPopupMode(1) #Menu Button
        #self.connect(self.stopProcess, SIGNAL("clicked()"), self.stopThread)
        
        self.statusBar().addPermanentWidget(self.stopProcess)
        self.statusBar().addPermanentWidget(self.pb)
    
    def updateStopProcessMenu(self):
        """
        update the menu of the stop process
        button, based directly on the processes
        stored by the task manager
        
        """
        self.stopProcess.menu().clear()
        for c in QApplication.instance().taskManager:
            self.stopProcess.menu().addAction(c.title)
        
        #QApplication.instance().taskManager.abort(QApplication.instance().taskManager[-1])
        
    def addMdiSubWindow(self, plot, title="", showMaximized=False):
        """ 
        Allow addition of new window in the mdiarea
        
        """        
        win=self.mdiArea.addSubWindow(plot)
        #print "widget parent", plot.parent()
        win.setAttribute(Qt.WA_DeleteOnClose)
        #win.connect(win, SIGNAL('destroyed(QObject *)'), self.testdestroy)
        #plot.setParent(win)
        win.setWindowTitle(title)
        if showMaximized:
            win.showMaximized()
        else:
            win.resize(400, 300)
        win.show()
        return win
   

           
    def updateTreeView(self):
        """
        Tree View update switch spectre/chromato
        
        """
        if self.treeView.model() == self.spectraModel:
            self.treeView.setModel(self.chromaModel)
            self.tabWidget.setTabText(0, "Chroma")
        else:
            self.treeView.setModel(self.spectraModel)
            #self.treeView.setSelectionMode(1)
            self.tabWidget.setTabText(0, "Spectra")
    
    def addTreeViewModel (self,model1, model2):
        """Add a model """
        self.chromaModel.appendRow(model1)
        self.spectraModel.appendRow(model2)
    
    
    def _actionHovered(self, action):
        """emulate tooltip cause they do not work that much"""
        tip = action.toolTip()
        QToolTip.showText(QCursor.pos(), tip)
    

    def showErrorMessage(self, title, string):
        QMessageBox.critical(self, title, string, 0, 0)
    
    
    def showWarningMessage(self, title, string):
        return QMessageBox.warning(self, title, string, QMessageBox.Ok|QMessageBox.Cancel)
    
    
    def showInformationMessage(self, title, string):
        QMessageBox.information(self, title, string, 0)
        
    
    def updateProgressBar(self, i):
        """update the value of the progress bar for all the treatment"""
        
        self.pb.setValue(min(i, 100))

    def to_indetermined_mode(self):
        self.pb.setMaximum(0)
        
    
    def to_determined_mode(self):
        self.pb.setMaximum(100)
        
    
    def showInStatusBar(self, string, time=5000):
        self.statusBar().showMessage(string, time)
    
    
    
    def addInterpreterDock(self, shell):
        self.shellDock = QDockWidget(self)
        self.shellDock.setWidget(shell)
        self.shellDock.setWindowTitle("shell")
        self.addDockWidget(0x2, self.shellDock)
        
    
    
    def showMetMSInformation(self):
        
        QMessageBox.about(self,
            self.tr("About %1").arg("metMS"),
            self.tr("""<b>%1 %2</b>
            <br>metabolite Mass Spectrometry
            <p>Copyright &copy; 2010 Marco INSA, INRA
            <br>Licensed under the terms of the CeciLL License
            <p>Developed and maintained by Marco
            <br>Bug reports and feature requests: 
            <a href="http://github.com/jerkos/metms">metMS site</a><br>
            Discussions around the project: 
            <a href="http://groups.google.com/group/spyderlib">Google Group</a>
            <p>This project is part of the BRIDGE project
            <p>Python %3, Qt %4, PyQt %5""") \
            .arg("metMS").arg(__version__) \
            .arg(platform.python_version()).arg(QT_VERSION_STR) \
            .arg(PYQT_VERSION_STR))


