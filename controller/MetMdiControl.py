#usr/bin/python

from PyQt4.QtCore import SIGNAL, QObject
from PyQt4 import QtGui

from controller.MetBaseControl import MSBaseController

class MSMdiAreaController(MSBaseController):
    """
    Handles mdi area control
    """
    
    def __init__(self, model, view):
        MSBaseController.__init__(self, model, view)
        
    def _buildConnections(self):
        pass
        #QObject.connect(self.view.mdiArea, SIGNAL("customContextMenuRequested(const QPoint &)"), self.view.mdiArea._handleContextMenu)
        #QObject.connect(self.view.mdiArea._contextMenu.actions()[0], SIGNAL("triggered()"), self.view.mdiArea.tileSubWindows)
        #QObject.connect(self.view.mdiArea._contextMenu.actions()[1], SIGNAL("triggered()"), self.view.mdiArea.cascadeSubWindows)
        #QObject.connect(self.view.mdiArea._contextMenu.actions()[2], SIGNAL("triggered()"), self.view.mdiArea.closeAllSubWindows)

    
    

