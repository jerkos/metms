#!/usr/bin/python
# -*- coding: utf-8 -*-

#author:Marco

import os.path as path#, sys
import cPickle
from copy import deepcopy
import csv
import numpy as np

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import SIGNAL, QObject, Qt, QThread#, pyqtSlot
from PyQt4.QtGui import QFileDialog, QInputDialog, QApplication, QMessageBox, QStandardItem, qApp
#from numpy import array

from controller.MetBaseControl import MSBaseController, ChoosenOne, MSDialogController
from controller.dialog.MetVisualisationControl import MSVisualisationController
from controller.dialog.MetIntegrationControl import MSIntegrationController
from controller.dialog.MetClusteringControl import MSClusteringController
from controller.dialog.MetIdentificationControl import MSIdentificationController
#from controller.dialog.MetConversionControl import MSConversionController 

from gui.dialog.MetVisualisationGui import MSVisualisationDialog
from gui.dialog.MetIntegrationGui import MSMatchedFilteredDialog, MSCentWaveDialog
from gui.dialog.MetIdentificationGui import MSIdentificationDialog
from gui.dialog.MetClusteringGui import MSClusteringDialog
#from gui.dialog.MetConversionGui import MSConversionDialog
#from gui.widget.MetWebBrowserGui import MSWebBrowserGui
from gui.MetBaseGui import MSWebBrowser, MSPeriodicTable, MSSettingsDialog

#from graphics.MetGLCanvas3D import MSGLCanvas3D
#from graphics.MetGLCanvas2D import MSGLCanvas2D
from graphics.MetMplCanvas import MSSpectrogramCanvas, MSDtwCanvas
#from core.MetProcessing import GLVertexCalculation
from core.MetObjects import MSSample, MSPeakList, MSChromatographicPeak, MSAbstractTypes
from utils.merger import merge


