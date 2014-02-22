# -*- coding: utf-8 -*-

# Copyright (c) 2010 INRA INSA Marc Dubois
#

"""
Module implementing the log viewer widget and the log widget.
and various additional widget
"""

import os.path as path
import sqlite3
from PyQt4.QtGui import (QMdiSubWindow, QCursor, QSplashScreen, QProgressBar,
                         QTextEdit, QMessageBox, QMenu, QTextCursor, QApplication,
                         QTreeView, QAbstractItemView, QAction, QMdiArea, QIcon, 
                         QPixmap, QSplitter, QToolBar, QIcon, QWidget, QVBoxLayout,
                         QPushButton, QHBoxLayout, QFileDialog, QStandardItemModel, QStandardItem,
                         QTableView, QListView, QItemDelegate, QStyledItemDelegate, QColor,
                         QCheckBox, QAbstractItemDelegate, QStyle,QStyleOptionButton, QLabel,
                         QLineEdit, QGroupBox, QFormLayout, QSpinBox, QComboBox, QDialog, QPen, QGraphicsLineItem,
                         QCompleter, QDoubleSpinBox, QItemSelectionModel, QBrush, QInputDialog, QFont,
                         QPalette, QSizePolicy, qApp, QGraphicsBlurEffect, QSpacerItem, QToolButton, QDockWidget, QTabWidget,
                         QDialogButtonBox, QRadioButton, QDrag, QHeaderView, QToolTip, QImage, QImageReader)
from PyQt4.QtCore import (SIGNAL, Qt, pyqtSignal, QPoint, QRect,  QAbstractItemModel, QSize, QTimer, QModelIndex,
                          QPropertyAnimation, QMimeData, QUrl)
from numpy import round
#from utils.MetHelperFunctions import check

from pe import Ui_Dialog
from core.MetDataObjects import MSElement, MSAlphabet
from graphics.MetMplCanvas import MSQtCanvas
from controller.MetBaseControl import MSDialogController
import weakref


class WithPointerToQApp(object):
    qApp=QApplication.instance()



class MSMdiSubWindow(QMdiSubWindow):
    
    #subWindowClosed=pyqtSignal()
    
    def __init__(self, parent=None):
        QMdiSubWindow.__init__(self, parent)
        
    def closeEvent(self):
        self.emit(SIGNAL("subWindowClosed()"))

class MSSettingsDialog(QDialog):
    """
    simplistic settings dialog
    
    """
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Settings...')
        self.setupUi()
    
    def setupUi(self):
        v=QVBoxLayout(self)
        tabWidget = QTabWidget(self)
        widget = QWidget()
        v_1 = QVBoxLayout()
        self.multiCore = QCheckBox("use all cpu available")
        self.multiCore.setChecked(QApplication.instance().multiCore)
        self.lowMemory = QCheckBox("reduce memory usage if possible(slowdown the application)")
        self.lowMemory.setChecked(QApplication.instance().lowMemory)        
        v_1.addWidget(self.multiCore)
        v_1.addWidget(self.lowMemory)
        widget.setLayout(v_1)
        tabWidget.addTab(widget, "Processing")
        v.addWidget(tabWidget)
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        widget_2 = QWidget()
        vert1 = QVBoxLayout()
        g = QGroupBox('PeakModelView')
        vert = QVBoxLayout()
        self.comparativeView = QRadioButton("Comparative View")
        self.treeView = QRadioButton("Samples View")
        self.basicView = QRadioButton("Peak attributes")
        for w in (self.comparativeView, self.treeView, self.basicView):        
            vert.addWidget(w)
        g.setLayout(vert)
        vert1.addWidget(g)
        widget_2.setLayout(vert1)
        tabWidget.addTab(widget_2, "Model")
        
        v.addWidget(self.buttonBox)


class MSPeriodicTable(QDialog):
    """
    Periodic Table showed when choosing new elements for calculation    
    """    
    
    def __init__(self, parent=None):
        
        QDialog.__init__(self, parent)

        # Set up the user interface from Designer.
        self.alpha=MSAlphabet.withElements([])
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.tableView.resizeRowsToContents()
        self.ui.tableView.resizeColumnsToContents()
            
        for attr in dir(self.ui):
            if attr.startswith('push'):
                self.connect(self.ui.__dict__[attr], SIGNAL('showInformationLabel'), self.timing)
                self.connect(self.ui.__dict__[attr], SIGNAL('clicked()'), self.ui.__dict__[attr].emitName)
                self.connect(self.ui.__dict__[attr], SIGNAL('returnElement'), self.returnEl)
        
        #elf.connect(self.ui.buttonBox, SIGNAL('accepted()'), self.returnEl)
        #self.connect(self.ui.buttonBox, SIGNAL('rejected()'), self.closeView)
                
    
    def closeView(self):
        self.close()
        
    
    
    def timing(self, t):
        self.timer=QTimer()
        self.timer.button=t
        self.timer.setSingleShot=True
        self.connect(self.timer, SIGNAL('timeout()'), self.retweet)
        #self.timer.timeout.connect(self.retweet)        
        self.timer.start(500)
        
    def retweet(self):
        t=self.timer.button
        if t.leaved:
            return
        e=self.alpha.element(str(t.text()))
        self.ui.label_6.setText(str(e.name))
        self.ui.label_7.setText(str(e.atomicNumber))
        self.ui.label_8.setText(str(e.massAv)[:7])
        self.ui.label_9.setText(str(e.massMo)[:7])
        model=QStandardItemModel(self)
        model.setHorizontalHeaderLabels(["Mass", "Prob"])
        i=0
        for m, p in zip(e.isomass, e.abundoncy):
            mass=QStandardItem(str(m)[:7])
            prob=QStandardItem(str(p)[:7])
            model.setItem(i,0,mass)
            model.setItem(i, 1, prob)
            i+=1
        self.ui.tableView.setModel(model)
        
    
    def returnEl(self, n):
        e=self.alpha.element(str(n))
        self.close()
        return e
        #self.done(1)




class MSStandardItem(QStandardItem):
    """
    Customized Item allowing to sort table with float value    
    
    """
    def __init__(self, string):
        QStandardItem.__init__(self, string)
    
    def __lt__(self, item):
        try:
            if float(self.text()) <float(item.text()):
                return True
            return False
        except ValueError:
            return QStandardItem.__lt__(self, item)




