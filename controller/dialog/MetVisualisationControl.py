# -*- coding: utf-8 -*-

__author__ = 'Marco','cram@hotmail.fr'

#import re
#from multiprocessing import Process, Pool, cpu_count
import multiprocessing
from PyQt4.QtCore import SIGNAL, pyqtSlot, QObject, QPropertyAnimation, QRect, QThread
from PyQt4.QtGui import QApplication, QMessageBox, qApp

#from core import MetObjects
#from parsers.MetNetcdfParser import MSNetcdfParser
from ..MetBaseControl import MSDialogController, MSThreadBasis
#from controller.MetBaseControl import  MSThreadBasis
from utils.misc import WithoutBlank, IceAndFire, Hot, GreenRed
from utils.decorators import slots, check
#import pp

def load(sample):
    sample.loadData()
    return sample

class MSParsingThread(MSThreadBasis):
    """thread for visualisation, parsing"""
    
    def __init__(self, samples, parent=None, **kw):
        MSThreadBasis.__init__(self, parent)
        self.sampleList = samples
        for item in self.sampleList:
            #item.msn= kw.get('MSn', 1)
            if kw['scan_type']=='MRM':
                item.kind ='MRM'   
                item.ppm = 5000.
            elif kw['scan_type']=='High Resolution':
                item.kind = 'HighRes'
                item.ppm= kw.get('ppm', 0.)


    def emission(self, value):
        self.emit(SIGNAL("update_pb"), value)

    def run(self):
        """
        a priori this function works better when it is not parallelized...
        
        """
        p = multiprocessing.Pool(processes=multiprocessing.cpu_count())
        self.sampleList = p.map(load, self.sampleList, chunksize=5)
        #for i, spl in enumerate(self.sampleList):
        #     if self.abort:
        #         break#cause return
        #     spl.loadData() if spl.kind=='HighRes' else spl.loadMZXMLData()
        self.emission(100)