class MSMenuController(MSBaseController, ChoosenOne):
    """
    class handling the control of the menu bar, could use a metaclass
    for the singleton approach
    
    """    
    #def __init__(self, lspl, win):
    #    """constructor connection definitions"""
    #    MSBaseController.__init__(self, lspl, win)
                
    def _buildConnections(self):
        #undo redo stuffs
        QObject.connect(qApp.instance().undoStack, 
                     SIGNAL('canRedoChanged(bool)'), 
                     self.view.editMenu.actions()[1].setEnabled)
        QObject.connect(qApp.instance().undoStack, 
                     SIGNAL('canUndoChanged(bool)'), 
                     self.view.editMenu.actions()[0].setEnabled)
        
        #tooltip emulation TODO
        QObject.connect(self.view.peakPickingMenu, 
                     SIGNAL("hovered(QAction *)"), 
                     self.view._actionHovered)
        QObject.connect(self.view.fileMenu, 
                     SIGNAL("hovered(QAction *)"), 
                     self.view._actionHovered)
        
        #file menu
        QObject.connect(self.view.op.actions()[0], 
                     SIGNAL("triggered()"), 
                     self.openFile)
        QObject.connect(self.view.op.actions()[1],
                     SIGNAL('triggered()'),
                     self.loadProject)
        
        QObject.connect(self.view.fileMenu.actions()[1], 
                     SIGNAL("triggered()"), 
                     self.saveProject)
        QObject.connect(self.view.fileMenu.actions()[2], 
                     SIGNAL("triggered()"), 
                     self.loadPeakList)
        QObject.connect(self.view.fileMenu.actions()[3], 
                     SIGNAL("triggered()"), 
                     self.convertParameters)
        QObject.connect(self.view.fileMenu.actions()[4], 
                     SIGNAL("triggered()"), 
                     self.launchBatch)
        QObject.connect(self.view.fileMenu.actions()[5], 
                     SIGNAL("triggered()"), 
                     self.mergeFile)
        QObject.connect(self.view.fileMenu.actions()[7], 
                     SIGNAL("triggered()"), 
                     self.quit)
         
        #edit menu
        QObject.connect(self.view.editMenu.actions()[0],
                     SIGNAL('triggered()'),
                     QApplication.instance().undoStack.undo)
        QObject.connect(self.view.editMenu.actions()[1],
                     SIGNAL('triggered()'),
                     QApplication.instance().undoStack.redo)
        QObject.connect(self.view.editMenu.actions()[3], 
                        SIGNAL('triggered()'),
                        self.showSettings)
        QObject.connect(self.view.exportMenu.actions()[0], 
                        SIGNAL('triggered()'),
                        self.exportPeakList)
        QObject.connect(self.view.exportMenu.actions()[1],
                        SIGNAL('triggered()'),
                        self.exportClusterMatrix)
        
        
        #algo menu
        QObject.connect(self.view.preProcessing.actions()[0], 
                    SIGNAL('triggered()'), 
                    self.smoothAllRawData)
        QObject.connect(self.view.preProcessing.actions()[1], 
                    SIGNAL('triggered()'), 
                    self.baselineCorrection)
        QObject.connect(self.view.preProcessing.actions()[2],
                     SIGNAL('triggered()'),
                     self.calibrate)
        QObject.connect(self.view.preProcessing.actions()[3],
                     SIGNAL('triggered()'),
                     self.resizeSample)
        
        
        
        QObject.connect(self.view.peakPickingMenu.actions()[0], 
                     SIGNAL("triggered()"), 
                     self.integrationParameters)
        QObject.connect(self.view.peakPickingMenu.actions()[1], 
                     SIGNAL("triggered()"), 
                     self.centWaveParameters)
        
        #alignment        
        QObject.connect(self.view.alignment.actions()[0],
                        SIGNAL("triggered()"),
                        self.alignmentByPolyFit)
        QObject.connect(self.view.alignment.actions()[1],
                        SIGNAL('triggered()'),
                        self.alignmentByDtw)
        QObject.connect(self.view.alignment.actions()[2],
                        SIGNAL("triggered()"),
                        self.alignmentByObiWarp)
        
        QObject.connect(self.view.algoMenu.actions()[3],
                        SIGNAL('triggered()'), 
                        self.normalizeSamples)
        QObject.connect(self.view.algoMenu.actions()[4], 
                     SIGNAL("triggered()"), 
                     self.clusteringParameters)
        QObject.connect(self.view.algoMenu.actions()[5], 
                     SIGNAL("triggered()"), 
                     self.identificationParameters)
        
        
        
        #view menu
        QObject.connect(self.view.plotting.actions()[0], 
                     SIGNAL("triggered()"),
                     self.show3DView)
        #QObject.connect(self.view.plotting.actions()[1], 
        #             SIGNAL("triggered()"),
        #             self.launchCytoscape)
        QObject.connect(self.view.plotting.actions()[1], 
                     SIGNAL("triggered()"),
                     self.showSpectrogramView)
        #self.connect(self.view.plotting.actions()[3], 
        #             SIGNAL("triggered()"),
        #             self.showAlignedData)
        
        #tools menu
        QObject.connect(self.view.toolsMenu.actions()[0], 
                     SIGNAL("triggered()"),
                     self.launchWebNavigator)
        #QObject.connect(self.view.toolsMenu.actions()[1], 
        #             SIGNAL("triggered()"),
        #             self.launchCytoscape)
        QObject.connect(self.view.toolsMenu.actions()[1], 
                     SIGNAL("triggered()"),
                     self.launchEricEditor)
        QObject.connect(self.view.toolsMenu.actions()[2], 
                     SIGNAL("triggered()"),
                     self.showPeriodicTable)
        
        
        #plugins menu
        QObject.connect(self.view.launchingMenu, 
                     SIGNAL('triggered(QAction*)'), 
                     self.loadPlugin)
        QObject.connect(self.view.pluginMenu.actions()[2], 
                     SIGNAL('triggered()'), 
                     self.deletePlugs)
        
        #about
        QObject.connect(self.view.aboutMenu.actions()[0], 
                     SIGNAL("triggered()"), 
                     self.view.showMetMSInformation)
        QObject.connect(self.view.aboutMenu.actions()[1], 
                     SIGNAL("triggered()"),
                     self.showQtInformation)
                     
        QObject.connect(self.view.aboutMenu.actions()[2], 
                     SIGNAL("triggered()"),
                     self.showDocumentation)
    
    def deletePlugs(self):
        self.view.showInformationMessage("Warning", "Autoloaded plugin will be no longer available")
        for p in self.view.pluginsInst:
            p.unload()            
            del p
        self.view.update()
    
    
    def loadPlugin(self, action):
        app=QApplication.instance()
        app.pluginManager.loadPlugin(app.model, app.view, action.text())
    
    def showPeriodicTable(self):
        
        a=MSPeriodicTable(self.view)
        self.connect(a.ui.buttonBox, SIGNAL('rejected()'), a.close)
        self.connect(a.ui.buttonBox, SIGNAL('accepted()'), a.close)
        a.show()
    
    def showAlignedData(self):
        self.view.showInformationMessage('available soon', 'will be implemented soon..')

    def launchEricEditor(self):
        """
        to improve
        """
        #ed = MSEditor(self.view)
        try:
            from spyderlib.widgets.editor import FakePlugin
        except ImportError:
            self.view.showErrorMessage("Error", "This option is currently unavailable")
            return
        w=FakePlugin()
        project=QFileDialog.getOpenFileName(self.view, "Open a project...", filter='*.py')
        w.load(str(project))
        self.view.addMdiSubWindow(w)

    def loadProject(self):
        project=QFileDialog.getOpenFileName(self.view, "Open a project...", filter='*.ms')
        if not project: 
            return
        QApplication.instance().model=cPickle.load(open(path.normcase(str(project)), 'rb'))
        QApplication.instance().currentModelChanged() #emission to update controller current model
        #for spl in self.model:
        #    MSDialogController.actualizeSpectraModel(spl)
        #    if spl.rawPeaks:
        #        MSDialogController.actualizePeakModel(spl)
        #    if spl.mappedPeaks:
        #        MSDialogController.actualizeClusterModel(spl)
        #self.view.treeView.setModel(self.view.spectraModel)
        #self.view.treeView_2.setModel(self.view.peakModel)
        #self.view.treeView_3.setModel(self.view.clusterModel)
        self.view.showInformationMessage("Open Project", "Project successfully loaded !")

    def saveProject(self):
        
        if self._checkParsingDone():
            f = QFileDialog.getSaveFileName(self.view, 'Save file', filter='*.ms')
            if not f:
                return
            with open(str(f), 'wb') as fd:
                cPickle.dump(self.model, fd, -1)
            self.view.showInformationMessage("Save project", "project successfully saved !")
        
    
    def loadPeakList(self):
        """
        TODO:rewrite this cause it is fake
        use csv module for that ?
        """        
        string, boolean = QInputDialog.getItem(self.view, "Choose a kind of MS", "Kind of MS experiment :",
                                               ("HighResolution" , "Multiple Reaction Monitoring"), editable=False)
        if string and boolean:
            f = str(QFileDialog.getOpenFileName(self.view, "Select peaklist to open", filter="*.pkl"))
            if not f:
                return
           
    
    