class MSPipelineToolBar(QToolBar, WithPointerToQApp):
    
    styleSheet="""QToolBar {
                         background: qlineargradient(x1: 0, y1:1, x2: 1, y2: 1,
                         stop: 0 #a6a6a6, stop: 0.08 #7f7f7f,
                         stop: 0.39999 #717171, stop: 0.4 #626262,
                         stop: 0.9 #4c4c4c, stop: 1 #333333);
                         spacing: 30px; /* spacing between items in the tool bar */
                         }
                 QToolButton {
                             color: white;                            
                             }
                 """
                 
    def __init__(self, string='', parent=None):
        QToolBar.__init__(self, string, parent)
        self.setStyleSheet(self.styleSheet)
        
        #self.setMaximumWidth(50)
        self.setIconSize(QSize(25, 25))
        self.setToolButtonStyle(3)
            
        self.addAction(QIcon(path.normcase("gui/icons/fileopen.png")), "Open")
        self.addAction(QIcon(path.normcase("gui/icons/peakicon.png")), "Peak Detection")
        self.addAction(QIcon(path.normcase("gui/icons/clustering.png")), "Clustering")
        self.addAction(QIcon(path.normcase("gui/icons/applications_science.png")), "Identification")
        self.addAction(QIcon(path.normcase("gui/icons/pathway.png")), "Pathway")
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.addWidget(spacer)        
        
        self.addAction(QIcon(path.normcase("gui/icons/exit.png")), "Exit")
        #self.addSeparator()
        for ac in self.actions():
            ac.setFont(QFont(self.qApp.font().rawName(), 7))
        
     
        self.actions()[0].triggered.connect(self.showOpenDialog)        
        self.actions()[1].triggered.connect(self.showIntAlgos)
        #self.actions()[2].triggered.connect(self.showClustAlgo)        
        self.connect(self.actions()[2], SIGNAL('triggered()'), self.showClustAlgo)
        self.actions()[3].triggered.connect(self.showIdAlgo)        
        self.actions()[4].triggered.connect(self.showPathwayAlgo)        
        #self.connect(self.actions()[6], SIGNAL('triggered()'), MSMenuController.quit)
        
        from controller.MetMenuBarControl import MSMenuController
        self.actions()[6].triggered.connect(MSMenuController.quit)

        self.intMenu=self.makeIntMenu()        
            
    def makeIntMenu(self):
        """
        create the Menu in __init__ of the toolbar
        """
        
        t=QToolBar(self)
        t.setStyleSheet("""border-radius: 10px;
                           border: 1px solid gray;
                           font:8px;
                           spacing:1px""")
            
           
        t.setToolButtonStyle(3)
        t.addAction(QIcon(path.normcase("gui/icons/RLogo.png")), "MatchFiltered")
        spacer = QWidget()
        spacer.setStyleSheet("border:0px;")
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        t.addWidget(spacer)   
        t.addAction(QIcon(path.normcase("gui/icons/RLogo.png")), "CentWave")        
        
        from gui.dialog.MetIntegrationGui import MSCentWaveDialog, MSMatchedFilteredDialog
        from controller.dialog.MetIntegrationControl import MSIntegrationController
        
        def match():
            integr = MSMatchedFilteredDialog(parent=self.qApp.view)
            integr.setAttribute(Qt.WA_DeleteOnClose)
            control = MSIntegrationController(self.qApp.model, integr, False)
            del control
                
        def cent():            
            integr = MSCentWaveDialog(parent=self.qApp.view)
            integr.setAttribute(Qt.WA_DeleteOnClose)
            control = MSIntegrationController(self.qApp.model, integr, False)
            del control
            
        self.connect(t.actions()[0], SIGNAL('triggered()'), match)
        self.connect(t.actions()[2], SIGNAL('triggered()'), cent)
                
        ctrlMenu = QtGui.QMenu()
       # self.ctrlMenu.CursorIn=False
        def leaveEvent(e):
            ctrlMenu.close()
        #ctrlMenu.leaveEvent=leaveEvent
        #self.ctrlMenu.enterEvent=enterEvent
        ctrlMenu.setStyleSheet("""background: qlineargradient(x1: 0, y1:0, x2: 1, y2: 1,
                                  stop: 0 #a6a6a6, stop: 0.08 #7f7f7f,
                                  stop: 0.39999 #717171, stop: 0.4 #626262,
                                  stop: 0.9 #4c4c4c, stop: 1 #333333);
                                  color: white;""")     
        
        menuAction = QtGui.QWidgetAction(ctrlMenu)
        s=QWidget()
        v=QVBoxLayout(s)
        textEdit=QTextEdit()
        textEdit.setStyleSheet("background: transparent;")
        textEdit.setReadOnly(True)
        text="""Instructions:\n
                Two algorithm for peak detection are available in metMS, they are both taken from the XCMS software, written in R:\n
                -MatchedFiltered: for all kind of MS\n
                -CentWave: adapted for High Resolution MS, in centroid, it offers better performance in this case than the MatchedFiltered algorithm\n
                We are working on a home made algorithm soonly available"""
        textEdit.setPlainText(text)
        v.addWidget(textEdit)
        v.addWidget(t)
        menuAction.setDefaultWidget(s)
        ctrlMenu.addAction(menuAction)
        return ctrlMenu
    
    def showPathwayAlgo(self):
        self.qApp.view.showInformationMessage("Not yet available", "still working on it!")
        
    def showIntAlgos(self):
        anim=QPropertyAnimation(self.intMenu, 'pos')
        anim.setDuration(200)
        p=QCursor.pos()
        anim.setStartValue(p)
        anim.setEndValue(QPoint(self.width(), p.y()))
        anim.start()
        self.intMenu.exec_()
        
    def showClustAlgo(self):
        from controller.dialog.MetClusteringControl import MSClusteringController
        from gui.dialog.MetClusteringGui import MSClusteringDialog
        
        clust = MSClusteringDialog(parent=self.qApp.view)
        clust.setAttribute(Qt.WA_DeleteOnClose)
        control=MSClusteringController(self.qApp.model, clust, False)
    
    def showIdAlgo(self):
        from controller.dialog.MetIdentificationControl import MSIdentificationController
        from gui.dialog.MetIdentificationGui import MSIdentificationDialog
        
        identif = MSIdentificationDialog(parent=self.qApp.view)
        identif.setAttribute(Qt.WA_DeleteOnClose)
        control = MSIdentificationController(self.qApp.model, identif, False)
        

    def showOpenDialog(self):
        from controller.dialog.MetVisualisationControl import MSVisualisationController
        from gui.dialog.MetVisualisationGui import MSVisualisationDialog
        
        dialog = MSVisualisationDialog(parent=self.qApp.view)
        dialog.setAttribute(Qt.WA_DeleteOnClose)
        control = MSVisualisationController(self.qApp.model, dialog, True)
        self.qApp.controllers[control] = None
        control.showView()


class MSView(QSplitter):
    """
    the ideal thing would be to list all possible signal
    
    """
    modifiedContext = pyqtSignal(object)     
    
    
    def __init__(self, widget, title="", parent=None):
        QSplitter.__init__(self, Qt.Vertical, parent)
        self.splitter = QSplitter(self)
        self.splitter.addWidget(widget)
        
        self.splitter.widget().sendingData.connect(self.signalEmission)

    
    
    def signalEmission(self, data):
        """propagation of the signal"""
        
        self.dataSelected.emit(data)




class MSSplashScreen(QSplashScreen):
    """
    custom splash screen for handling progress bar
    good to add an animation...    
    
    """    
    
    def __init__(self, pixmap, flag):    
        QSplashScreen.__init__(self, pixmap, flag)
        #pal= qApp.palette()
        #pal.setBrush(10, QColor.fromRgbF(1.,1.,1.,.1))
        #self.setPalette(pal)        
        #effect=QGraphicsBlurEffect()
        #effect.setBlurRadius(5)
        #effect.setBlurHints(5)
        #self.setGraphicsEffect(effect)
        self.pb = QProgressBar(self)
        self.pb.setTextVisible(False)
        #self.setOpacity(0.5)
        #print self.width(), self.height()
        self.pb.setGeometry(QRect(QPoint(0,self.height()-5), 
                            QPoint(self.width(), self.height())))
    
    def setValue(self,value):
        self.pb.setValue(value)







#===============================================================================
# TreeView and QTableView
#===============================================================================
class UpAndDownTableView(QTableView):
    """
    Mother class in Fact ?
    be inherited by QAbstractItemView ? subClass focus 
    
    """
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)
        self.setSelectionBehavior(1)#line selection
        self.setSelectionMode(1)#only one item can be selected at a time        
        self.setSortingEnabled(True)        
        self.horizontalHeader().setStretchLastSection(True)
        self.cursorIn = False
    
    def focusOutEvent(self, e):
        if self.cursorIn:
            self.setFocus()
    
    def enterEvent(self, e):
        self.cursorIn=True
    
    def leaveEvent(self, e):
        self.cursorIn=False
        self.clearFocus()


