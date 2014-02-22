#!/usr/bin/env python
# -*- coding: utf-8 -*-

#python import
import os.path as path
import glob
import imp

#handling errors loading plugins
class MissingPluginAttributesError(Exception):
    def __init__(self):
        Exception.__init__(self)
        print ("Plugin module must have at least a 'autoActivation ' and 'className' slots")

class LoadPluginError(Exception):
    def __init__(self):
        Exception.__init__(self)
        print ("Load plugin failure")

#plugin manager
class MSPluginManager(object):
    
    plugins_path = path.normcase('pluginmanager/plugins/')
    
    def __init__(self, parent = None):
        self.parent = parent
    

    def cleanCompiledPlugins(self):
        pass
        
    def getAvailablePlugins(self):
        plugins = [plugins for plugins in glob.glob("".join([self.plugins_path, 'Plugin*.py']))] 
        if not plugins:
            print ("No plugin detected")
            return []
        return plugins
        
    
                
    def loadPlugin(self, model, view, plug, moduleName):
    
        mod = imp.load_source(moduleName, plug)
        if not getattr(mod, "className") or not getattr(mod, "autoActivation"):
            raise MissingPluginAttributesError
            
        className = getattr(mod, "className")
        pluginClass = getattr(mod, className)
        pluginObject = pluginClass(model, view, parent=self)
        return pluginObject

#template for creating plugins
class MSPlugin(object):
    def __init__(self, model, view, parent =None):
        """
        template class for creating different kind of Plugins
        @view:QMainWindow
        @model:MSSampleList
        """
        self.parent = parent
        self.view = view
        self.model = model
        self.guiWidgets=[]
        
    def _buildConnections(self):
        raise NotImplementedError
    
    def _guiUpdate(self):
        """add code for updating the gui"""
        raise NotImplementedError
        
    def unload(self):
        """
        define here what you have to do to unload your module
        default implementation        
            
        """
        for e in self.guiWidgets:
            e.setParent(None)
            del e
        
    def pluginAlgorithm(self):
            raise NotImplementedError