#=============================================================================
#File data 
#=============================================================================
    def mergeFile(self):
        class MergeDialog(QtGui.QDialog):
            def __init__(self, parent=None):
                QtGui.QDialog.__init__(self, parent)
                self.setWindowTitle("Merge files")
                self.setAttribute(Qt.WA_DeleteOnClose)
                v = QtGui.QVBoxLayout(self)
                f =  QtGui.QFormLayout()
                self.lineEdit =  QtGui.QLineEdit()
                self.pushButton =  QtGui.QPushButton("Browse")
                f.addRow(self.lineEdit, self.pushButton)
                v.addLayout(f)
                self.buttons = QtGui.QDialogButtonBox()
                self.buttons.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
                v.addWidget(self.buttons)
                self.connect(self.pushButton, SIGNAL('clicked()'), self.setFiles)
            
            def setFiles(self):
                files = QFileDialog.getOpenFileNames(parent=None, caption="Choose file to merge")
                self.filesToMerge = map(str, list(files))
                s = ""
                for i, f in enumerate(self.filesToMerge):
                    s+= f.replace('\\', '/').split('/')[-1]
                    s+= '; ' if i != len(self.filesToMerge)-1 else ""
                self.lineEdit.setText(s)
        
        d = MergeDialog(self.view)
        
        def finish():
            """have to write that shit..."""
            self.view.showInformationMessage("Job done", "Done !")
        
        def merging():
            t = d.filesToMerge
            d.close()
            if not t:
                return
            t = Merger(t)
            t.connect(t, SIGNAL("started()"), self.view.to_indetermined_mode)
            t.connect(t, SIGNAL("finished()"), self.view.to_determined_mode)
            t.connect(t, SIGNAL("finished()"), finish)
            t.start()
            t.exec_()
                    
        d.connect(d.buttons, SIGNAL('accepted()'), merging)
        d.connect(d.buttons, SIGNAL("rejected()"), d.close)
        d.exec_()
    
    def launchBatch(self):
        pass
    
    
    
    def _checkParsingDone(self):
        if not self.model:
            self.view.showErrorMessage("Error", "No sample parsed, please open one file")
            return False
        return True
        
    
    def launchCytoscape(self):
        """show the example for the moment"""
        web = MSWebBrowser(parent=self.view)
        web.load_cytoscape()
        self.view.addMdiSubWindow(web)
    
    
    
    def showSpectrogramView(self):
        """provide scatterplot visualisation of the sample"""
        if self._checkParsingDone:
            string, boolean = QtGui.QInputDialog.getItem(self.view, "Spectrum", "Choose one sample :", \
            [spl.shortName() for spl in self.model], 0, False)
        
            if boolean and string:
                spl = self.model.sample(string, fullNameEntry=False)
                if spl is None:
                    print ("can not make spectrogram...")
                    return
                self.view.showInStatusBar("Plotting points.Please Wait...", 10000)
                self.view.addMdiSubWindow(MSSpectrogramCanvas(spl.spectra), 'Spectrogram of %s'%str(string))#MSGLCanvas2D

    
    def show3DView(self, sampleIdx=0):
        """provide 3D view of all the sample"""
        if not self._checkParsingDone():
            return
        string, boolean = QtGui.QInputDialog.getItem(self.view,"3D plot", "Choose one sample :", 
                                                     [spl.xmlfile for spl in self.model], sampleIdx, False)
        if boolean and string:
            #scriptR='3d.R'
            spl= self.model.sample(str(string))
            spectra=None
            if self.model.sample(str(string)).kind=='HighRes':
                string_, boolean_ = QtGui.QInputDialog.getText(self.view,"3D plot", "Select scan range (use '-' as separtor):")
                if not string_ and not boolean_ and '-' not in string_:
                    self.view.showErrorMessage("Stupid Error happened !", "use '-' to separate the to spectrum indexes")
                    return
                try:
                    minrange, maxrange = int(str(string_).split('-')[0]),int(str(string_).split('-')[1])
                except TypeError:
                    print ('index must be integers!')
                    return
                if maxrange > len(spl.spectra):
                    self.view.showInformationMessage('Error', "out of bound, reajust to normal value")
                    maxrange=len(spl.spectra)
                if minrange < len(spl.spectra):
                    minrange=0
                spectra= spl.spectra[minrange:maxrange]
            else:
                spectra=spl.spectra
            self.launchThreadFor3D(spectra)     
            self.view.showInStatusBar("3D plotting.Please Wait...", 10000)