class MSAbstractItemView(QAbstractItemView):
    def __init__(self, parent=None):
        QAbstractItemView.__init__(self, parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setAcceptDrops(True)
        self.cursorIn = False
        self.contextMenu = QMenu()
    
    def focusOutEvent(self, e):
        """
        allow to keep the focus when changing selection and adding to the mdiArea
        
        """
        if self.cursorIn:
            self.setFocus()
    
    def enterEvent(self, e):
        self.cursorIn=True
    
    
    def leaveEvent(self, e):
        """
        deselect all item when the mouse cursor leave the treeView
        
        """
        self.cursorIn=False
        self.clearFocus()
    
    def deselectAll(self):
        if self.model() is None or self.selectionModel() is None or \
        not self.selectionModel().hasSelection():
            return
        selectedRows = self.selectionModel().selectedRows()
        for idx in reversed(sorted(selectedRows)):
            self.selectionModel().select(idx, QItemSelectionModel.Deselect)
        
    def removeSelected(self):
        """
        Public method to remove the selected entries.
        
        """
        if self.model() is None or self.selectionModel() is None or not self.selectionModel().hasSelection():
            print "no selection"
            return
        #print " pass the first test"
        selectedRows = self.selectionModel().selectedRows()
        for idx in reversed(sorted(selectedRows)):
            #print "before del"
            self.model().removeRow(idx.row(), idx.parent())
            #print "after del"
        
    
    def removeAll(self):
        """
        Public method to clear the view.
        
        """
        if self.model() is not None:
            self.model().removeRows(0, self.model().rowCount(self.rootIndex()), 
                                    self.rootIndex())
    
    #support for text and urls(file dragging) dragging
    def dragEnterEvent(self, e):
        if e.mimeData().hasText() or e.mimeData().hasUrls():
            e.acceptProposedAction()
            
    def dragMoveEvent(self, e):
        if e.mimeData().hasText() or e.mimeData().hasUrls():
            e.acceptProposedAction()
    
    
    def buildMenuActions(self):
        """
        method to override in subclass
        
        """
        pass
    
    def showContextMenu(self):
        self.buildMenuActions()
        if self.contextMenu is not None:# and self.contextMenu.actions():
            self.contextMenu.exec_(QCursor.pos())



        
        
class MSToDropTreeView(QTreeView, MSAbstractItemView):
    """
    Class implementing a tree view supporting removal of entries.
    
    """
    #changedLine=pyqtSignal(QModelIndex)
    #modelChanged=pyqtSignal(QModelIndex, model)   
    
    def __init__(self, parent=None):
        QTreeView.__init__(self, parent)
        MSAbstractItemView.__init__(self, parent)
        #self.verticalHeader = QHeaderView(Qt.Vertical)
        #self.setHeader(self.verticalHeader)
        self.header().setVisible(False)
        self.setExpandsOnDoubleClick(False)


    def keyPressEvent(self, evt):
        """
        Protected method implementing special key handling.
        @param evt reference to the event (QKeyEvent)
        TODO:bind the update models
        
        """
        QTreeView.keyPressEvent(self, evt)
        if evt.key() in (Qt.Key_Delete, Qt.Key_Backspace) and self.model() is not None:
            self.removeSelected()
        #we assume that we are in the cluster case
            #to update the current peak...
        self.emit(SIGNAL('changedLine'))    
        qApp.instance().dockControl.plotClusterSelection(self.selectedIndexes()[0], True)
                                            
    def buildMenuActions(self):
        """
        TODO: see we can construct only menu to avoid having to much instanciated menus
        
        """
        if not self.selectedIndexes():
            return
        index=self.selectedIndexes()[0]
        if not index.isValid():
            print "non valid index"
            return
        if index.data().toString() in ("fragments/adducts:","isotopic cluster:"):
            return
         
        self.contextMenu.clear()
        self.contextMenu.addAction('&Identification')
        self.connect(self.contextMenu.actions()[0], SIGNAL('triggered()'), qApp.instance().dockControl.identify)
        
        isAdduct = False
        if index.parent().data().toString() in ("fragments/adducts:","isotopic cluster:"):
            isAdduct = True
        data=index.data().toString()
        mass, rt = map(float, data.split('/')[:2])
        sample=qApp.instance().dockControl.currentSample[2]
        #if sample is None:
        #supposed to be always true    
        #    return
        peak=sample.peakAt(mass, rt)
        peaks=sample.mappedPeaks.peaksInRTRange(rt,  6.)
        #a=None            
        if not isAdduct:            
            a=QMenu("&Add Peak to cluster...", self.contextMenu)
            self.connect(a, SIGNAL('triggered(QAction*)'), qApp.instance().dockControl.addPeakToOneCluster)
            s=(str(peak),)
            for iso in peak.isoCluster + peak.fragCluster:
                s+=(str(iso),)
            for p in peaks:
                if not str(p) in s:#avoid to have the proposition of the same peak
                    a.addAction(str(p))
            self.contextMenu.addMenu(a)
        else:
            action = self.contextMenu.addAction("&Remove from cluster...")
            self.connect(action, SIGNAL('triggered()'), qApp.instance().dockControl.removePeakFromOneCluster)
    
    def dropEvent(self, e):
        sample = qApp.instance().model.sample(str(e.mimeData().text()), fullNameEntry=False)
        if sample is None:
            print "fatal error, blue screen coming soon...no i am kidding"
            return
        idx = 3
        MSDialogController.actualizeClusterModel(sample)
        qApp.instance().dockControl.setCurrentSample(sample, idx)
        self.update()
        

class MSToDropTableView(QTableView, MSAbstractItemView):
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)
        MSAbstractItemView.__init__(self, parent)
        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)

    
    def dropEvent(self, e):
        m = self.model()
        sample = qApp.instance().model.sample(str(e.mimeData().text()), fullNameEntry=False)
        if sample is None:
            print "fatal error, blue screen coming soon...no i am kidding"
            return
        idx = None
        if m == qApp.instance().view.spectraModel:
            #print "trying to actualize spectra model"
            qApp.instance().view.sampleDockWidget.cursor().setShape(Qt.WaitCursor)
            MSDialogController.actualizeSpectraModel(sample)
            qApp.instance().view.sampleDockWidget.cursor().setShape(Qt.ArrowCursor)
            idx = 1
        elif m == qApp.instance().view.peakModel:
            MSDialogController.actualizePeakModel(sample)
            idx = 2
       
        qApp.instance().dockControl.setCurrentSample(sample, idx)
        self.update()
    
    def keyPressEvent(self, evt):
        """
        Protected method implementing special key handling.
        @param evt reference to the event (QKeyEvent)
        TODO:bind the update models
        
        """
        QTableView.keyPressEvent(self, evt)
        if evt.key() in (Qt.Key_Delete, Qt.Key_Backspace) and self.model() is not None:
            self.removeSelected()
        if self is qApp.instance().view.treeView_2:
            #to update the current peak...
            self.emit(SIGNAL('changedLine'))

        m = self.model()
        if m == qApp.instance().view.spectraModel:
            qApp.instance().dockControl.plotSelection(self.selectedIndexes()[0], True)
        elif m == qApp.instance().view.peakModel:
            qApp.instance().dockControl.plotPeakSelection(self.selectedIndexes()[0], True)
    
    def buildMenuActions(self):
        if not self is qApp.instance().view.treeView_2:
            print "not treeView_2"
            return
        if not self.selectedIndexes():
            return
        index=self.selectedIndexes()[0]
        if not index.isValid():
            print "non valid index"
            return
        if index.data().toString() in ("fragments/adducts:","isotopic cluster:"):
            return
            
        self.contextMenu.clear()
        self.contextMenu.addAction('&Identification')
        self.connect(self.contextMenu.actions()[0], SIGNAL('triggered()'), qApp.instance().dockControl.identify)
        

    