class MSVisualisationController(MSDialogController):
    """
    Visualisation Controller
    first for automation of connections you can define special variables
    """
    
    '''
    __specialsConn__ = {"clicked()":('fileDialogButton', 'dial')}
    
    __thread__= MSParsingThread
    __specialsFunc__ = "setSampleColors"
    __getParam__ = 'getParameters'
    __threadConn__ = {#'status_message': 'showInStatusBar', 
                      'update_pb':'updateProgressBar',
                      'sendSampleList':'updateModel'}
    __endFunc__ = "setModels"
    
    '''
    nb = 0
    choices = ("", "High Resolution")
    
    def __init__(self, lspl, visu, creation=None):
        MSDialogController.__init__(self, lspl, visu, creation)
        MSVisualisationController.nb += 1
        self.title = "Parsing nb: %d" % MSVisualisationController.nb
        
        QObject.connect(self.view.comboBox, SIGNAL('currentIndexChanged(const QString&)'), self.updateLayout)
        QObject.connect(self.view.fileDialogButton, SIGNAL('clicked()'), self.showOpenDialogs)
        #QObject.connect(self.qApp, SIGNAL('deleteLastController()'), self.qApp.deleteController)
        
    def _initialize(self):
        """called in MSDialogController.__init__()"""
        for element in self.choices:
            self.view.comboBox.addItem(element)
        self.view.comboBox.setCurrentIndex(1)
        self.view.ppm.setValue(10)
        self.view.msn.setValue(1)
            
    def getParameters(self):
        self.parameters["scan_type"] = self.view.comboBox.currentText()
        if self.view.comboBox.currentText() == 'High Resolution':
            self.parameters['ppm'] = self.view.ppm.value()
        elif self.view.comboBox.currentText()=='MRM':
            self.parameters['MSn'] = self.view.msn.value()
        return self.parameters
    
    @pyqtSlot()
    def updateLayout(self, string):
        if string=="High Resolution":
            self.view.fl.itemAt(4).widget().setVisible(False)
            self.view.fl.itemAt(2).widget().setVisible(True)
            self.view.ppm.setVisible(True)
            self.view.msn.setVisible(False)
        elif string=="MRM":
            #self.view.fl.itemAt(4).widget().setVisible(True)
            self.view.fl.itemAt(2).widget().setVisible(False)
            self.view.ppm.setVisible(False)
            #self.view.msn.setVisible(True)
            
    @pyqtSlot()
    def showOpenDialogs(self):
        self.selectedFiles=[]
        self.parameters["checkdir"] = self.view.directory.isChecked()
        if self.parameters["checkdir"]:
            if self.view.comboBox.currentText() == 'High Resolution':
                self.openDirDialog('*.CDF')
            else:
                self.openDirDialog('*.mzXML')
        else:
            filter_ = '*cdf;;*mzxml' if self.view.comboBox.currentText()=='High Resolution' \
            else '*mzxml;;*cdf'
            self.openFileDialog(filter_=filter_)
     
    @staticmethod
    def setSampleColors(lspl):
        """
        TODO:move maybe this method
        
        """
        for i, sample in enumerate(lspl):
            sample.color = WithoutBlank._get_color(float(i)/len(lspl))
    
    @pyqtSlot()
    def updateModel(self, spllist):
        """get the samplelist from the multiprocessing processes"""
        self.sampleList=spllist
        self.model.extend(spllist)
    
    @pyqtSlot()
    def setModels(self):
        """
        just set the model
        """
        print "setting treeView models..."
        self.task.setParent(None)#this i preferable
        self.task=None
        self.qApp.view.showInStatusBar("Setting treeView Model...")
        
        self.model+=self.sampleList#add samples
        
        for spl in self.sampleList:
            #if the user press the stop button
            #show only the ones already parsed
            if spl.spectra:
                MSDialogController.actualizeSampleModel(spl)
        self.qApp.view.showInformationMessage("Parsing done", "Parsing done successfully")
        self.qApp.emit(SIGNAL('deleteLastController()'))#at the end we can safely remove the last controller
        
    @pyqtSlot()                                                  
    def startTask(self):
        MSDialogController.startTask(self)
        self.setSampleColors(self.sampleList)
        self.task = MSParsingThread(self.sampleList, parent=self.qApp, **self.parameters)
        self.qApp.controllers[self] = self.task
        #self.qApp.view.updateStopProcessMenu()
        QObject.connect(self.view, SIGNAL('destroyed(QObject *)'), self.task.start)
        QObject.connect(self.task, SIGNAL('finished()'), self.setModels)        
        QObject.connect(self.task, SIGNAL('update_pb'), self.qApp.view.updateProgressBar)
        self.view.close()
        self.view = None #after deletion se to None

class MSLoadPeaksController(MSDialogController):
    def __init__(self, model, view, tree, creation):
        MSDialogController.__init__(self, model, view, tree, creation)
        self._specialConnections()
        self.spl = None# a new sample will be created
        
    def _specilaConnections(self):
        self.connect(self.view.buttonBox, QtCore.SIGNAL("accepted()"), self.loadPeakList)
        
    
    def getProcessingParameters(self):
        self.processingParameters["name"] = str(self.view.lineEdit.text())
    
    def loadPeakList(self):
        from parers.MetParserBase import MSParserBasis
        parser = MSParserBasis(self.model)
        
        def buildingPeaks(dict_):
            return obj.MSChromatographicPeak(None, 
                                             None,
                                             dict_["mz"],
                                             dict_["rt"], 
                                             dict_["rtmax"], 
                                             dict_["rtmin"], 
                                             dict_["area"], 
                                             chromatogram=None)
        peaks = obj.MSPeakList()                                       
        for data in parser.parsing():
            try:
                peaks.append(buildingPeaks(data))
            except KeyError:
                self.view.parent().showErrorMessage("Error in parsing peaklist", 
                "Can not parse peakList due to <b>wrong column name</b>")
    
    def buildModel(self):pass
        


