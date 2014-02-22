import sys
from PyQt4 import QtCore, QtGui
#import gui
#import Wiff_To_mzXMLConverter

class controller_gui_conversion:
    
    def __init__(self, widget):
        self.widget = widget
        
        self.initialisation()
        
        QtCore.QObject.connect(self.widget.buttonBox, QtCore.SIGNAL("accepted()"),self.Conversion)
        QtCore.QObject.connect(self.widget.buttonBox, QtCore.SIGNAL("rejected()"),self.Quit)
        QtCore.QObject.connect(self.window.pushButton_3, QtCore.SIGNAL("clicked()"),self.Scanning)
        QtCore.QObject.connect(self.window.pushButton_8, QtCore.SIGNAL("clicked()"),self.ReScanning)

        
    def initialisation(self):
        self.widget.textEdit_2.setText(self.widget.InstructionsOpt())
        

    def Conversion(self):
        args=self.window.lineEdit.text()
        opt=self.window.lineEdit_2.text()
        list_a=list(self.conv.DEFAULT_OPT)
        if args!="":
            list_a += args.split(" ")
        listing_files=self.conv.StudyInput(opt)
        self.conv.LaunchingConversion(args, listing_files)
    
    def Quit(self):
        self.widget.close()
        return

if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    con=controller_gui_conversion()
    con.tabwidget.show()
    app.exec_()