class MSDragFromTableView(QTableView, MSAbstractItemView):
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)
        MSAbstractItemView.__init__(self, parent)
        self.setDragEnabled(True)
        self.poss = None
        self.idxHovered=None
        
    def enterEvent(self, e):
        MSAbstractItemView.enterEvent(self, e)
        self.setMouseTracking(True)
            
    def leaveEvent(self, e):
        MSAbstractItemView.leaveEvent(self, e)
        self.setMouseTracking(False)
        
    def mousePressEvent(self, event):
        if(event.button() == Qt.LeftButton):
            self.poss = event.pos()
        QTableView.mousePressEvent(self, event)

 
    def mouseMoveEvent(self, event):
        if(not event.buttons() and Qt.LeftButton):
            QTableView.mouseMoveEvent(self, event)
            idx = self.indexAt(event.pos())
            if idx.data().toString() != "":#when cursor on empty parts, find index !
                if self.idxHovered is not None:
                    self.emit(SIGNAL("disHighlightRequested(QModelIndex)"), self.idxHovered)
                self.idxHovered = idx
                self.emit(SIGNAL("highlightRequested(QModelIndex)"), idx)
            else:
                self.idxHovered = None
                self.emit(SIGNAL("noHighlightRequested()"))
        else:
            idx = self.indexAt(event.pos())
            t = idx.data().toString()
            if t != "":# and QPoint(event.pos()-self.poss).manhattanLength()>3:
                drag = QDrag(self)
                mimeData = QMimeData()
                mimeData.setText(t)
                drag.setMimeData(mimeData)
                drag.exec_()
            QTableView.mouseMoveEvent(self, event)
            
    def dropEvent(self, e):
        if not map(str, map(QUrl.toString, e.mimeData().urls())):
            return

        from controller.dialog.MetVisualisationControl import MSVisualisationController
        from gui.dialog.MetVisualisationGui import MSVisualisationDialog       
        view=MSVisualisationDialog(self.parent())
        controller=MSVisualisationController(qApp.instance().model, view, creation=True)
        files=[f[8:] for f in map(str, map(QUrl.toString, e.mimeData().urls()))]
        controller.selectedFiles=files
        view.lineEdit.setText(";".join(files))
        
    def buildMenuActions(self):
        self.contextMenu.clear()
        a = self.contextMenu.addAction(QIcon(path.normcase('gui/icons/color_fill.png')), '&Change Color')
        self.connect(a, SIGNAL('triggered()'), qApp.instance().dockControl.updateColor)           
        d = self.contextMenu.addAction(QIcon(path.normcase('gui/icons/delete.png')),'&Remove')
        self.connect(d, SIGNAL('triggered()'), qApp.instance().dockControl.removeSample)
        

class WhatToShowDialog(QDialog):
    """
    small class to be used in 
    MSmdiArea when drop in 
    
    """
    def __init__(self, sample, parent=None):
        self.sample = sample
        QDialog.__init__(self, parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("Drop options")
        v = QVBoxLayout(self)
        self.label = QLabel("Sample: %s"%self.sample.shortName())
        v.addWidget(self.label)
        self.tic = QRadioButton("Show tic", self)
        v.addWidget(self.tic)
        
        self.show3d = QRadioButton("Show in 3d", self)
        v.addWidget(self.show3d)        
        
        self.showSpectrogram = QRadioButton("Show spectrogram", self)
        v.addWidget(self.showSpectrogram)
        
        self.peakTable = QRadioButton("Show peak table", self)
        v.addWidget(self.peakTable)
        if not self.sample.rawPeaks:
            self.peakTable.setEnabled(False)
        
        self.clusterTable = QRadioButton("Show cluster table", self)
        v.addWidget(self.clusterTable)
        if not self.sample.mappedPeaks:
            self.clusterTable.setEnabled(False)
        
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        v.addWidget(self.buttons)
        
        
        
class MSMdiArea(QMdiArea):
    """
    Mdi Area in several windows mode
    
    """
    def __init__(self, parent=None):
        QMdiArea.__init__(self, parent)
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, e):
        #if e.mimeData().hasText() or e.mimeData().hasUrls():
        e.acceptProposedAction()
            
    def dragMoveEvent(self, e):
        #if e.mimeData().hasText() or e.mimeData().hasUrls():
        e.acceptProposedAction()
    
    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            #try:
            #print path.normcase(str(e.mimeData().urls()[0].toString()))[8:]
            #im = QImage(path.normcase(str(e.mimeData().urls()[0].toString()))[8:])
            #if im.isNull():
            #    QApplication.instance().view.showErrorMessage('Error', 'can not load image data ?')
            #    return
            pixmap = QPixmap(path.normcase(str(e.mimeData().urls()[0].toString()))[8:])            
            label = QLabel()
            label.setPixmap(pixmap)
            #label.show()
            QApplication.instance().view.addMdiSubWindow(label, "Image")
            #label.show()
            
            #except Exception:
            #    return
        elif e.mimeData().hasText():
            t = e.mimeData().text()
            #print t
            sample = QApplication.instance().model.sample(t, fullNameEntry=False)
            if sample is None:
                return
            d = WhatToShowDialog(sample)
            
            def showAppropriateStuff():
                tic = d.tic.isChecked()
                peakTable = d.peakTable.isChecked()
                clusterTable = d.clusterTable.isChecked()
                show3d = d.show3d.isChecked()
                spectrogram = d.showSpectrogram.isChecked()
                d.close()
                if tic:
                    title="TICS"
                    legend={'bottom':'RT(s)', 'left':'INTENSITY'}
                    flags='chroma'
                    canvas = MSQtCanvas([s.chroma[0] for s in qApp.instance().model], 
                                         title=title, labels=legend, flags=flags)
                    canvas.connect(qApp.instance(), SIGNAL('redraw()'), canvas.redraw) 
                    QApplication.instance().view.addMdiSubWindow(canvas)
                if peakTable:
                    canvas=QTableView()
                    canvas.horizontalHeader().setStretchLastSection(True)
                    canvas.setSortingEnabled(True)
                    model=MSDialogController.getSampleModel(self.sample, flags='peak')
                    canvas.setModel(model)
                    QApplication.instance().view.addMdiSubWindow(canvas)
                if clusterTable:
                    canvas=QTableView()
                    canvas.horizontalHeader().setStretchLastSection(True)
                    canvas.setSortingEnabled(True)
                    model=MSDialogController.getSampleModel(self.sample, flags='cluster')
                    canvas.setModel(model)
                    QApplication.instance().view.addMdiSubWindow(canvas)
                if show3d:
                    qApp.instance().menuControl.show3DView()
                if spectrogram:
                    qApp.instance().menuControl.showSpectrogramView()
                                                
            self.connect(d.buttons, SIGNAL('accepted()'), showAppropriateStuff)
            self.connect(d.buttons, SIGNAL('rejected()'), d.close)            
            d.exec_()

from controller.MetBaseControl import MSBaseController
class MSTreeItemDelegate(QItemDelegate, MSBaseController):
    """Special class for drawing colored cells in the table view"""

    def __init__(self, model, parent=None):
        """Constructor, empty just want to define paintEvent method"""
        
        QItemDelegate.__init__(self, parent)
        self.model = model
    
    
    def getColor(self, xmlfile, painter, option):
        c = self.model.sample(xmlfile).color
        color =QColor()
        color.setRedF(c[0]); color.setGreenF(c[1]); color.setBlueF(c[2])
        painter.setPen(color)#c[0],c[1],c[2]))
        painter.setOpacity(.2)
        #painter.drawRect(option.rect)
        painter.fillRect(option.rect, color)
        painter.setPen(Qt.black)
        painter.setOpacity(1.)
    
    def paint(self,  painter, option, index):
       
        xmlfile=self.fullXmlPath(index.model().data(index, Qt.DisplayRole).toString())
        i = index.parent()        
        while not xmlfile and i:
            xmlfile = self.fullXmlPath(index.model().data(i, Qt.DisplayRole).toString())
            i= i.parent()
       #c[0],c[1],c[2]))
        self.getColor(xmlfile, painter, option)
          
        text = index.data(Qt.DisplayRole).toString()
        painter.drawText(option.rect, Qt.AlignLeft, text)




