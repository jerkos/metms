#!usr/bin/python

"""Module implementing the controller of the identification dialog"""


__author__ = "marco","cram@hotmail.fr"


import sqlite3
import os.path as path
try:
    from PyQt4.QtGui import QStandardItemModel, QApplication, QTableView, QStandardItem
    from PyQt4.QtCore import SIGNAL, pyqtSlot, QObject
    pyqt=True
except ImportError:
    pyqt=False

from utils.parsers import MSKeggParser
from utils.parsers import MSMetjpParser
from utils.parsers import MSBioCycParser
from core.MetIdentification import MSIdentificationModel
from core.MetDataObjects import MSAlphabet
#from core import MetObjects as obj
from gui.MetBaseGui import MSTableView, MSStandardItem
#from controller.widget.MetTableViewControl import MSTableViewController
from controller.MetBaseControl import MSDialogController, MSThreadBasis


#def identify(spl, model, parameters):
#    '''can not be in the class, need to be serialized in order to
#    distribute in multiprocessing environnment'''
#    id_=MSIdentificationModel(spl, **parameters)
#    id_.identification(model, error=5)
#    return model
#
#def wrap(a):
#    return identify(*a)


class MSIdThread(MSThreadBasis):
    """Identifiaction thread"""
    
    def __init__(self, lspl, **parameters):
        MSThreadBasis.__init__(self)
        self.sampleList = lspl
        self.parameters=parameters
        if pyqt:
            self.models=[QStandardItemModel() for spl in self.sampleList]
    
    def run(self):
        """Thread Actions identifcation instance"""
        
        for i, spl in enumerate(self.sampleList):
            id_ =MSIdentificationModel(spl, **self.parameters)
            id_.identification(self.models[i], error=5)
          
                
        