#===============================================================================
# Export         
#===============================================================================
    def exportPeakList(self):
        if not self.model:
            self.view.showErrorMessage('Error', 'No sample found...')
            return
        string, boolean = QtGui.QInputDialog.getItem(self.view, "Select sample", "Select one sample:", 
                                                     [spl.shortName() for spl in self.model])
        if not boolean:
            return
        sample = self.model.sample(string, fullNameEntry=False)
        fileName = path.normcase(str(QFileDialog.getSaveFileName(self.view, "Save peakList")))
        sample.exportPeakList(fileName)
        self.view.showInformationMessage('Done', 'Export is done')
    
    def exportClusterMatrix(self):
        if not self.model:
            self.view.showErrorMessage('Error', 'No sample found...')
            return
        if not all([spl.mappedPeaks for spl in self.model]):
            self.view.showErrorMessage('Error', 'At least one sample does not have clusters')
        fileName = path.normcase(str(QFileDialog.getSaveFileName(self.view, "Save peakList")))
        self.model.exportClusterMatrix(fileName)
        self.view.showInformationMessage('Done', 'Export is done')


    def showSettings(self):
        d = MSSettingsDialog(self.view)
        d.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        def setParams():
            multiCore = d.multiCore.isChecked()
            lowMemory = d.lowMemory.isChecked()
            d.close()
            qApp.instance().multiCore = multiCore
            qApp.instance().lowMemory = lowMemory
        QObject.connect(d.buttonBox, SIGNAL('accepted()'), setParams)        
        QObject.connect(d.buttonBox, SIGNAL('rejected()'), d.close)     
        d.exec_()