class MSTableView(QWidget):
    
    s = ("Peaks found", "Peaks with isotopic cluster", 
         "Peaks with fragment/adduct cluster",
         "Peaks with high correlation values inter_sample")
         
    def __init__(self, tableView, **kwargs):
        if 'parent' in kwargs:
            QWidget.__init__(self, kwargs['parent'])
        else:QWidget.__init__(self)
        
        self.tableView = tableView
        self.tableView.setParent(self)
        self.tableView.setSortingEnabled(True)
        self.tableView.resizeColumnsToContents()

        if 'model' in kwargs:
            self.model=kwargs['model']
            self.tableView.setModel(self.model)
        self.selectionEnabled = kwargs.get("selection")
        
        self.button = QPushButton('export to CSV',self)
        self._setupGui()
        self._buildConnections()
        self.computeSelection()

    
    #@ckeck(QAbstractItemModel)
    def setModel(self, model):
        self.tableView.setModel(model)


    def _setupGui(self):
        vl = QVBoxLayout(self)
        if self.selectionEnabled:
            hl = QHBoxLayout()
            hl.addWidget(QLabel("Highlight:"))
            self.comboBox = QComboBox(self)
            self.comboBox.addItems(self.s)
            hl.addWidget(self.comboBox)
            self.go = QPushButton("Go...", self)
            hl.addWidget(self.go)
            vl.addLayout(hl)
        vl.addWidget(self.tableView)
        hl = QHBoxLayout()
        hl.addWidget(self.button)
        #hl.addSpacer(QSpacer(20,40))
        vl.addLayout(hl)
        #self.setLayout(vl)
        
    
    def _buildConnections(self):
        self.connect(self.button, SIGNAL('clicked()'), self._export)
        try:        
            self.connect(self.go, SIGNAL('clicked()'), self.computeSelection)
        except AttributeError:pass

    def _export(self):
        fileName = QFileDialog.getSaveFileName(self, 'Save File', '.', '(*.csv, *.tsv)')
        if fileName:
            end = fileName.split('.')[-1]
            if end == 'csv':
                sep =';'
            elif end == 'tsv':
                sep='\t'
            else:
                sep=';'
            self._write(fileName, sep)
    
    
    def _write(self, *args):
        with open(args[0], 'w')as f:
            model = self.tableView.model()
            result =''
            for i in xrange (len(model.rowCount())):
                for j in xrange(len(model.columnCount())):
                    result+=model.index(i,j).data.toString()
                    if j < len(model.columnCount()):                    
                        result+=args[1].join(['\n'])
            f.write(result)
    
                
    def computeSelection(self):
        """will redraw the entire table using an itemdelegate"""
        threshold = str(self.comboBox.currentText())
        index_list =[]
        if threshold == "Peaks found":
            for i in xrange(self.model.rowCount()):
                if self.model.item(i, 5):
                    data = self.model.item(i, 5).data(Qt.DisplayRole).toString()
                    list_index =[]
                    if  data != "Not Found" and data !="":
                        for  j in xrange(self.model.columnCount()):
                            list_index.append(self.model.indexFromItem(self.model.item(i, j)))
                    index_list.extend(list_index)
                    
        elif threshold == "Peaks with isotopic cluster":
            transition_list = self.model.get_peak_list().as_trans_list()
            for i in xrange(self.model.rowCount()):
                if self.model.item(i, 1):
                    data = self.model.item(i, 1).data(Qt.DisplayRole).toString()
                    if data in transition_list:
                        for j in xrange(self.model.columnCount()):
                            index_list.append(self.model.indexFromItem(self.model.item(i, j)))
                            
        elif threshold == "Peaks with fragment/adduct cluster":
            for i in xrange(self.model.rowCount()):
                if self.model.item(i, 1) and self.model.item(i, 0):
                    data = self.model.item(i, 1).data(Qt.DisplayRole).toString()
                    rt = self.model.item(i, 0).data(Qt.DisplayRole).toString()
                    peak =self.model.get_peak_list().is_peak(float(data)-self.charge, float(rt))
                    if peak and len(peak.get_frag_cluster()):
                        for j in xrange(self.model.columnCount()):
                            index_list.append(self.model.indexFromItem(self.model.item(i, j)))
        
        
        elif threshold == "Peaks with high correlation values inter_sample":
            for i in xrange(self.model.rowCount()):
                if self.model.item(i, 1) and self.model.item(i, 0):
                    data = self.model.item(i, 1).data(Qt.DisplayRole).toString()
                    rt = self.model.item(i, 0).data(Qt.DisplayRole).toString()
                    peak =self.model.get_peak_list().is_peak(float(data)-self.charge, float(rt))
                    if peak and peak.get_frag_cluster().get_inter_corr() !="NA":
                        if peak.get_frag_cluster().get_inter_corr() > 0.5:
                            for j in xrange(self.model.columnCount()):
                                index_list.append(self.model.indexFromItem(self.model.item(i, j)))
                    
        delegate = SimpleDelegate(index_list, self.tableView)
        self.tableView.setItemDelegate(delegate)
        self.tableView.repaint()


class SimpleDelegate(QItemDelegate):
    """
    Special class for drawing colored cells in the table view
    
    """
    def __init__(self, index_list, parent=None):
        """Constructor, empty just want to define paintEvent method"""
        
        QStyledItemDelegate.__init__(self, parent)
        self.indexes = index_list
        
    def paint(self,  painter, option, index):
        """have to be reimplemented"""
        
        if index in self.indexes:
            painter.setPen(QColor(Qt.green))
            painter.setOpacity(.5)
            painter.drawRect(option.rect)
            painter.fillRect(option.rect, QColor(Qt.green))
        else:
            painter.setPen(QColor(Qt.red))
            painter.setOpacity(.5)
            painter.drawRect(option.rect)
            painter.fillRect(option.rect, QColor(Qt.red))
        
        if index.isValid():
            painter.setPen(QColor(Qt.black))
            text = index.data(Qt.DisplayRole).toString()
            painter.drawText(option.rect, Qt.AlignLeft, text)
    

class NoSelectionError(Exception):
    """
    idea cause i use print stuff like no selection several times
    
    """
    pass


