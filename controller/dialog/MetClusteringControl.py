#!usr/bin/python
#-*-coding:utf8-*-

#from multiprocessing import Pool#, Process, cpu_count
import os.path as path

from PyQt4.QtCore import SIGNAL, QObject#, QThread
from PyQt4.QtGui import QStandardItemModel, QStandardItem, QApplication, qApp, QDoubleSpinBox#, QMessageBox, QApplication

from controller.MetBaseControl import MSDialogController, MSThreadBasis
from core.MetClustering import clusteringWrapper
from utils.misc import OrderedDict
from utils.decorators import slots, check
#import pp


class MSClusteringController(MSDialogController):
    """
    Class to Control the gui and the model for clustering
    
    """
    POS_ADDUCTS=path.normcase('config/databases/POS_ADDUCTS.csv'), \
                path.normcase('config/databases/POS_ADDUCTS_LOW_RES.csv')
    NEG_ADDUCTS=path.normcase('config/databases/NEG_ADDUCTS.csv'), \
                path.normcase('config/databases/NEG_ADDUCTS_LOW_RES.csv')
    FRAGMENTS=path.normcase('config/databases/FRAGMENTS.csv'), \
              path.normcase('config/databases/FRAGMENTS_LOW_RES.csv')
              
    def __init__(self, lspl, visu, creation):
        MSDialogController.__init__(self, lspl, visu, creation)
        self.polarity=1 #initialisation
        if not self.model:
            self.goodIdx = 0
        else:
            self.goodIdx = 0 if self.model[0].kind == 'HighRes' else 1
        
        self.populateTableViews(self.polarity)
        self.allAddsChecked = False
        self.allFragsChecked = False
        QObject.connect(self.view.posmode, SIGNAL('toggled(bool)'), self.updatePolarity)
        QObject.connect(self.view.checkAllAdds, SIGNAL('clicked()'), self.checkAdds)
        QObject.connect(self.view.checkAllFrags, SIGNAL('clicked()'), self.checkFrags)
        
        self.view.exec_()
    
    
    def getFragAddData(self, polarity=1):
        """parsing adducts and fragments files"""
        frags=self.readData(self.FRAGMENTS[self.goodIdx])
        if not polarity:
            adds=self.readData(self.NEG_ADDUCTS[self.goodIdx])
        elif polarity:
            adds=self.readData(self.POS_ADDUCTS[self.goodIdx])
        return frags, adds
    
    
    def readData(self, file_):
        """read data from databases files"""
        def fragData(line, d):
            d[(s[0], s[1], str(1))]= False
            
        def addData(line, d):
            d[(s[0], s[-1].rstrip(), s[1])]= False
        
        routine=None
        if file_ in (self.POS_ADDUCTS+self.NEG_ADDUCTS):
            routine=addData
        elif file_ in self.FRAGMENTS:
            routine=fragData
        else:
            print ("Error reading adducts and fragments files")
            return
        res=OrderedDict()        
        with open(file_) as f:
            for i in range (2):
                l=f.readline()
            while l!="":
                s=l.split(',')
                routine(l, res)
                l=f.readline()
        return res
    
    
    def checkAdds(self):
        for i in xrange(self.adductsModel.rowCount()):
            #data = self.adductsModel.item(i,0).text()
            item = self.adductsModel.item(i,0)
            if self.allAddsChecked:
                item.setCheckState(0)
                self.view.checkAllAdds.setText('Check All')
            else:
                item.setCheckState(2)
                self.view.checkAllAdds.setText('UnCheck All')
        self.allAddsChecked = not self.allAddsChecked
                   
    def checkFrags(self):
        for i in xrange(self.fragsModel.rowCount()):
            #data = self.fragsModel.item(i,0).text()
            item = self.fragsModel.item(i,0)
            if self.allFragsChecked:
                item.setCheckState(0)
                self.view.checkAllFrags.setText('Check All')
            else:
                item.setCheckState(2)
                self.view.checkAllFrags.setText('UnCheck All')
        self.allFragsChecked = not self.allFragsChecked
        
        
    def populateTableViews(self, polarity):
        frags, adds = self.getFragAddData(polarity)
        self.adductsModel, self.fragsModel = QStandardItemModel(), QStandardItemModel()
        self.adductsModel.setHorizontalHeaderLabels(["Adducts(name, mass, nmol)"])
        self.fragsModel.setHorizontalHeaderLabels(["Fragments(name, mass, nmol)"])
        
        for i, adduct in enumerate(adds.keys()):
            item =QStandardItem(', '.join(map(str, adduct)))
            item.setCheckable(True)
            if adds[adduct]:
                item.setCheckState(2)
            else:
                item.setCheckState(0)
            self.adductsModel.setItem(i, 0, item)
        self.view.adductsTable.setModel(self.adductsModel)
        
        for i, frag in enumerate(frags.keys()):
            item = QStandardItem(', '.join(map(str, frag)))
            item.setCheckable(True)
            if frags[frag]:
                item.setCheckState(2)
            else:
                item.setCheckState(0)
            self.fragsModel.setItem(i, 0, item)
        self.view.fragTable.setModel(self.fragsModel)
    
    def getFragsAndAdductsToCheck(self):
        frags, adducts={}, {}
        for i in range(self.fragsModel.rowCount()):
            data = self.fragsModel.item(i,0).text()
            item = self.fragsModel.item(i,0)
            if item.checkState():
                frags[tuple([str(x) for x in data.split(', ')])]= True
            else:
                frags[tuple([str(x) for x in data.split(', ')])]= False
                
        for i in range(self.adductsModel.rowCount()):
            data = self.adductsModel.item(i,0).text()
            item = self.adductsModel.item(i,0)
            if item.checkState():
                adducts[tuple([str(x) for x in data.split(', ')])]= True
            else:
                adducts[tuple([str(x) for x in data.split(', ')])]= False

        checkMasses=OrderedDict()        
        for frag in frags.keys():
            if frags[frag]:
                checkMasses[(float(frag[1]), float(frag[2]))] = frag[0]
        for add in adducts.keys():
            if adducts[add]:
                if self.polarity:#positive polarity
                    checkMasses[(-float(add[1]), float(add[2]))] = add[0]
                elif not self.polarity:#negative polarity
                    checkMasses[(float(add[1]), float(add[2]))] = add[0]
        return checkMasses
    

    def updatePolarity(self, boolean):
        self.polarity = 1 if boolean else 0#positive, negative
        self.populateTableViews(self.polarity)
    
    
    def getParameters(self):
        """classical getParameters (model) function"""
        
        self.parameters["rtError"] = self.view.lineEdit_2.value()
        self.parameters["clusterLength"] = self.view.lineEdit_3.value()
        self.parameters["idmsLength"] =tuple([float(x) for x in self.view.lineEdit_4.text().split('-')])
        self.parameters["badPeaks"] = self.view.lineEdit_5.isChecked()
        #self.parameters["useCorr"] = self.view.check.isChecked()
        self.parameters["gap"]=self.view.spinBox.value()
        self.parameters["resolveConflicts"]=self.view.lineEdit_6.isChecked()
        self.parameters["frags"]=self.getFragsAndAdductsToCheck()
    
    
    def startTask(self):
        """
        Main Function (model function) Clustering
        
        """
        MSDialogController.startTask(self)
        #qApp.instance().view.showInStatusBar("Clustering Step...Please Wait..",  5000)
        self.task = MSClusterThread(self.sampleList, **self.parameters)
        QObject.connect(self.view, SIGNAL('destroyed(QObject *)'), self.task.begin)
        #self.connect(self.view, SIGNAL('destroyed(QObject *)'), self.setViewToNone)
        QObject.connect(self.task, SIGNAL("started()"),qApp.instance().view.to_determined_mode)
        QObject.connect(self.task, SIGNAL('update_pb'), qApp.instance().view.updateProgressBar)
        #QObject.connect(self.task, SIGNAL("finished()"),qApp.instance().view.to_determined_mode)
        QObject.connect(self.task, SIGNAL("finished()"), self.setModels)
        #print "about to close"
        self.view.close()
        #print "closed"
        #self.task.begin()
    
    def setModels(self):#, sampleList):
        """
        closing function of the process
        
        """
        qApp.instance().view.showInformationMessage("Clustering done", "Clustering Done succesfully !")
        qApp.instance().view.tabWidget.setCurrentIndex(2)
        

    
    def _initialize(self):
        """initialization of the parameters"""
        
        self.view.lineEdit_2.setValue(6.)
        self.view.lineEdit_3.setValue(6)
        self.view.lineEdit_4.setText("0-0")
        #self.view.lineEdit_5.setText("10.")
        self.view.decrOrder.setChecked(True)
        self.view.lineEdit_6.setChecked(True)
        self.view.spinBox.setValue(0)
     