class MSIdentificationController(MSDialogController):
    """Class for handling identification gui"""
    
    
    
    ELEMENTS_FILE=path.normcase("config/config/elements.xml")
    KEGG_FILE=path.normcase("config/databases/KEGG.txt")
    METJP_FILE= path.normcase("config/databases/metaboliteMass.txt")
    BIOCYC_FILE= path.normcase( "config/databases/LinksBioCycKegg.txt")
    METEXPLORE_FILE=path.normcase('config/databases/metexplore.sqlite')
    
    
    def __init__(self, lspl, visu, creation, showDirectResult=False):
        """
        constructor 
        
        """
        #data needed to process
        MSDialogController.__init__(self, lspl, visu, creation)
        self.databases ={"KEGG":None,
                         "METJP":None, 
                         "BIOCYC":None,
                         "METEXPLORE":None}
        QObject.connect(self.view.checkBox_8, SIGNAL('toggled(bool)'), self._update)
        self._update(True)#initializing to metexplore so we keep enabled
        self.showDirectResult = showDirectResult        
        
        self.view.exec_()
    
    def _update(self, boolean):
        self.view.comboBox.setEnabled(boolean)
        
    def _initialize(self):
        """clalled in __init__ by MSDialogController"""
        
        self.view.lineEdit_3.setText("C,H,N,O,P,S")
        self.view.spin_hit.setValue(20)
        self.view.lineEdit_2.setValue(10.)
        self.view.checkBox_8.setChecked(True)
        
    
    def databasesParsing(self, kegg,  met_jp, biocyc, metexplore):
        """ parse all files"""
        #KEGG
        if kegg:
            QApplication.instance().view.statusBar().showMessage("Parsing Kegg file", 2000)
            kegg_ = MSKeggParser(self.KEGG_FILE)
            kegg_.parsing()
            self.databases["KEGG"] = kegg_
        #METJP
        if met_jp:
            QApplication.instance().view.statusBar().showMessage("Parsing MetabolomeJP file", 2000)
            metjp_ = MSMetjpParser(self.METJP_FILE)
            metjp_.parsing()            
            self.databases["METJP"] = metjp_
        #BIOCYC
        if biocyc:
            QApplication.instance().view.statusBar().showMessage("Parsing BioCyc file", 2000)
            biocyc_parser = MSBioCycParser(self.BIOCYC_FILE)
            biocyc_parser.parsing()
            self.databases["BIOCYC"] = biocyc_parser
            
        if metexplore[0]:
            conn=sqlite3.Connection(self.METEXPLORE_FILE)
            c=conn.cursor()
            c.execute('select * from Metabolite, MetaboliteInBioSource, BioSource, Organism where\
                        Metabolite.id=MetaboliteInBioSource.idMetabolite and \
                        MetaboliteInBioSource.idBioSource=BioSource.id and \
                        BioSource.idOrg=Organism.id and \
                        Organism.name="'+str(metexplore[1])+'"')
            #c has an __iter__ function
            #dict formula/names
            self.databases["METEXPLORE"]=dict([(str(met[2]), str(met[1])) for met in c])
            
    
    
    
    def getParameters(self):
        #get parameters values
        self.parameters["charge"]=float(self.view.charges[str(self.view.spinBox.currentText())])
        #self.parameters["lastConvolve"]=str(self.view.spinBox.currentText())
        self.parameters["ppm"] =float(self.view.lineEdit_2.value())
        self.parameters["hit"] = self.view.spin_hit.value()
        self.parameters["checkIsos"] = self.view.checkIso.isChecked()

      
        wantedAlphabet = str(self.view.lineEdit_3.text())
        #el = ElementParser(self.ELEMENTS_FILE)
        alphabet=MSAlphabet.withElements(wantedAlphabet.split(','))
        QApplication.instance().view.statusBar().showMessage("Parsing Elements file", 2000)
        #self.parameters["allElements"]=alphabet
        self.parameters["alphabet"] =alphabet#el.selectElements(wantedAlphabet)
        
        #manages checking        
        self.parameters["idms"] = self.view.checkBox_4.isChecked()
        self.parameters["phos"] = self.view.checkBox_6.isChecked()
        self.parameters["smiles"] =self.view.checkBox_7.isChecked()
        
        if  self.parameters["smiles"] and not self.view.checkBox_5.isChecked():
            QApplication.instance().view.showInformationMessage("One more check needed", 
                                                      "In order to use smiles information, Biocyc checkbox must be checked")
            return
        #get databases
        self.databasesParsing(self.view.checkBox.isChecked(), 
                              self.view.checkBox_2.isChecked(), 
                              self.view.checkBox_5.isChecked(),
                              (self.view.checkBox_8.isChecked(), str(self.view.comboBox.currentText())))
        self.parameters["databases"] = self.databases
        self.parameters["data"]=dict(self.view.data)
    
    
    @pyqtSlot()
    def startTask(self):    
        """
        Main Function
        
        """                
        MSDialogController.startTask(self)
        self.task= MSIdThread(self.sampleList, **self.parameters)
        QObject.connect(self.view, SIGNAL('destroyed(QObject *)'), self.task.begin)
        QObject.connect(self.task, SIGNAL("started()"),self.qApp.view.to_indetermined_mode)
        QObject.connect(self.task, SIGNAL("finished()"), self.qApp.view.to_determined_mode)
        QObject.connect(self.task, SIGNAL("finished()"), self.setModels)
        self.view.close()

    
    def setModels(self):
        """Add the model to the view when the thread ended"""
        
        if self.showDirectResult:        
            table = QTableView()
            view = MSTableView(table, model=self.buildModel(self.sampleList[0].rawPeaks[0]), selection=True)
            self.qApp.view.addMdiSubWindow(view, "identification of mapped peaks of %s"%self.sampleList[0].shortName())
        
        currentSample = self.qApp.dockControl.currentSample[2]
        if currentSample is not None:
            MSDialogController.actualizeClusterModel(currentSample)
        self.qApp.view.showInformationMessage("Job Done", "Identification is done !")
        
    def buildModel(self, choosenOne):
        identificationModel = QStandardItemModel()
        if choosenOne.formulas:
            identificationModel.setHorizontalHeaderLabels(["score", "formula", "diff mass", "names"])
            for i, f in enumerate(choosenOne.formulas.iterkeys()):
                identificationModel.setItem(i, 0, MSStandardItem(str(choosenOne.formulas[f]["score"])))
                identificationModel.setItem(i, 1, QStandardItem(str(f)))
                identificationModel.setItem(i, 2, MSStandardItem(str(choosenOne.formulas[f]["diffmass"])))
                identificationModel.setItem(i, 3, QStandardItem(choosenOne.formulas[f]["names"]))
        return identificationModel