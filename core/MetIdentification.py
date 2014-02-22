# -*- coding: utf-8 -*-




#This file is part of metMS software.
#Copyright: Marco, Fabien Jourdan, Fabien Létisse, Pierre Millard
#MetMS is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published 
#by the Free Software Foundation, either version 3 of the License, 
#or (at your option) any later version.

#MetMS is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with MetMS. If not, see <http://www.gnu.org/licenses/>.





__author__ = ("marco", "cram@hotmail.fr")
__version__ = "$Revision:1" 



"""
Module implementing the identification module
the aim of this module is to try to identify interesting peaks
we generate several formulas for one mass and then apply several filters on it
like smiles formulas nb of phosphate group in the, idms ,... 
"""




#import subprocess
#import sys
#import os, os.path as path
#from copy import deepcopy

#from numpy import array, convolve
#from PyQt4.QtCore import SIGNAL

#from core import MetObjects as obj
from controller.MetBaseControl import MSModel
#from core import MetProcessing as proc
#from core.MetObjects import MSSample
#from core.generator import pyFormulaGenerator
from core.MetDataObjects import MSFormula



"""module varibales level"""



class MSIdentificationModel(MSModel):
    """
    launching the formula generator
    and compare to the databases        
    get all data needed from the controller by the dict processing parameters    
    @peaks we are working on
    @charge: +1 negative mode
    @mmu: incertitude on the mass
    @hit: numbers of hit wanted
    @Pscanning: filter on the P number when generates formulas
    @alphabet :alphabet used when generates formulas
    """
    
    #SCRIPT_ISO=path.normcase('core/iso_v2.py')
    #ISO_FILE='isos.txt'
    #FORMULA_FILE='formula.txt'
    idModelLabel = ("score", "formula", "mass", "rt", "difference", "name", "url")

    
    def __init__(self, spl=None, **k):
        MSModel.__init__(self, spl, parent=self)
        
        
        self.peaks=self.model.mappedPeaks if self.model.mappedPeaks else self.model.rawPeaks
             
        #unpack parameters
        #first tools stuffs
        if self.model.kind=='HighRes':
            self.charge=k.get("charge")
        else:
            self.charge=1. if self.model.polarity=='negative' else -1.

            
        #self.lastConvolveElement=k.get("lastConvolve")
        self.ppm = k.get("ppm")/1e6 #jut have to * mass after
        self.hit = k.get("hit")
        self.checkIsos = k.get("checkIsos")

        #to be performed or not
        self.PScanning =k.get("phos")
        self.idmsCheck = k.get("idms")
        self.smilesCheck =k.get("smiles")
        
        #databases and alphabet
        #self.allElements=k.get('allElements')
        self.alphabet = k.get("alphabet")
        self.parserKegg = k.get("databases")["KEGG"]
        self.parserBioCyc = k.get("databases")["BIOCYC"]
        self.parserMetjp = k.get("databases")["METJP"]
        self.metexplore=k.get("databases")['METEXPLORE']
        #self.resolution = processingParameter["res"]
        
        self.data = k.get('data') #number of each element
        
     
        self.url = "http://www.genome.jp/dbget-bin/www_bget?cpd:" #for information        

        
        
    

    
    def mappingObsOnCalcPattern(self, calc, obs, errormass):
        '''mapped mass between observed and calculated isotopic pattern
        better than put a threshold on the intensity of the masspeak'''
        newcalc, newobs =[], []
        check=[]
        if obs:
            for m, p in obs:
                val = errormass#self.ppm*m*2 #? i dont know what to do with myself
                for mass,prob in calc:
                    if abs(m-mass) < val:#good
                        if mass not in check:
                            newcalc.append(prob)
                            newobs.append(p)
                            check.append(mass)
                            break
        return newcalc, newobs#only the probability

    
    
    def isotopicPatternComparison (self, formula, peak, error=0.25):
        """
        calculate score for each formula
        TODO: take in charge the Na+
        """
        
        def norm(l, value):
            for i, m in enumerate(l):
                l[i]=m/float(value)
            
        f=formula.copy()
        if self.charge > 0:
            f.removeElement(self.alphabet.element('H'))
        else:
            f.addElement(self.alphabet.element('H'))
        
        mp=f.patternGeneration(f.calcMass()*self.ppm)#proc.isoPatternCalculation(f)
        
        err=None        
        if self.model.kind=='HighRes':
            err=self.ppm*peak.mass()
        elif self.model.kind=='MRM':
            err=.5
        
        #adjustmass = proc.resolutionAdjustment(mp, err)
        calc_pattern, obs_pattern= self.mappingObsOnCalcPattern(mp, peak.isoSpectra, err)#adjustmass,return uniquement les probas
        
        #normalisation
        if calc_pattern and obs_pattern:
            norm(calc_pattern, max(calc_pattern))
            norm(obs_pattern, max(obs_pattern))
       
        #calc_pattern = calc_pattern/calc_pattern.sum()
        errors=[]#actually not use to
        test = reversed(range(1, len(calc_pattern)))
        for obs, calc in zip(obs_pattern, calc_pattern):
            p = (max(obs, calc) - min(obs, calc))/max(obs, calc)
            errors.append(p)
        
        score = 0.            
        for i, value in enumerate(obs_pattern):
            score += pow(value - calc_pattern[i], 2)
            #if errors[i] > error:
            #    score+=error[i]*test[i]# penalize...depends on the place
        formula.score = score if score != 0. else 10.
       

    
    def recursiveFragmentChecker(self, peak):
        """return recursively actually that's works"""        
        nP= 1 if  self.PScanning else 0
        nOH, nC =0, 0 
        
        def updateValues(peak, nP, nOH, nC):
              for i, frag in enumerate(peak.fragCluster):
                    diff = abs(peak.mass() - frag.mass())
                    #check for phosphate                
                    if diff == 80. or diff == 97.:nP +=1
                    #check for watter
                    if diff == 18.:nOH+=1
                    #check for CO2 loss
                    if diff == 44.:nC+=1
              return nP, nOH, nC
        
        def __rec(peak, nP, nOH, nC):
           i=0
           while i < len(peak.fragCluster):
               nP, nOH, nC = updateValues(peak, nP, nOH, nC)
               __rec(peak.fragCluster[i], nP, nOH, nC)
               i+=1
           return nP, nOH, nC
                   
        return __rec(peak, nP, nOH, nC)
                    
          
    def smilesChecker(self, formula):
        """
        to see if it is the same as recursive fragment checker
        see if its accord
        """        
        pass 
    
    
    
    
    def updateData(self, symbol, min_value, max_value):
        """update data object data for generating formulas (min, max) values)
        TODO Warning"""
        
        try:        
            self.currentData[symbol] = "-".join([str(min_value), str(max_value)])
        except KeyError:
            print ("Symbol not found: %s in %s"%(symbol, self.currentData.keys()))
        

    
    def rangeUpdate(self, peak):
        #prevent conflict !!TODO
        #for P Scanning and OH
        np, noh, nC= self.recursiveFragmentChecker(peak)
        self.updateData("P", max(np, int(self.currentData['P'].split('-')[0])), self.currentData["P"].split("-")[1])
        self.updateData("O", max(noh, int(self.currentData['O'].split('-')[0])), self.currentData["O"].split("-")[1])
        self.updateData("H", max(noh, int(self.currentData['H'].split('-')[0])), self.currentData["H"].split("-")[1])
        
        #handles idms !!        
        if self.idmsCheck:
            self.updateData("C", peak.idms, peak.idms)
    
    
    @staticmethod
    def dictToString(d):
        """
        may be useful if we care about the order of the key...
        """
        
        s = ""
        for i, key in enumerate(d.iterkeys()):
            s+= key+" "+d[key]+" " if i<len(d) else key+" "+d[key]
        return s
    
    
    
    
    def identification (self, model=None, error =0.02):
        """
        Main Function
        """
       
        import time
        t = time.clock()
        #line = 0
        
        for i,peak in enumerate(self.peaks.ipeaks()):

            self.currentData=dict(self.data)
            self.rangeUpdate(peak)# P scan, idms, see if its in agreement of smiles pattern? 
                        
            mfg = pyFormulaGenerator(peak.mass()+self.charge, self.ppm*1e6, self.dictToString(self.currentData)) 
            #apply Fiehn's Seven Golden Rules
            data= [MSFormula(x) for x in mfg.do_calculations()]
            if not data:
                continue
            for formula in data:
                #1 Isotopic Pattern Filter (the two previous steps have been done with the formula generator)
                if self.checkIsos:#not really necessary ?
                    self.isotopicPatternComparison(formula, peak, error)
                #2 idms done when generates formulas
                #4 smiles 
            data.sort(key =lambda x:x.score)#lowest are the best #sorting by score
            filtered=data[:int(self.hit)]#take only the hit ieme first matching
            for formula in filtered:
                formulaMass=formula.calcMass()
                data, name = self.searchInDatabase(str(formula))#databases search
                url, names ="", ""
                #first kegg
                if data:
                    if not peak.isFoundInDatabase:
                        peak.isFoundInDatabase = True
                    for d in data:
                        if name == 'KEGG':
                            url += self.url +d["ENTRY"]+"\n"
                        if "NAME" in d.keys():
                            names += d["NAME"] if d["NAME"].endswith('\n') else "".join([d["NAME"],"\n"])
                            #formula.compounds.append(d["NAME"])
                        
                else: 
                    names+="Not Found"