#===============================================================================
# THREAD AND MULTIPROCESSING IMPLEMENTATION
#===============================================================================
def makeClusters(spl, parameters):
    '''can not be in the class, need to be serialized in order to
    distribute in multiprocessing environnment'''
    clusteringWrapper(spl, **parameters)
    return spl
        
def wrap(args):
    return makeClusters(*args)        

class MSClusterThread(MSThreadBasis):
    """
    Threading Clustering process
    
    """
    def __init__(self, lspl, **clusteringParameters):        
        MSThreadBasis.__init__(self)
        self.sampleList=lspl
        mode=self.sampleList[0].kind
        if not all([spl.kind==mode for spl in self.sampleList]):
            print ("Error, all members of sampleList must be the same kind")
            return
        self.parameters = clusteringParameters
        self.parameters['mode']=mode
        self.parameters['lspl'] = self.sampleList
    
    def emission(self, value):
        self.emit(SIGNAL("update_pb"), value)
    
    def run(self):
#        if QApplication.instance().multiCore:
#            server = pp.Server()
#            print "working on %s cpu(s)"%str(server.get_ncpus())
#            jobs = []
#            for i, spl in enumerate(self.sampleList):
#                j = server.submit(worker, (spl, self.parameters), (clusteringWrapper, slots, check), ('core.MetObjects',))
#                jobs.append(j)            
#                self.emission((i+1/len(self.sampleList))*100)
#            for i in xrange(len(jobs)):
#                self.sampleList[i] = jobs[i]()
#            server.destroy()
#            self.emission(100)
#        else:
            print "starting the for loop"
            for i, spl in enumerate(self.sampleList):
                spl.doClustering(**self.parameters)
                print "before emission"
                self.emission((float(i+1)/len(self.sampleList))*100)
                print "after emssion"
            print "end for loop"

def worker(spl, params):
    spl.doClustering(**params)
    return spl