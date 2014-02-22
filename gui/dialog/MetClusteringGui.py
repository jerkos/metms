#usr/bin/python
# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'cluster_gui.ui'
#
# Created: Tue Jun 22 14:38:32 2010
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt, SIGNAL

class MSClusteringDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle("Clustering parameters")
        self.setupUi()
        
    def setupUi(self):
        
        self.setWindowFlags(QtCore.Qt.Window)
        self.resize(500, 400)
        self.verticalLayout = QtGui.QVBoxLayout(self)
        
        
        gb = QtGui.QGroupBox("Files options", self)
        hl = QtGui.QHBoxLayout()
        hl.addWidget(QtGui.QLabel("Working on:",self))
        self.lineEdit = QtGui.QLineEdit(self)
        self.lineEdit.setReadOnly(True)
        hl.addWidget(self.lineEdit)     
        gb.setLayout(hl)
        self.verticalLayout.addWidget(gb)
        
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        
        gb_2 = QtGui.QGroupBox("Algorithms parameters", self)
        h = QtGui.QHBoxLayout()
        f = QtGui.QFormLayout()
        self.lineEdit_2 = QtGui.QDoubleSpinBox(self)
        self.lineEdit_3 = QtGui.QSpinBox(self)
        self.lineEdit_4 = QtGui.QLineEdit(self)
        self.lineEdit_5 = QtGui.QCheckBox('keep Bad Peak', self)
        self.lineEdit_6=QtGui.QCheckBox('resolve conflicts', self)
        self.spinBox = QtGui.QSpinBox(self)
        self.decrOrder = QtGui.QCheckBox('Monotonic IC',self)
        self.decrOrder.setToolTip("""the algorithm if checked will find only 
                                    peaks belonging the the isotopic cluster
                                    with a height inferior to the original peak""")
        self.posmode = QtGui.QRadioButton('positive mode', self)
        self.posmode.setChecked(True)
        self.negmode = QtGui.QRadioButton('negative mode', self)
        
        #self.check = QtGui.QCheckBox("use correlation...", self)
        f.addRow("rt drift", self.lineEdit_2)
        f.addRow("isocluster length", self.lineEdit_3)
        f.addRow("gap", self.spinBox)
        #f.addRow(self.check, QtGui.QLabel(""))
        f.addRow(self.posmode, self.negmode)
        
        h.addLayout(f)
        f_2 = QtGui.QFormLayout()
        f_2.addRow(self.decrOrder,  QtGui.QLabel(""))
        f_2.addRow("idms length", self.lineEdit_4)
        f_2.addRow(self.lineEdit_6, self.lineEdit_5)
        #f_2.addRow('resolve conflicts', self.lineEdit_6)
       
        h.addLayout(f_2)
        gb_2.setLayout(h)
            
        self.verticalLayout.addWidget(gb_2)
        
        h =  QtGui.QHBoxLayout()
        self.adductsTable = QtGui.QTableView(self)
        self.adductsTable.horizontalHeader().setStretchLastSection(True)
       
        h.addWidget(self.adductsTable)
        self.fragTable = QtGui.QTableView(self)
        self.fragTable.horizontalHeader().setStretchLastSection(True)
        h.addWidget(self.fragTable)
        self.verticalLayout.addLayout(h)
        
        h2=QtGui.QHBoxLayout()
        self.checkAllAdds=QtGui.QPushButton("Check all adducts")
        self.checkAllFrags=QtGui.QPushButton("Check all fragments")
        h2.addWidget(self.checkAllAdds);h2.addWidget(self.checkAllFrags)
        self.verticalLayout.addLayout(h2)
        
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)
            