#===============================================================================
#     PREPROCESSING
#===============================================================================
    def smoothAllRawData(self):
        """
        TODO: add a preview options...
        
        """
        if not self.model:
            self.view.showErrorMessage("Error", "No sample available...")
            return
        class Dial(QtGui.QDialog):
            choices =('average Smoothing', 'Savitsky-Golay Smoothing', 'Gaussian Smoothing')
            def __init__(self, parent):
                QtGui.QDialog.__init__(self, parent)
                self.setWindowTitle("Smoothing Options...")
                f =QtGui.QFormLayout(self)
                self.a_=QtGui.QComboBox(self); self.a_.addItems(self.choices)
                self.a =QtGui.QSpinBox(self)
                self.a.setToolTip('''<p><b>Average Smoothing:</b><p>
                                    <p>Window: windowsize</p>
                                    <p><b>Savitsky-Golay Smoothing:</b><p>
                                    <p>Window: windowsize</p>
                                    <p><b>Gauss Smoothing:</b><p>
                                    <p>Window: full width at half maximum of a median chromatogrpahic peak</p>''')
                self.a.setValue(5)
                self.b = QtGui.QSpinBox(self)
                self.b.setToolTip('''<p><b>Average Smoothing:</b><p>
                                    <p>Order: not used</p>
                                    <p><b>Savitsky-Golay Smoothing:</b><p>
                                    <p>Order: the order of the polynomial used in the filtering.
                                    Must be less then `window_size` - 1.</p>
                                    <p><b>Gauss Smoothing:</b><p>
                                    <p>Order: n-th derivative of the gaussian kernel</p>''')
                self.c= QtGui.QDialogButtonBox(self)
                self.c.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
                f.addRow("Smoothing function:", self.a_)
                f.addRow("window:" ,self.a)
                f.addRow("order:", self.b)
                f.addRow("", self.c)
                self.connect(self.a_, SIGNAL('currentIndexChanged(const QString &)'), self.updateView)
        
            def updateView(self, string):
                if string == self.choices[0]:
                    self.b.setEnabled(False)
                else:
                    self.b.setEnabled(True)
                    
        dialog = Dial(self.view)
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        dialog.updateView(dialog.choices[0])
        
        def smooth():
            window = dialog.a.value()
            order = dialog.b.value()
            method = dialog.a_.currentText()
            dialog.close()          
            qApp.instance().undoStack.push(SmoothUndoCommand(QApplication.instance().model, 
                                                       method, window, order,
                                                       "Smoothing #%s"%'1'))
        QObject.connect(dialog.c, SIGNAL("rejected()"), dialog.close)
        QObject.connect(dialog.c, SIGNAL("accepted()"), smooth)        
        dialog.exec_()
        
    def baselineCorrection(self):
        if not self.model:
            self.view.showErrorMessage("Error", "No sample available...")
            return

        string, boolean = QtGui.QInputDialog.getDouble(self.view, "enter a baseline", "quantile value", value=2e3)
        if not boolean:
            return
        qApp.instance().undoStack.push(BaseLineCorrectionCommand(QApplication.instance().model, 
                                                           string,
                                                           "baselineCorrection #%s"%'1'))
    
    #@pyqtSlot()
    def calibrate(self):
        if not self.model:
            self.view.showErrorMessage("Error", "No sample available...")
            return
        
        class Calibrate(QtGui.QDialog):
            def __init__(self, parent=None):
                QtGui.QDialog.__init__(self, parent)
                self.setWindowTitle("Calibration...")
                hbox=QtGui.QHBoxLayout()
                vbox=QtGui.QVBoxLayout()
                self.add=QtGui.QPushButton('add...')
                vbox.addWidget(self.add)
                self.remove=QtGui.QPushButton('remove...')
                vbox.addWidget(self.remove)
                self.open_ = QtGui.QPushButton("Open file...")
                vbox.addWidget(self.open_)
                self.buttonBox= QtGui.QDialogButtonBox(self)
                self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
                vbox.addWidget(self.buttonBox)
                self.tableView=QtGui.QTableView(self)
                self.tableView.setSelectionMode(1)
                self.tableView.setSelectionBehavior(1)
                hbox.addWidget(self.tableView)
                hbox.addLayout(vbox)
                self.setLayout(hbox)
            
                self.model = QtGui.QStandardItemModel()
                self.model.setHorizontalHeaderLabels(['known', 'measured'])
                self.connect(self.add, SIGNAL('clicked()'), self.updateModel)
                self.connect(self.remove, SIGNAL('clicked()'), self.removeFromModel)
                self.connect(self.open_, SIGNAL('clicked()'), self.loadFile)
                self.tableView.setModel(self.model)
                self.count=0
                
            def updateModel(self):
                x, y=QtGui.QStandardItem(), QtGui.QStandardItem()
                x.setEditable(True)
                y.setEditable(True)
                self.model.setItem(self.count, 0, x)
                self.model.setItem(self.count, 1, y)
                self.count+=1
                    
            def removeFromModel(self):
                selectedRows = self.selectionModel().selectedRows()
                for idx in reversed(sorted(selectedRows)):
                    self.tableView.model().removeRow(idx.row(), idx.parent())
                
            def loadFile(self):
                file = str(QtGui.QFileDialog.getOpenFileName(self, "Open csv file"))
                reader=csv.reader(open(file, 'rb'), delimiter=',')
                model=QtGui.QStandardItemModel()
                for i, r in enumerate(reader[1:]):
                    model.setItem(i, 0, QStandardItem(r[0]))
                    model.setItem(i, 1, QStandardItem(r[1]))
                self.tableView.setModel(model)
                
        dialog=Calibrate(self.view)
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)        
        def calib():
            data=[]
            #get the data
            for i in xrange(dialog.tableView.model().rowCount()):
                data.append((float(str(dialog.tableView.model().item(i, 0).text())), 
                             float(str(dialog.tableView.model().item(i, 1).text()))))
            QApplication.instance().undoStack.push(CalibrationCommand(QApplication.instance().model, 
                                                                            data,
                                                                            "Calibration #%s"%'1'))            
        QObject.connect(dialog.buttonBox, SIGNAL("rejected()"), dialog.close)
        QObject.connect(dialog.buttonBox, SIGNAL("accepted()"), calib)
        dialog.exec_()
        
    
    def resizeSample(self):
        if not self.model:
            self.view.showErrorMessage("Error", "no loaded sample")
            
        class Selector(QtGui.QDialog):
            def __init__(self, parent=None):
                QtGui.QDialog.__init__(self, parent)
                self.setWindowTitle("Resizing samples")
                self.setupUi()
            
            def setupUi(self):
                v = QtGui.QVBoxLayout()
                f = QtGui.QFormLayout()
                self.lineEdit = QtGui.QLineEdit(self)
                self.items = [spl.shortName() for spl in QApplication.instance().model] + ['All']
                self.comboBox = QtGui.QComboBox(self)
                self.comboBox.addItems(self.items)
                f.addRow("Please enter min(s) and max(s) separated by '-'", self.lineEdit)
                f.addRow("Working On samples:", self.comboBox)
                v.addLayout(f)
                self.dialogButtons = QtGui.QDialogButtonBox()
                self.dialogButtons.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)                
                v.addWidget(self.dialogButtons)
                self.setLayout(v)
        d = Selector(self.view)
        d.setAttribute(QtCore.Qt.WA_DeleteOnClose)
                               
        def resize():
            s = str(d.comboBox.currentText())
            min_, max_ = map(float, str(d.lineEdit.text()).split('-'))
            d.close()
            if s == 'All':
                if any([spl.rawPeaks for spl in self.model]):
                    self.view.showErrorMessage("Error", 
                                               "Can not resize sample when peak picking has already been done")
                for sample in self.model:
                    print "Resize %s"%sample.shortName()
                    sample.resizeSpectraLength(min_, max_)
            else:
                sample = self.model.sample(s, fullNameEntry=False)
                if sample.rawPeaks:
                    self.view.showErrorMessage("Error", 
                                               "Can not resize sample when peak picking has already been done")                    
                sample.resizeSpectraLength(min_, max_)
            for tree in (self.view.treeView, self.view.treeView_2, self.view.treeView_3):
                tree.removeAll()
            for spl in self.model:
                MSDialogController.actualizeSpectraModel(spl)
            self.view.showInformationMessage("Done", "Resizing has been done !")
                    
        QObject.connect(d.dialogButtons, SIGNAL('accepted()'), resize)
        QObject.connect(d.dialogButtons, SIGNAL('rejected()'), d.close)        
        d.exec_()
        