class MSCompoundTreeView(QWidget):
    filenames = {'./config/databases/metaboliteMass.txt':('\t', 2, 0)}#'./config/databases/KNOWNS.csv',
    charges = {"None":0., "+H":1.0072277, "+Na":22.98992, "-H":-1.0072277}
    #delimiter character, number of the name columns, name of the mass columns
    #counting from zero
    METEXPLORE_DB = 'config/databases/metexplore.sqlite'
    def __init__(self, parent=None, **kwargs):
        QWidget.__init__(self, parent)
        
        a=QToolBar(parent=self)
        a.addWidget(QLabel('Select :'))
        self.compound=QLineEdit(self)
        a.addWidget(self.compound)
        self.charge = QComboBox(self)
        self.charge.addItems(self.charges.keys())
        a.addWidget(self.charge)
        
        v=QVBoxLayout(self)
        v.addWidget(a)
        self.comboBox=QComboBox(self)
        conn=sqlite3.connect(self.METEXPLORE_DB)        
        self.c=conn.cursor()
        self.c.execute('select * from  Organism ')
        self.comboBox.addItems([r[1] for r in self.c])
        v.addWidget(self.comboBox)        
            
        self.listView = UpAndDownTableView(self)#QTableView(parent=self)
        self.listView.verticalHeader().setDefaultSectionSize(20)
        self.listView.setSelectionBehavior(1)
        self.listView.keyPressEvent = self.showEIC
        self.connect(self.listView, SIGNAL('doubleClicked(const QModelIndex &)'), self.plot)
        v.addWidget(self.listView)

        self.model=None
        self.data=None        
        self._buildModel(self.comboBox.currentText())
        
        self.connect(self, SIGNAL('activated(const QModelIndex &)'), self.writeOn)
        self.connect(self.compound, SIGNAL('returnPressed()'), self.selectAndScrollToItem)
        self.connect(self.comboBox, SIGNAL('currentIndexChanged(const QString &)'), self._buildModel)
    
    
    def selectAndScrollToItem(self):
        t=self.compound.text()
        is_float=False
        try:
            val=float(t)
            is_float=True
        except ValueError:
            pass
        if not is_float:
            for i in xrange(self.model.rowCount()):
                index=self.model.index(i, 0)
                if index.data().toString()==t:
                    self.listView.scrollTo(index, 1)
                    self.listView.selectRow(i)
        else:
            from graphics.MetMplCanvas import MSQtCanvas
            val += self.charges[str(self.charge.currentText())]
            samples= [spl for spl in QApplication.instance().model if spl.checked]
            chromas= [spl.massExtraction(val) for spl in samples]
            title="EIC@%s"%str(val)
            legend={'bottom':'rt', 'left':'INTENSITY'}
            pw = MSQtCanvas(chromas, title, labels=legend)
            self.connect(qApp.instance(), SIGNAL('redraw'), pw.redraw)
            pw.setPixmapVisibility(True)
            QApplication.instance().view.addMdiSubWindow(pw, title)
            
    
    def showEIC(self, e):
        QTableView.keyPressEvent(self.listView, e)
        if not self.listView.selectedIndexes():
            print "no selection error"
        self.plot(self.listView.selectedIndexes()[0])
      
    
    def plot(self, index):#, bool_=False):
        """
        why not use dockWidget control ?
        
        """
        r=index.row()
        c=index.column()
        mass = float(self.listView.model().index(r, c+2).data().toString())
        chroma=[]
        mass += self.charges[str(self.charge.currentText())]
        for spl in QApplication.instance().model:
            if spl.checked:
                c=spl.massExtraction(mass)
                chroma.append(c)
        pw=MSQtCanvas(chroma, "chroma@%s"%str(mass))
        self.connect(qApp.instance(), SIGNAL('redraw'), pw.redraw)
        pw.setPixmapVisibility(True) #force to show peaks
        a = qApp.instance().view.mdiArea.activeSubWindow()
        if a is not None:
            w = a.widget()
            import sip
            sip.delete(w)
            a.setWidget(pw)
        else:
            #isMax = True if a.isMaximized() else False 
            qApp.instance().view.addMdiSubWindow(pw, 'EIC@%f'%mass)
        #if a is not None and not bool_:
        qApp.instance().view.mdiArea.tileSubWindows()
    
    
    def loadCompounds(self, filename):
        """
        import csv
        reader=csv.reader(open(filename), delimiter=self.filenames[filename][0])
        return [row for row in reader]
        
        """
        self.setCursor(QCursor(3))
        self.c.execute('select * from Metabolite, MetaboliteInBioSource, BioSource, Organism where\
                        Metabolite.id=MetaboliteInBioSource.idMetabolite and \
                        MetaboliteInBioSource.idBioSource=BioSource.id and \
                        BioSource.idOrg=Organism.id and \
                        Organism.name="'+str(filename)+'"')
        self.setCursor(QCursor(0))
           
    
    def getFullName(self, end):
        for element in self.filenames:
            if element.split('/')[-1]==end:return element
        return None
    
    def _buildModel(self, string):
        #fullname=self.getFullName(string)
        self.loadCompounds(string)
        self.model = QStandardItemModel(self)
        
        completer=[]#QStringList()
        i=0        
        for c in sorted(self.c, key=lambda x:x[5]):
            if str(c[5])=='0' or str(c[2])=='NA':
                continue
            name = QStandardItem(str(c[1]))
            name.setEditable(False)
            self.model.setItem(i, 0, name)
            completer.append(str(c[1]))
            
            f=QStandardItem(str(c[2]))
            f.setEditable(False)
            self.model.setItem(i, 1, f)
            
            mz=MSStandardItem(str(c[5]))
            mz.setEditable(False)
            self.model.setItem(i, 2, mz)
            i+=1
            
        self.compound.setCompleter(QCompleter(completer))#[d[self.filenames[fullname][1]] for d in self.data]))
        self.listView.setModel(self.model)
    
    def writeOn(self, index):
        if self.acSubWindow is None: 
            return
        rt = float(index.data().toString().split(',')[-1])
        r = rt*60.
        mplcanvas=self.acSubWindow.widget().mainWidget
        line=QGraphicsLineItem(r, 0, r, 1e9, scene=mplcanvas.pw.scene())
        pen=QPen(Qt.blue,2)
        line.setPen(pen)
        mplcanvas.pw.addItem(line)
        mplcanvas.pw.scene().update()




