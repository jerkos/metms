# -*- coding: utf-8 -*-


from PyQt4 import QtGui, QtCore


class MSVisualisationDialog(QtGui.QDialog):
     
    def __init__(self, parent=None):        
        QtGui.QDialog.__init__(self, parent)
        self._setupUi()
    
    
    def _setupUi(self):
        self.resize(400, 200)
        self.setWindowTitle("Parsing File...")
        
        verticalLayout = QtGui.QVBoxLayout(self)        
        gb = QtGui.QGroupBox("Files options", self)
        self.directory = QtGui.QCheckBox("parse directory recursively",self)
        f = QtGui.QFormLayout(); hl_2 =QtGui.QHBoxLayout(); v=QtGui.QVBoxLayout()
        f.addRow(self.directory, QtGui.QLabel(""))
        self.lineEdit = QtGui.QLineEdit(self)
        hl_2.addWidget(QtGui.QLabel("Path :"))
        hl_2.addWidget(self.lineEdit)
        self.fileDialogButton = QtGui.QPushButton("Browse...", self)
        self.fileDialogButton.setMaximumSize(QtCore.QSize(70,200))
        hl_2.addWidget(self.fileDialogButton)
        v.addLayout(hl_2)
        v.addLayout(f)
        gb.setLayout(v)
        #verticalLayout.addWidget(gb)
        
        #spacerItem3 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, 
        #                                QtGui.QSizePolicy.Minimum)
        #verticalLayout.addItem(spacerItem3)
        
        gb_2 = QtGui.QGroupBox("Input files parameters", self)
        vl = QtGui.QVBoxLayout()
        hl = QtGui.QHBoxLayout()
        self.fl = QtGui.QFormLayout()
        
        self.ppm=QtGui.QSpinBox(self)
        self.ppm.setMaximumSize(QtCore.QSize(200,200))
        self.msn=QtGui.QSpinBox(self)
        self.msn.setMaximumSize(QtCore.QSize(200,200))
        self.msn.setVisible(False)
        self.comboBox = QtGui.QComboBox(self)
        self.comboBox.setMaximumSize(QtCore.QSize(200,200))
        self.fl.addRow("Data type:", self.comboBox)
        self.fl.addRow("ppm:", self.ppm)
        #self.fl.addRow("MSn:", self.msn)
        #self.fl.itemAt(4).widget().setVisible(False)
        vl.addLayout(self.fl)
        vl.addLayout(hl)
        gb_2.setLayout(vl)
        
        verticalLayout.addWidget(gb_2)
        verticalLayout.addWidget(gb)
        
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)
       
        verticalLayout.addWidget(self.buttonBox)
        
        
class MSMergingDialog(QtGui.QDialog):
     
    def __init__(self, parent=None):        
        QtGui.QDialog.__init__(self, parent)
        self._setupUi()
    
    def _setupUi(self):
       self.resize(400, 200)
       self.setWindowTitle("Merging...")
       


class MSLoadPeaksDialog(QtGui.QDialog):
    
    def __init__(self, parent=None):    
        QtGui.QDialog.__init__(self, parent)