#===============================================================================
# NOrmalization
#===============================================================================
    def normalizeSamples(self):
        if not self.model:
            self.view.showErrorMessage("Error", "no sample found...")
            return
        class Dialog(QtGui.QDialog):
            def __init__(self, parent=None):
                QtGui.QDialog.__init__(self, parent)
                self.setupUi()
                self.connect(self.comboBox, SIGNAL('currentIndexChanged(const QString &)'), self.updateCombo)
                self.connect(self.comboBox_2, SIGNAL('currentIndexChanged(const QString &)'), self.updateLabel)
                self.peak = None
            def setupUi(self):
                v = QtGui.QVBoxLayout()
                f = QtGui.QFormLayout()
                self.comboBox = QtGui.QComboBox()
                self.items = [spl.shortName() for spl in QApplication.instance().model]
                self.comboBox.addItems(self.items)
                f.addRow("Choose One sample", self.comboBox)
                self.comboBox_2 = QtGui.QComboBox()
                f.addRow("Peak", self.comboBox_2)
                self.label = QtGui.QLabel()
                f.addRow("Area", self.label)
                self.checkBox = QtGui.QCheckBox("Apply to all", self)
                self.buttonBox = QtGui.QDialogButtonBox(self)
                self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
                v.addLayout(f)
                v.addWidget(self.checkBox)
                v.addWidget(self.buttonBox)                
                self.setLayout(v)
            
            def updateCombo(self, string):
                items = [str(p) for p in QApplication.instance().model.sample(string, fullNameEntry=False).irawPeaks()]
                self.comboBox_2.clear()
                self.comboBox_2.addItems(items)
            
            def updateLabel(self, string):
                self.peak = QApplication.instance().model.sample(self.comboBox.currentText(), 
                                       fullNameEntry=False).peakAt(*map(float, string.split('/')))
                self.label.setText(str(self.peak.area))
        
        dialog = Dialog(self.view)
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        dialog.updateCombo(qApp.instance().model[0].shortName())
        def norm():
            applyToAll = dialog.checkBox.isChecked()
            samplesToTreat = [spl for spl in self.model] if applyToAll else [self.model.sample(dialog.comboBox.currentText(), 
                                                                                                fullNameEntry=False)]
            peak = dialog.peak
            if peak is None:
                return
            dialog.close()
            for spl in samplesToTreat:
                spl.normalize(peak)
                
        QObject.connect(dialog.buttonBox, SIGNAL('rejected()'), dialog.close)
        QObject.connect(dialog.buttonBox, SIGNAL('accepted()'), norm)
        dialog.exec_()
#===============================================================================
#     ALIGNMENT
#===============================================================================
    def alignmentByObiWarp(self):
        self.view.showInformationMessage("No yet implemented", "coming soon..")
    
    
    def alignmentByDtw(self):
        if not self.model:
            self.view.showErrorMessage("Error", "No sample available...load several files first")
            return
        class DtwWidget(QtGui.QDialog):
            def __init__(self, parent=None):
                self.dtws, self.ref, self.others = [None]*3
                
                QtGui.QDialog.__init__(self, parent)
                self.setAttribute(Qt.WA_DeleteOnClose)
                self.setWindowTitle("Dtw Parameters")
                self.v = QtGui.QVBoxLayout(self)
                h = QtGui.QHBoxLayout()                
                self.derivative = QtGui.QCheckBox("Derivative DTW") 
                h.addWidget(self.derivative)
                self.showImg = QtGui.QCheckBox('Show Image', self)
                h.addWidget(self.showImg)
                self.v.addLayout(h)
                self.mplWidget = QtGui.QLabel("Empty, no calculation done yet")#MSDtwCanvas()
                #self.mplWidget.setMinimumSize(400, 300)
                self.v.addWidget(self.mplWidget)
                self.calc = QtGui.QPushButton("Go...")
                self.v.addWidget(self.calc)
                self.buttons = QtGui.QDialogButtonBox()
                self.buttons.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
                self.v.addWidget(self.buttons)
                
            def setDtws(self):                    
                #self.dtws = obj[0]
                i = self.v.indexOf(self.mplWidget)
                self.v.removeWidget(self.mplWidget)
                self.mplWidget.deleteLater()
                self.mplWidget = MSDtwCanvas(self.dtws, parent=self)
                self.mplWidget.setMinimumSize(500,400)
                self.v.insertWidget(i, self.mplWidget)
                self.dtws=None
                
            def compute(self):
                spl = [s for s in QApplication.instance().model if s.checked]
                self.dtws, self.ref, self.others = QApplication.instance().model.alignRawDataByDtw(spl, 
                                                                                                   self.derivative.isChecked(), 
                                                                                                    self.showImg.isChecked())
                self.setDtws()                
                #t = DtwAligner(spl, self.derivative.isChecked())
                #self.connect(t, SIGNAL('started()'), QApplication.instance().view.to_indetermined_mode)
                #self.connect(t, SIGNAL('finished()'), QApplication.instance().view.to_determined_mode)
                #self.connect(t, SIGNAL('endCalc(PyQt_PyObject)'), self.setDtws)                        
                #t.start()
                #t.exec_()            
        
        d = DtwWidget(self.view)
        
        def applyResult():
            #TODO: apply the result            
            dtws = d.dtws
            d.close()
            
        
        d.connect(d.calc, SIGNAL('clicked()'), d.compute)
        d.connect(d.buttons, SIGNAL('rejected()'), d.close)
        d.connect(d.buttons, SIGNAL('accepted()'), applyResult)
        d.exec_()
                
    
    
    def alignmentByPolyFit(self):
        if not self.model:
            self.view.showErrorMessage("Error", "No sample available...load several files first")
            return
        class Dial(QtGui.QDialog):
            def __init__(self, parent=None):
                QtGui.QDialog.__init__(self, parent)
                self.setWindowTitle("Alignment...")
                self.setupUi()
                #self.connect(self.dialogButtons, SIGNAL("accepted()"), self.close)
                #self.connect(self.dialogButtons, SIGNAL("rejected()"), self.close)
            def setupUi(self):
                v = QtGui.QVBoxLayout(self)
                self.textEdit = QtGui.QTextEdit(self)
                self.textEdit.setText('''<p><br> Informations:</br><p>
                                        This algorithm perform a polynomial fitting
                                        between a reference a sample and an other one
                                        It is extremly fast but not really accurate''')
                #self.textEdit.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
                v.addWidget(self.textEdit)
                g = QtGui.QGroupBox("Parameters")                                
                f = QtGui.QFormLayout()
                self.checkBox = QtGui.QRadioButton("align RawData", self)
                self.checkBox_2 = QtGui.QRadioButton("align with Peaks", self)                
                f.addRow(self.checkBox, self.checkBox_2)
                self.spinBox = QtGui.QSpinBox(self)
                self.spinBox.setMaximum(10)
                self.spinBox.setValue(3)
                f.addRow("Poly degree", self.spinBox)
                self.spinBox_2 = QtGui.QSpinBox(self)
                self.spinBox_2.setValue(6)
                f.addRow("Rt tolerance", self.spinBox_2)
                g.setLayout(f)                
                v.addWidget(g)
                self.dialogButtons = QtGui.QDialogButtonBox(self)
                self.dialogButtons.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
                v.addWidget(self.dialogButtons)
        
        d = Dial(self.view)
        d.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        def align():
            alignRaw = d.checkBox.isChecked()
            errorRt = d.spinBox_2.value()
            polyDegree = d.spinBox.value()
            d.close()     
            QApplication.instance().undoStack.push(AlignmentCommand(QApplication.instance().model, 
                                                             polyDegree, alignRaw, errorRt,
                                                             "Alignment"))
        QObject.connect(d.dialogButtons, SIGNAL("accepted()"), align)
        QObject.connect(d.dialogButtons, SIGNAL('rejected()'), d.close)
        d.exec_() 
       
        
                
        
    
