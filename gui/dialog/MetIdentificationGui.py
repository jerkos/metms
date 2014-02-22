# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'identification.ui'
#
# Created: Tue Jun 29 11:09:26 2010
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
import sqlite3

class MSIdentificationDialog(QtGui.QDialog):

    def __init__(self, parent =None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle("Identification parameters")
        self.charges = {"positive(+H)":-1.0072277, "positive(+Na)":-22.98992, "negative(-H)":1.0072277}
        self.setupUi()
        #by default: -C 1-95 -H 1-190 -N 0-20 -O 1-80 -P 0-12 -S 0-9
        self.data ={"C":"1-40", "H":"1-60", "N":"0-20", "O": "1-30","P":"0-5", "S":"0-5"}
        self.connect(self.push, QtCore.SIGNAL("clicked()"),self.launch_second)

    def setupUi(self):
        self.resize(200, 100)
        self.verticalLayout = QtGui.QVBoxLayout(self)
        
        gr = QtGui.QGroupBox("Files options", self)
        vb3 = QtGui.QHBoxLayout()
        self.lineEdit = QtGui.QLineEdit(self)
        self.lineEdit.setReadOnly(True)
        vb3.addWidget(self.lineEdit)
        gr.setLayout(vb3)
        self.verticalLayout.addWidget(gr)
        
        
        h = QtGui.QHBoxLayout()
        gr4 = QtGui.QGroupBox("Options", self)
        hbox = QtGui.QHBoxLayout()
        f=QtGui.QFormLayout();f_2=QtGui.QFormLayout()        
        self.spinBox = QtGui.QComboBox(self)
        self.spinBox.addItems(self.charges.keys())
        self.spinBox.setMaximumSize(QtCore.QSize(100, 200))
        f.addRow("charge:", self.spinBox)        
        self.lineEdit_2 = QtGui.QDoubleSpinBox(self)#QtGui.QLineEdit(self)
        self.lineEdit_2.setMaximumSize(QtCore.QSize(100, 200))
        self.lineEdit_2.setDecimals(3)
        self.lineEdit_2.setMaximum(1e5)        
        self.spin_hit = QtGui.QSpinBox(self)
        f_2.addRow("hits:", self.spin_hit)        
        self.checkIso = QtGui.QCheckBox(self)
        f.addRow("Isotopic comparison:", self.checkIso)
        f_2.addRow("ppm error:", self.lineEdit_2)
        hbox.addLayout(f);hbox.addLayout(f_2)
        gr4.setLayout(hbox)
        h.addWidget(gr4)
       
        
        #alphabet
        gr5 = QtGui.QGroupBox("Alphabet", self)
        vb4 =QtGui.QVBoxLayout()
        self.lineEdit_3 =QtGui.QLineEdit(self)
        self.lineEdit_3.setMaximumSize(QtCore.QSize(200,200))
        vb4.addWidget(self.lineEdit_3)
        self.push=QtGui.QPushButton("number of element", self)
        self.push.setMaximumSize(QtCore.QSize(200,200))
        vb4.addWidget(self.push)
        gr5.setLayout(vb4)
        h.addWidget(gr5)
        
        self.verticalLayout.addLayout(h)
        
        self.verticalLayout.addItem(QtGui.QSpacerItem(40,20))
        
        hb= QtGui.QHBoxLayout()
        # filtering
        gr1 = QtGui.QGroupBox("Filtering Options", self)
        self.checkBox_4 =QtGui.QCheckBox("idms filter", self)
        self.checkBox_6 =QtGui.QCheckBox("P filter(P-scanning)", self)
        self.checkBox_7 =QtGui.QCheckBox("Smiles filter", self)
        vb =QtGui.QVBoxLayout()
        vb.addWidget(self.checkBox_4)
        vb.addWidget(self.checkBox_6)
        vb.addWidget(self.checkBox_7)
        gr1.setLayout(vb)
        hb.addWidget(gr1)
       
        #databases
        gr2  = QtGui.QGroupBox("DataBases", self)
        vb2 =QtGui.QVBoxLayout()
        self.databases =QtGui.QLabel("Search in :")
        vb2.addWidget(self.databases)
        self.checkBox =QtGui.QRadioButton("KEGG", self)
        vb2.addWidget(self.checkBox)
        self.checkBox_2=QtGui.QRadioButton("Metabolome JP", self)
        vb2.addWidget(self.checkBox_2)
        self.checkBox_5=QtGui.QRadioButton("BioCyc", self)
        vb2.addWidget(self.checkBox_5)
        self.checkBox_8=QtGui.QRadioButton("Metexplore", self)
        self.comboBox=QtGui.QComboBox(self)
        conn=sqlite3.Connection('config/databases/metexplore.sqlite')
        c=conn.cursor()
        c.execute('select name from Organism')
        self.comboBox.addItems([e[0] for e in c])#"Homo sapiens")
        self.comboBox.setEnabled(False)
        vb2.addWidget(self.checkBox_8)
        vb2.addWidget(self.comboBox)
        gr2.setLayout(vb2)
        hb.addWidget(gr2)
        self.verticalLayout.addLayout(hb)
        
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)



    def launch_second(self):
        sec =SecondaryWidget("".join(map(str, self.lineEdit_3.text().split(','))),self.data, self)
        sec.exec_()
  


class SecondaryWidget(QtGui.QDialog):

    def __init__(self, alphabet, data, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.alphabet = alphabet
        self.line_edit =[]
        self.labels=[]
        self.data =data
        self.setupUi()

        
        self.connect(self.button_box, QtCore.SIGNAL("accepted()"),self.get_data)
        self.connect(self.button_box, QtCore.SIGNAL("rejected()"),self.close)
    
   
        
    def setupUi(self):
    
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.label=QtGui.QLabel("Enter wanted number of element (ie min-max):")
        self.verticalLayout.addWidget(self.label)
        for letter in self.alphabet:
            hl = QtGui.QHBoxLayout()
            label = QtGui.QLabel(letter+" :")
            self.labels.append(label)
            if letter in self.data.keys():
                n =QtGui.QLineEdit(self.data[str(letter)])
            else:
                n =QtGui.QLineEdit("1-30")
            self.line_edit.append(n)
            hl.addWidget(label)
            hl.addWidget(n)
            #self.data[label] = n
            self.verticalLayout.addLayout(hl)
        self.button_box =QtGui.QDialogButtonBox(self)
        self.button_box.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.button_box)
        
    def get_data(self):
        data={}
        for i in xrange (len(self.labels)):
            data[str(self.labels[i].text().split(" ")[0])] =str(self.line_edit[i].text())
        self.close()
        self.parent().data =data
        
