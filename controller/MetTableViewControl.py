#usr/bin/python



from PyQt4.QtCore import *
from PyQt4.QtGui import *


from controller.MetBaseControl import MSBaseController


class MSTableViewController(MSBaseController):
    """
    class for handling event of the cluster table
    """
    
    def __init__(self, table_, spl, charge):
        MSBaseController.__init__(self, spl, table_)
        self._buildSpecialConnections()
        self.charge = charge
    


    def _buildSpecialConnections(self):    
        """connection"""
        self.connect(self.view.pushButton_2, SIGNAL("clicked()"), self.export_to_csv)
        self.connect(self.view.pushButton, SIGNAL("clicked()"), self.compute_selection)
        self.connect(self.view.table_view, SIGNAL("clicked(const QModelIndex &)"), self.ShowToolTip)
        
    
    def ShowToolTip(self, index):
        index_data = str(self.view.table_view.model().data(index, Qt.DisplayRole).toString()).split('\s')
        QToolTip.showText(QCursor.pos(), '\n'.join(index_data))
    
    @pyqtSlot()
    def export_to_csv(self):
        fileName = QFileDialog.getSaveFileName(self.view, "Save file")
        with open(fileName,'w') as fd:
            for i in xrange(self.model.idModel.rowCount()):
                for j in xrange(self.model.idModel.columnCount()):
                    if j <= self.model.idModel.columnCount()-1:
                        fd.write(self.model.idModel.item(i,j).text())+ ";"
                    else:
                        fd.write(self.model.idModel.item(i,j).text())+"\n"  
    
    
    def compute_selection(self):
        """
        will redraw the entire table using an itemdelegate
        """
        threshold = self.view.combobox.currentText()
        
        index_list =[]
        if threshold == "Peaks found":
            for i in xrange(self.view.model.rowCount()):
                if self.view.model.item(i, 5):
                    data = self.view.model.item(i, 5).data(Qt.DisplayRole).toString()
                    list_index =[]
                    if  data != "Not Found" and data !="":
                        for  j in xrange(self.view.model.columnCount()):
                            list_index.append(self.view.model.indexFromItem(self.view.model.item(i, j)))
                    index_list.extend(list_index)
                    
        elif threshold == "Peaks with isotopic cluster":
            transition_list = self.model.get_peak_list().as_trans_list()
            for i in xrange(self.view.model.rowCount()):
                if self.view.model.item(i, 1):
                    data = self.view.model.item(i, 1).data(Qt.DisplayRole).toString()
                    if data in transition_list:
                        for j in xrange(self.view.model.columnCount()):
                            index_list.append(self.view.model.indexFromItem(self.view.model.item(i, j)))
                            
        elif threshold == "Peaks with fragment/adduct cluster":
            for i in xrange(self.view.model.rowCount()):
                if self.view.model.item(i, 1) and self.view.model.item(i, 0):
                    data = self.view.model.item(i, 1).data(Qt.DisplayRole).toString()
                    rt = self.view.model.item(i, 0).data(Qt.DisplayRole).toString()
                    peak =self.model.get_peak_list().is_peak(float(data)-self.charge, float(rt))
                    if peak and len(peak.get_frag_cluster()):
                        for j in xrange(self.view.model.columnCount()):
                            index_list.append(self.view.model.indexFromItem(self.view.model.item(i, j)))
        
        
        elif threshold == "Peaks with high correlation values inter_sample":
            for i in xrange(self.view.model.rowCount()):
                if self.view.model.item(i, 1) and self.view.model.item(i, 0):
                    data = self.view.model.item(i, 1).data(Qt.DisplayRole).toString()
                    rt = self.view.model.item(i, 0).data(Qt.DisplayRole).toString()
                    peak =self.model.get_peak_list().is_peak(float(data)-self.charge, float(rt))
                    if peak and peak.get_frag_cluster().get_inter_corr() !="NA":
                        if peak.get_frag_cluster().get_inter_corr() > 0.5:
                            for j in xrange(self.view.model.columnCount()):
                                index_list.append(self.view.model.indexFromItem(self.view.model.item(i, j)))
                    
        delegate = Found_Peak_Delegate(self.view.table_view, index_list)
        self.view.table_view.setItemDelegate(delegate)
        self.view.table_view.repaint()
        

class Found_Peak_Delegate(QItemDelegate):
    """
    Special class for drawing colored cells in the table view
    """
    
    def __init__(self, parent, index_list):
        """Constructor, empty just want to define paintEvent method"""
        
        QStyledItemDelegate.__init__(self, parent)
        self.index_list = index_list
        
    def paint(self,  painter, option, index):
        """
        have to be reimplemented
        """
        
        if index in self.index_list:
        #if value >= self.threshold:
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