#===============================================================================
#     Utility
#===============================================================================
    def showQtInformation(self):
        QtGui.QMessageBox.aboutQt(self.view)
    
    
    
    def showDocumentation(self):
        """API pySpec"""
        web = MSWebBrowser(parent=self.view)
        web.load("doc/class-tree.html")
        self.view.addMdiSubWindow(web)
        
    def launchWebNavigator(self):
        """launch Webyo"""
        #import webbrowser
        #webbrowser.open("http://www.google.com")
        web = MSWebBrowser(parent=self.view)
        self.view.addMdiSubWindow(web)
        
    def openFile(self):
        """Dialog for opening file"""
        dialog = MSVisualisationDialog(parent=self.view)
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        controller = MSVisualisationController(self.model, dialog, True)

        
    #def mergeFile(self):
    #    """dialog for merging files"""
    #    self.view.showInformationMessage("Information",\
    #    "We strongly recommand you to merge files during the peak-picking")
      
    
    def convertParameters(self):
        self.view.showInformationMessage('Information', 'Conversion from .wiff to mzXML and .raw to mzXML will be soon supported if constructor libraries are available')
        return        

    
    def integrationParameters(self):
        integr = MSMatchedFilteredDialog(parent=self.view)
        control = MSIntegrationController(self.model, integr, False)
        #integr.exec_()
        
    def centWaveParameters(self):
        integr = MSCentWaveDialog(parent=self.view)
        control = MSIntegrationController(self.model, integr, False)
        #integr.exec_()
        
    def clusteringParameters(self):
        clust = MSClusteringDialog(parent=self.view)
        control = MSClusteringController(self.model, clust, False)
        #clust.exec_()
        
    def identificationParameters(self):
        identif = MSIdentificationDialog(parent =self.view)
        control = MSIdentificationController(self.model, identif, False)
        #identif.exec_()
    
    @staticmethod
    def quit():
        """close the event loop and so the application"""
        res = QtGui.QApplication.instance().view.showWarningMessage("Exiting", "Are you sure ?")
        if res == QMessageBox.Cancel:#4194304:
            return      
        QtGui.qApp.quit()
        
    
    