from core.MetDataObjects import MSFormula, MSAlphabet
class MSIsoCalculator(QWidget):
    
    elementsFile = path.normcase("config/config/elements.xml")
    charges ={"+H":1.00794, "-H":-1.00794, "None":0.}
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.qApp=QApplication.instance()
        #self.data ={"C":"1-40", "H":"1-80", "N":"0-20", "O": "1-40","P":"0-5", "S":"0-5"}
        self.setupUi()
        #self.listView.setFocusPolicy(Qt.StrongFocus)
        self.acSubWindow=None
        
        self.alpha = MSAlphabet.withElements(elements=[])#el.parsing()
        #self.connect(self.listView, SIGNAL("doubleClicked(const QModelIndex &)"), self.showSpectra)
        self.connect(self.formula, SIGNAL("textChanged(const QString &)"), self.isoCalc)
        self.connect(self.deltam, SIGNAL("valueChanged(double)"), self.isoCalc)
        self.connect(self.minprob, SIGNAL("valueChanged(double)"), self.isoCalc)
        self.connect(self.parent().mdiArea, SIGNAL('subWindowActivated (QMdiSubWindow *)'), self.updateAcSubWindow)

    
    def updateAcSubWindow(self, sub):
        self.acSubWindow = sub    
        
    def setupUi(self):
        V = QVBoxLayout(self)
        gb = QGroupBox("Isotopic distribution")
       
        self.formula =QLineEdit(self)
        self.formula.setMinimumSize(QSize(100,20))
        self.deltam = QDoubleSpinBox(self)
        self.deltam.setValue(10)
        self.charge = QComboBox(self)
        self.charge.addItems(self.charges.keys())
        
        self.minprob=QDoubleSpinBox(self)
        self.minprob.setDecimals(2)
        
        self.calcEic=QCheckBox('show EIC',self)
        self.calcEic.setChecked(True)
        self.showGauss=QCheckBox('show peaks', self)        
        self.showGauss.setChecked(False)        
        
        self.massAvg=QLabel(self)
        #self.massAvg.setMaximum(1000.)
        self.massMono=QLabel(self)#QDoubleSpinBox(self)        
        #self.massMono.setMaximum(1000.)
        
        self.listView=UpAndDownTableView(self)    
        self.listView.verticalHeader().setDefaultSectionSize(20)
        self.listView.setSelectionBehavior(1)            
        self.connect(self.listView, 
                     SIGNAL('doubleClicked(const QModelIndex &)'),
                     self.plot)
        self.listView.keyPressEvent = self.showSpectra
        #self.listView.setGridStyle(Qt.NoPen)
        
        f = QFormLayout()
        f.addRow("formula:", self.formula)
        f.addRow("ppm:", self.deltam)
        f.addRow("charge", self.charge)
        f.addRow("minProb (10-6):", self.minprob)
        f.addRow("Mass average:", self.massAvg)
        f.addRow("Mass Monoistopic:", self.massMono)
        f.addRow(self.calcEic, self.showGauss)
        
        gb.setLayout(f)
        V.addWidget(gb)
        V.addWidget(self.listView)
        
        
    def showSpectra(self, e):
        """
        to check again
        
        """
        QTableView.keyPressEvent(self.listView, e)
        if not self.listView.selectedIndexes():
            print "no selection !"
            return
        self.plot(self.listView.selectedIndexes()[0], True)
        
    def plot(self, index):
        if not index.isValid():
            print "index not valid"
            return
            
        from core.MetObjects import MSAbstractTypes
        from core.MetObjects import MSChromatogram
        #from numpy import round
        
        mass = index.data().toString()
        prob = self.listView.model().index(index.row(), index.column()+1).data().toString()
        mass=round(float(mass), decimals=4)
        prob=round(float(prob), decimals=4)
        mass += self.charges[str(self.charge.currentText())]
        chroma, gauss=[], []
        if self.calcEic.isChecked():
            for spl in self.qApp.model:
                if spl.checked:
                    c=spl.massExtraction(mass)#massExtractionBisectAlgo(spl, mass)
                    chroma.append(c)
        
        if self.showGauss.isChecked():
            #intensity=QInputDialog.getInt(self, 'Value Requested', 'Please enter an intensity value', min=0)
            m=self.listView.model()  
            indexes=[]            
            for i in xrange(m.rowCount()):
                indexes.append((m.index(i, 0).data().toFloat()[0], 
                                m.index(i, 1).data().toFloat()[0]))
            for mass, prob in indexes:
                x,y=MSAbstractTypes.makeGaussianPeak(mass, prob)
                gauss.append(MSChromatogram(x_data=x, y_data=y))
                
        pw = MSQtCanvas(chroma+gauss, "chroma@%s"%str(mass))
        pw.setPixmapVisibility(True)
        a = qApp.instance().view.mdiArea.activeSubWindow()
        if a is not None:
            w = a.widget()
            import sip
            sip.delete(w)
            a.setWidget(pw)
        else:
            self.qApp.view.addMdiSubWindow(pw, title='EIC')
        qApp.instance().view.mdiArea.tileSubWindows()
    
    
    def isoCalc(self, string):
        if isinstance(string, QtCore.QString):
            if not str(string).endswith('.'):
                return
           
        #from graphics.MetMplCanvas import MSQtCanvas
        from core import MetDataObjects
        from utils.misc import IceAndFire2
        #from core.MetProcessing import isoPatternCalculation, resolutionAdjustment
        #from core.MetObjects import MSSpectrum        
        #from core.MetIdentification import MSIdentificationModel
        formula = MSFormula(str(self.formula.text()), alphabet=self.alpha)
        self.massAvg.setText(str(round(formula.calcMass(average=True),4)))
        self.massMono.setText(str(round(formula.calcMass(), 4)))
        ppm= self.deltam.value()*formula.calcMass()/1e6
        minprob = self.minprob.value()/1e6
        MetDataObjects.limitp=minprob
        adjustmass= formula.patternGeneration(ppm)#isoPatternCalculation(formula)
        #adjustmass = resolutionAdjustment(mp, ppm)        
      
        model=QStandardItemModel()
        model.setHorizontalHeaderLabels(['mass', 'prob'])        
        i=0        
        for m, p in adjustmass:
            mass=QStandardItem(str(round(m, 4)))
            mass.setBackground(QBrush(IceAndFire2._get_color(p, asQColor=True)))
            mass.setEditable(False)
            
            prob=MSStandardItem(str(round(p, 4)))
            prob.setBackground(QBrush(IceAndFire2._get_color(p, asQColor=True)))
            prob.setEditable(False)
            
            model.setItem(i, 0, mass)
            model.setItem(i, 1, prob)
            i+=1
            #x_data.append(m);y_data.append(p)
        lastmodel=self.listView.model()
        if lastmodel:del lastmodel
        self.listView.setModel(model)
        #print x_data, y_data
        #QApplication.instance().view.addMdiSubWindow(MSQtCanvas([MSSpectrum(x_data=x_data, y_data=y_data)], "isotopic calc", flags='spectrum'))




class FormulaGenerator(QWidget):
    elementsFile = path.normcase("config/config/elements.xml")
    charges ={"+H":1.00794, "-H":-1.00794, "None":0.}
    
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.qApp=QApplication.instance()
        self.data ={"C":"1-40", "H":"1-80", "N":"0-20", "O": "1-40","P":"0-5", "S":"0-5"}
        self.setupUi()
        #self.listView.setFocusPolicy(Qt.StrongFocus)
        self.acSubWindow=None
        
        self.alpha = MSAlphabet.withElements()#el.parsing()
        self.connect(self.comp, SIGNAL("clicked()"), self.formulaCalc)
        
        self.connect(self.parent().mdiArea, 
                     SIGNAL('subWindowActivated (QMdiSubWindow *)'), 
                     self.updateAcSubWindow)
   
    
    def setupUi(self):
        V=QVBoxLayout(self)
        gl = QGroupBox("Formula Generator")
        f3 = QFormLayout()
        self.mass = QDoubleSpinBox(self)
        self.mass.setMaximum(1000.)
        self.mass.setDecimals(4)
        self.charge= QComboBox()
        self.charge.addItems(self.charges.keys())
        self.ppm = QDoubleSpinBox(self)
        self.ppm.setValue(10.)
        self.comp = QPushButton("Compute")
        self.tableView=QTableView(self)
        self.tableView.verticalHeader().setDefaultSectionSize(20)
        self.tableView.setSortingEnabled(True)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        #self.tableView.verticalHeader().setStretchLastSection(True)
        f3.addRow("mass:", self.mass)
        f3.addRow("charge:", self.charge)
        f3.addRow("ppm:", self.ppm)
        f3.addRow("", self.comp)
        gl.setLayout(f3)
        V.addWidget(gl)
        V.addWidget(self.tableView)
        
    def formulaCalc(self):
        """call to the C++ Class FormulaGenerator"""
        
        from core.generator import MSFormulaGenerator
        from numpy import round
        from utils.misc import IceAndFire

        
        mass = self.mass.value()
        charge = self.charges[str(self.charge.currentText())]
        ppm = self.ppm.value()
        line =""
        for key in sorted(self.data): #by alphabetical order
            sub = str(key)+" "+str(self.data[key])+" "
            line+=sub
        gen=MSFormulaGenerator(mass+charge, ppm, line)
        formulas=gen.do_calculations()
        diff=gen.getMassDifference()
        table = QStandardItemModel()
        table.setHorizontalHeaderLabels(["formula", "mass difference"])
        for i, f in enumerate(formulas):
            m=((mass+charge)*ppm)/1e6#max difference
                        
            color=IceAndFire._get_color(abs(diff[i]/m), asQColor=True)
            form=QStandardItem(str(f))
            form.setBackground(QBrush(color))
            diffe=QStandardItem(str(round(diff[i], decimals=4)))
            diffe.setBackground(QBrush(color))
            table.setItem(i, 0, form)
            table.setItem(i, 1, diffe)
        self.tableView.setModel(table)
        
    def updateAcSubWindow(self, sub):
        self.acSubWindow = sub  