#                    from csv import QUOTE_NONE, writer, writerow
#                    if i==0:
#                        writer(open(self.OUPUT_FILE, 'wb'), delimiter=';', quoting=QUOTE_NONE)
#                        writerow(MSSample.idModelLabel)
#                    else:
#                        writer(open(self.OUPUT_FILE, 'ab'), delimiter=';', quoting=QUOTE_NONE)
#                        writerow([str(formula.score), str(formula), str(peak.mass()),str(peak.rt), names,url])
                #peak.formulas.append(formula)
                d = {"score":formula.score, "diffmass":formulaMass-(peak.mass()+self.charge), "names":names}
                #peak.formulas={}
                peak.formulas[str(formula)] = d
            del mfg
            #lastPeak=newPeak if newPeak else None
        #self.cleanUp()#just clean temporary files
        print "ident elapsed time",time.clock()-t    

    
    @staticmethod
    def setNonEditable(table_id):
        for i in xrange (table_id.rowCount()):
            for j in xrange (table_id.columnCount()):
                if table_id.item(i, j):
                    table_id.item(i, j).setEditable(False)
                
            
    def searchInDatabase(self, formula):
        """
        get matching formula
        several matches are observed for one formulas (isomers)        
        
        """
        kegg, met_jp, biocyc, metexplore=[],[],[],[]
        
        #first kegg database
        if self.parserKegg:
            for data in  self.parserKegg._genData():
                if data["FORMULA"] ==formula:
                    kegg.append(data)
            return kegg, "KEGG"
        
        #second metjp database
        if self.parserMetjp:
            for data in self.parserMetjp.idata():
                if data["FORMULA"] == formula:
                    print "found", data['NAME']
                    met_jp.append(data)
            return met_jp, "MET_JP"
        
        
        if self.parserBioCyc:
            for data in self.parserBioCyc.data:
                if data["FORMULA"] == formula:
                    biocyc.append(data)
            return biocyc, "BIOCYC"
        
        if self.metexplore:
            for key in self.metexplore.iterkeys():
                if key==formula:
                    metexplore.append({"NAME":self.metexplore[key]})
                    print "found", key, self.metexplore[key]
            return metexplore, "METEXPLORE"
        
        