class SmoothUndoCommand(QtGui.QUndoCommand):
    choices =('average Smoothing', 'Savitsky-Golay Smoothing', 'Gaussian Smoothing')
    def __init__(self, model, method, window, order, text, parent=None):
        QtGui.QUndoCommand.__init__(self, text, parent)
        self.model = deepcopy(model)#save state
        self.method = method
        self.window = window
        self.order = order
        
    def undo(self):
        QApplication.instance().model=self.model
        QApplication.instance().currentModelChanged()# = self.model
        QApplication.instance().view.showInformationMessage('Smoothing undone', "Smoothing undone")
    
    def redo(self):
        for s in QApplication.instance().model:
            for spectra in s.spectra:
                if self.method == self.choices[0]:
                    spectra.y_data = MSAbstractTypes.averageSmoothing(spectra.y_data, self.window)
                elif self.method == self.choices[1]:
                    spectra.y_data = MSAbstractTypes.SGSmoothing(spectra.y_data, self.window, self.order)
                elif self.method == self.choices[2]:
                    from scipy.ndimage import gaussian_filter1d as gaussSmoothing
                    spectra.y_data = gaussSmoothing(self.window, self.order)

        QApplication.instance().view.showInformationMessage('Smoothing done', "Smoothing done ")




class BaseLineCorrectionCommand(QtGui.QUndoCommand):
    def __init__(self, model, value, text, parent=None):
        QtGui.QUndoCommand.__init__(self, text, parent)
        self.model = deepcopy(model)#save state
        self.value = value
    
    def undo(self):
        QApplication.instance().model=self.model
        QApplication.instance().currentModelChanged()# = self.model
        QApplication.instance().view.showInformationMessage('BaseLine undone', "BaseLine undone")
    
    def redo(self):
        for s in QApplication.instance().model:
            for spectra in s.spectra:
                baseline=spectra.computeBaseLine(quantile=self.value, smooth=False)
                spectra.y_data= np.clip(spectra.y_data - baseline, 0, spectra.y_data.max())
                #MSAbstractTypes.averageSmoothing(spectra.y_data, self.window , self.method)
        QApplication.instance().view.showInformationMessage('Baseline calculation done', "Baseline calculation done")


class CalibrationCommand(QtGui.QUndoCommand):
    def __init__(self, model, value, text, parent=None):
        QtGui.QUndoCommand.__init__(self, text, parent)
        self.model = deepcopy(model)#save state
        self.value = value
    
    def undo(self):
        QApplication.instance().model=self.model
        QApplication.instance().currentModelChanged()# = self.model
        QApplication.instance().view.showInformationMessage('Calibration undone', "Calibration undone")
    
    def redo(self):
        for s in QApplication.instance().model:
           s.applyCalibration(self.value)
        QApplication.instance().view.showInformationMessage('Baseline calculation done', "Baseline calculation done")


class AlignmentCommand(QtGui.QUndoCommand):
    def __init__(self, model, polyDegree, rawData, errorRt, text, parent=None):
        QtGui.QUndoCommand.__init__(self, text, parent)
        self.qApp = QApplication.instance()
        self.model = deepcopy(model)
        self.spectraModel = QtGui.QStandardItemModel(qApp.instance().view.spectraModel)        
        self.peakModel = QtGui.QStandardItemModel(qApp.instance().view.peakModel)
        self.clusterModel = QtGui.QStandardItemModel(qApp.instance().view.clusterModel)        
        self.polyDegree = polyDegree
        self.rawData = rawData#boolean value working on raw data ?
        self.errorRt = errorRt#if we are working on peaks peakgrouping etc...
    
    def undo(self):
        qApp.instance().model=self.model
        qApp.instance().currentModelChanged()
        qApp.instance().view.spectraModel = self.spectraModel
        qApp.instance().view.peakModel = self.peakModel
        qApp.instance().view.clusterModel = self.clusterModel
        qApp.instance().view.treeView.setModel(qApp.instance().view.spectraModel)
        qApp.instance().view.treeView_2.setModel(qApp.instance().view.peakModel)
        qApp.instance().view.treeView_3.setModel(qApp.instance().view.clusterModel)
        qApp.instance().view.showInformationMessage('Alignment Undone', 'Alignment Undone')
        
    def  redo(self):
        m = QApplication.instance().model
        if self.rawData:
            m.alignRawData(m)
        else:
            m.alignPeaksInRTDimension(m, self.polyDegree, self.errorRt)
        for tree in (qApp.instance().view.treeView, qApp.instance().view.treeView_2, qApp.instance().view.treeView_3):
            tree.removeAll()
        for spl in qApp.instance().model:
            MSDialogController.actualizeSpectraModel(spl)
            if spl.rawPeaks:
                MSDialogController.actualizePeakModel(spl)
            if spl.mappedPeaks:
                MSDialogController.actualizeClusterModel(spl)
        qApp.instance().view.showInformationMessage('Alignment calculation done', "Alignment done")
        
        
#===============================================================================
# Theading merger
#===============================================================================
class Merger(QThread):
    def __init__(self, filenames, parent=None):
        self.filenames = filenames
        QThread.__init__(self, parent)
    
    def run(self):
        merge(self.filenames)

class DtwAligner(QThread):
    def __init__(self, spl, derivative, parent=None):
        self.spl = spl
        self.derivative = derivative
        QThread.__init__(self, parent)
        self.dtws=[]
        self.ref=None
        self.others=None
    
    def run(self):
        self.dtws, self.ref, self.others=QApplication.instance().model.alignRawDataByDtw(self.spl, self.derivative)
        self.emit(SIGNAL('endCalc(PyQt_PyObject)'), (self.dtws, self.ref, self.others))
    