import os.path as op

from PyQt4 import QtCore, QtGui, QtWebKit
#from PyQt4.QtCore import Qt
#===============================================================================
# WEB BROWSER CODE
#===============================================================================
class WebTab(QtGui.QWidget):
    """class for handling tab"""
    
    def __init__(self, url="http://www.google.fr", parent =None):
        """Constructor"""
        
        QtGui.QWidget.__init__(self, parent)
        vb = QtGui.QVBoxLayout(self)
        self.webview = QtWebKit.QWebView()
        self.true_url = QtCore.QUrl(url)
        self.webview.setUrl(self.true_url)
        vb.addWidget(self.webview)
        

class MSWebBrowser(QtGui.QWidget):
    
    def __init__(self, url="http://www.google.fr", parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.first_url = url
        self._setupUi()
        self._buildConnections()
        # set the default
        
        self.url.setText(self.first_url)#print only url on the line edit        
        self.tabWidget.currentWidget().webview.setUrl(QtCore.QUrl(self.first_url)) # load page
        self.back.setEnabled(False)# history buttons:
        self.next.setEnabled(False)        
    
    def _setupUi(self):
        self.resize(600, 400)
        verticalLayout = QtGui.QVBoxLayout(self)
        horizontalLayout = QtGui.QHBoxLayout()
        self.back = QtGui.QPushButton(self)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(op.normcase("gui/icons/back.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.back.setIcon(icon)
        horizontalLayout.addWidget(self.back)
        self.next = QtGui.QPushButton(self)
        self.next.setEnabled(True)
        self.next.setLayoutDirection(QtCore.Qt.RightToLeft)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(op.normcase("gui/icons/next.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.next.setIcon(icon1)
        horizontalLayout.addWidget(self.next)
        self.stop = QtGui.QPushButton(self)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(op.normcase("gui/icons/stop.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.stop.setIcon(icon2)
        horizontalLayout.addWidget(self.stop)
        self.reload = QtGui.QPushButton(self)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(op.normcase("gui/icons/reload.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.reload.setIcon(icon3)
        horizontalLayout.addWidget(self.reload)
        self.home = QtGui.QPushButton(self)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(op.normcase("gui/icons/home.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.home.setIcon(icon5)
        horizontalLayout.addWidget(self.home)
        self.cytoscape = QtGui.QPushButton(self)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(op.normcase("gui/icons/cytoscape.jpeg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.cytoscape.setIcon(icon4)
        horizontalLayout.addWidget(self.cytoscape)        
        self.url = QtGui.QLineEdit(self)
        horizontalLayout.addWidget(self.url)
        self.pb = QtGui.QProgressBar(self)
        horizontalLayout.addWidget(self.pb)
        verticalLayout.addLayout(horizontalLayout)
        

        self.tabWidget = QtGui.QTabWidget()
        self.tabWidget.setTabsClosable(True)
        tab = WebTab(self.first_url, parent=self.tabWidget)
        self.tabWidget.addTab(tab, tab.webview.url().toString().split('.')[1])
        self._buildTabConnections(tab)
        verticalLayout.addWidget(self.tabWidget)
        
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Plus:
            tab = WebTab(parent=self.tabWidget)
            self._buildTabConnections(tab)
            self.tabWidget.addTab(tab, tab.webview.url().toString().split('.')[1])
            self.tabWidget.setCurrentWidget(tab)
     
     
    def _buildConnections(self):
        self.connect(self.back,QtCore.SIGNAL("clicked()"), self.back_)
        self.connect(self.next,QtCore.SIGNAL("clicked()"), self.next_)
        self.connect(self.url,QtCore.SIGNAL("returnPressed()"), self.url_changed)
        self.connect(self.reload,QtCore.SIGNAL("clicked()"), self.reload_page)
        self.connect(self.stop,QtCore.SIGNAL("clicked()"), self.stop_page)
        self.connect(self.home,QtCore.SIGNAL("clicked()"), self.home_)
        self.connect(self.tabWidget, QtCore.SIGNAL("tabCloseRequested(int)"),self.tabWidget.removeTab)
        self.connect(self.cytoscape, QtCore.SIGNAL("clicked()"), self.load_cytoscape)
    
    def _buildTabConnections(self, tab):
        tab.webview.settings().setAttribute(QtWebKit.QWebSettings.PluginsEnabled, True)
        tab.webview.settings().setAttribute(QtWebKit.QWebSettings.JavascriptEnabled, True)
        tab.webview.settings().setAttribute(QtWebKit.QWebSettings.JavascriptCanOpenWindows, True)
        tab.webview.settings().setAttribute(QtWebKit.QWebSettings.JavascriptCanAccessClipboard, True)
        self.connect(tab.webview,QtCore.SIGNAL("linkClicked (const QUrl&)"), self.link_clicked)
        self.connect(tab.webview,QtCore.SIGNAL("urlChanged (const QUrl&)"), self.link_clicked)
        self.connect(tab.webview,QtCore.SIGNAL("loadProgress (int)"), self.load_progress)
        self.connect(tab.webview,QtCore.SIGNAL("titleChanged (const QString&)"), self.title_changed)

    def load_cytoscape(self):
        """
        String represents the graph which is going to be drawn
        """
        self.tabWidget.currentWidget().webview.load(QtCore.QUrl("cytoscape_web/test.html"))
    
    def load(self, string):
        self.tabWidget.currentWidget().webview.load(QtCore.QUrl(string))
            
    def home_(self):
        self.tabWidget.currentWidget().webview.setUrl(QtCore.QUrl(self.first_url))
        
    def url_changed(self):
        """Url have been changed by user"""
        page = self.tabWidget.currentWidget().webview.page()
        history = page.history()
        if history.canGoBack():
            self.back.setEnabled(True)
        else:
            self.back.setEnabled(False)
        if history.canGoForward():
            self.next.setEnabled(True)
        else:
            self.next.setEnabled(False)
        
        url = self.url.text()
        self.tabWidget.currentWidget().webview.setUrl(QtCore.QUrl(url))
        
    def stop_page(self):
        """Stop loading the page"""
        self.tabWidget.currentWidget().webview.stop()
    
    def title_changed(self, title):
        """Web page title changed - change the tab name"""
        self.tabWidget.setTabText(self.tabWidget.currentIndex(), title)
        #self.setWindowTitle(title)
    
    def reload_page(self):
        """Reload the web page"""
        self.tabWidget.currentWidget().webview.setUrl(QtCore.QUrl(self.url.text()))
    
    def link_clicked(self, url):
        """Update the URL if a link on a web page is clicked"""
        page = self.tabWidget.currentWidget().webview.page()
        history = page.history()
        if history.canGoBack():
            self.back.setEnabled(True)
        else:
            self.back.setEnabled(False)
        if history.canGoForward():
            self.next.setEnabled(True)
        else:
            self.next.setEnabled(False)
        
        self.url.setText(url.toString())
    
    def load_progress(self, load):
        """Page load progress"""
        self.pb.setValue(load)
        if load == 100:
            self.stop.setEnabled(False)
            self.pb.setValue(0)
        else:
            self.stop.setEnabled(True)
        
    def back_(self):
        """Back button clicked, go one page back"""
        page = self.tabWidget.currentWidget().webview.page()
        history = page.history()
        history.back()
        if history.canGoBack():
            self.back.setEnabled(True)
        else:
            self.back.setEnabled(False)
    
    def next_(self):
        """Next button clicked, go to next page"""
        page = self.tabWidget.currentWidget().webview.page()
        history = page.history()
        history.forward()
        if history.canGoForward():
            self.next.setEnabled(True)
        else:
            self.next.setEnabled(False)        
        