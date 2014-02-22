#!usr/bin/python
#-*-coding:utf-8-*-

import re
from copy import deepcopy
import xml.dom.minidom
import os.path as op
import csv

 #object for handling smiles data
class MSSmilesFormulas(str):
    """C([O-])(=O)C1(=CC=C2(C(=C1)C(=O)C3(C(C2=O)=CC=CC=3)))"""
    """class attributes """    
    
    carboxyPattern=set(('C(=O)O', 'C([O-])(=O)', 'C(=O)[O-]'))
    alcoholPattern=set(('OH', 'HO'))
    phosphatePattern=set(())    
    CHEMICAL_FUNCTIONS=op.normcase("config/config/chemical_functions.csv")
    
    def __init__(self, smiles, parent=None):
        str.__init__(self, smiles)
        self =[symbol.upper() for symbol in self if symbol.islower()]#transformation lower to upper case

        self.formula = parent
        self.compound=None
        
    @classmethod 
    def readPattern(cls):
        reader=csv.reader(open(cls.CHEMICAL_FUNCTIONS, 'rb'), delimiter=',')
        for i, patterns in enumerate((cls.carboxyPattern, cls.alcoholPattern, cls.phosphatePattern)):        
            for el in reader[i]:            
                patterns.add(el)
    
    @classmethod     
    def addFunction(cls, func, list_):
        try:
            getattr(cls, list_).append(func)
        except AttributeError:
            print ('MSSmilesFormula has no attributes %s'%str(list_))
    

    def carboxyPatternChecker(self):
        carboxy =0
        for pattern in self.carboxyPattern:
            carboxy+=self.carboxyPattern.count(pattern)            
        return carboxy
    
    def alcoholPatternChecker(self):
        O_O =0
        for pattern in self.alcoholPattern:
            O_O+=self.alcohol.count(pattern)
        return O_O

        


class MSElement(object):
    """represent an Element example: C, O, H"""
    
    def __init__(self, mass, isotopemass, abundoncy, symbol, name=""):
        if not isinstance(symbol, str):
            raise TypeError("Symbol must be a String")
            
        self.symbol =symbol
        self.name =name
        self.massMo=mass[0]#monisotopic mass
        self.massAv=mass[1]#average mass
        self.abundoncy=abundoncy
        self.isomass=isotopemass
        self.atomicNumber=None
        
    def __str__(self):
        return "/".join([self.symbol, str(self.mass)])
    
    def __eq__(self, el):
        if el.symbol==self.symbol:
            return True
        return False
    
    def toString(self):
        string=''
        string+=" ".join([self.name,'\n'])
        string+="".join([str(self.atomicNumber), '\n'])
        string+="".join([str(self.massAv),'\n'])
        string+="".join([str(self.massMo),'\n'])
        string+="Mass/Prob\n"
        for m, p in zip(self.isomass, self.abundoncy):
            string+="/".join([str(m), str(p)+'\n'])
        return string



class MSAlphabet(list):
    """represent the used alphabet to find metabolites, this is a list of element"""
    
    ELEMENTS= op.normcase('config/config/elements.xml')
    
    def __init__(self, el =[]):
        list.__init__(self, el)        
    
    @classmethod
    def withElements(cls, elements=['C', 'H', 'N', 'O', 'P', 'S']):
        if elements:
            if not all([isinstance(el, str) for el in elements]):
                raise TypeError, "must be a list of string object"

        document = xml.dom.minidom.parse(cls.ELEMENTS)
        elementTags = document.getElementsByTagName('element')
        
        al=[]
        for x, elementTag in enumerate(elementTags):
        
            name = elementTag.getAttribute('name')
            symbol = str(elementTag.getAttribute('symbol'))
            atomicNumber = elementTag.getAttribute('atomicNumber')
            
            massTags = elementTag.getElementsByTagName('mass')
            massMo = float(massTags[0].getAttribute('monoisotopic'))
            massAv = float(massTags[0].getAttribute('average'))
            mass = (massMo, massAv)
            
            isotopes = []#;iso=[]
            massiso =[]            
            #isotopes[massNumber] = (imass,abundance)
            isotopeTags = elementTag.getElementsByTagName('isotope')
            for isotopeTag in isotopeTags:
                #massNumber = isotopeTag.getAttribute('massNumber')
                imass = float(isotopeTag.getAttribute('mass'))
                massiso.append(imass)                
                abundance = float(isotopeTag.getAttribute('abundance'))
                isotopes.append(abundance)
          
            if not elements:
                e=MSElement(mass, massiso, isotopes, symbol, name);e.atomicNumber=atomicNumber
                al.append(e)
            else:
                if symbol in elements:
                    e=MSElement(mass, massiso, isotopes, symbol, name);e.atomicNumber=atomicNumber
                    al.append(e)
        return cls(al)
    
    def __str__(self):
        return "".join([el.symbol for el in self])
    
    def element2string(self):
        """to avoid possible mistakes when element's symbol
            contains several letters """
        return set([element.symbol for element in self])
    
    def addElement(self, element):
        if not isinstance(element, MSElement) and not isinstance(element, str):
            raise TypeError("Element must be an Element or str object")
        string=element.symbol if isinstance(element, MSElement) else element
        if string in self.element2string:
            return
        self=MSAlphabet(self+MSAlphabet.withElements([string]))
        self.sort(key=lambda x:x.symbol)

    
    def removeElement(self, element):
        if not isinstance(element, MSElement) and not isinstance(element, str):
            raise TypeError("Element must be an Element or str object")
        string=element.symbol if isinstance(element, MSElement) else element
        if string not in self.element2string:
            return
        toRemove=None
        for el in self:
            if string==el.symbol:
                toRemove=el
        self.remove(toRemove)
    
    def element(self, symbol):
        for el in self:
            if el.symbol==symbol:
                return el
        return None









#===============================================================================
# Formula
#===============================================================================
import string
from numpy import convolve

limitp=1e-6

def fact(n):
    if n < 2:
        return 1
    else:
        return n*fact(n-1)

def filter_p(l_p,l_mass,limitp):
    index=[i for i,p in enumerate(l_p) if p<limitp] # liste des index des masses pour lesquelles p<limitp
    index.reverse()
    for i in index: # supprime les masses pour lesquelles p<limitp (on multiplie ensuite par une valeur <1 donc le resultat sera obligatoirement inferieur a limitp)
        l_p.pop(i)
        l_mass.pop(i)
    return (l_p,l_mass)


def isoPatternCalculation(f):
    mass=dict((element.symbol, element.isomass) for element in f)
    ab=dict((element.symbol, element.abundoncy) for element in f)
    formula=dict((element.symbol, f[element]) for element in f)
    groups={}
    for element in formula:
        if len(mass[element])==1: # cas ou il y a 1 isotope par element
            groups[element]=([1.],[mass[element][0]*formula[element]])
        elif len(mass[element])==2: # cas ou il y a 2 isotopes par element
            l_p,l_mass=[1.],[]
            for i in range(formula[element]):
                    l_p=convolve(l_p,ab[element])
            l_mass=[mass[element][0]*(formula[element]-j)+mass[element][1]*j for j in range(len(l_p))]
            groups[element]=filter_p(list(l_p),l_mass,limitp)
        else: # pour les elements ayant plus de 2 isotopes
            l_mass,l_p=[],[]
            n,at,a,indent=formula[element],len(mass[element]),1,len(mass[element])-1
            l_fact=[fact(i) for i in range (n+1)] # calcul des factorielles
            l_C=[[l_fact[i]/(l_fact[j]*l_fact[i-j]) for j in range (i+1)] for i in range(n+1)] # creation de la liste de combinaisons
            t="".join("\t"*i+"for "+string.ascii_lowercase[i+1]+ " in range(n+"+"-".join(string.ascii_lowercase[j] for j in range(i+1))+"):\n" for i in range(at-1))
            t+="\t"*(indent)+"p=l_C[n][b]*ab[element][0]**b*"+\
                "*".join("l_C[n-"+"-".join(string.ascii_lowercase[j] for j in range(1,i+1))+\
                "]["+string.ascii_lowercase[i+1]+\
                "]*ab[element]["+str(i)+"]**"+string.ascii_lowercase[i+1] for i in range(1,at-1))
            t+="*ab[element][-1]**(n-"+"-".join(string.ascii_lowercase[i+1] for i in range(at-1))+")\n"
            t+="\t"*(indent)+"m="+"+".join("mass[element]["+str(i)+"]*"+string.ascii_lowercase[i+1] for i in range(at-1))
            t+="+mass[element][-1]*(n-"+"-".join(string.ascii_lowercase[i+1] for i in range(at-1))+")\n"
            t+="\t"*(indent)+"if m not in l_mass:l_mass.append(m);l_p.append(p);\n"
            t+="\t"*(indent)+"else:l_p[l_mass.index(m)]+=p;"
#                print(t)
            exec t.strip() in globals(), locals()
            groups[element]=filter_p(l_p,l_mass,limitp)

#calcul du massif isotopique de la molecule en combinant les massifs generes par les differents elements
    iso_clust={}
    i=len(groups)-1
    t="".join("\t"*i+"for "+string.ascii_uppercase[i]+","+string.ascii_lowercase[i] + " in enumerate(groups['"+j+"'][0]):\n" for i,j in enumerate(groups.keys()))
    t+="\t"*(i+1)+"p="+"*".join(string.ascii_lowercase[l] for l in range(len(groups)))
    t+="\n"+"\t"*(i+1)+"if p>limitp:"
    t+="\n"+"\t"*(i+2)+"m="+"+".join("groups['"+m+"'][1]["+string.ascii_uppercase[l]+"]" for l,m in enumerate(groups.keys()))
    t+="\n"+"\t"*(i+2)+"iso_clust[m]=iso_clust.get(m,0.)+p"
    #print(t)
    exec(t) in globals(), locals()
    
    return  [(m, p) for m, p in iso_clust.items()]


class MSFormula (dict):
    """
    Representation of element, metabolite
    """

    def __init__(self, formula, smiles=None, alphabet=MSAlphabet.withElements(['C','H','N','O','P','S'])):
        #change the formula(string) to object dict
        dict.__init__(self)
        self.alphabet = alphabet #alphabet of the formula (used symbol)    
        reg = re.compile('([A-Z]|[A-Z][a-z])(\d+)')
        if '.' in formula:
            for splitted in formula.split('.')[:-1]:
                if reg.match(splitted):
                    for element in self.alphabet:
                        if element.symbol == reg.match(splitted).group(1):
                            self[element] = int(reg.match(splitted).group(2))
                            break
                else:
                    try:
                        from PyQt4.QtGui import QApplication
                        QApplication.instance().view.showErrorMessage('Error', 
                        "Unknown error: formula is obviously not good...")
                    except ImportError:
                        raise ValueError, "Unknown error: formula is obviously not good..."
        else:
            try:
                from PyQt4.QtGui import QApplication
                QApplication.instance().view.showErrorMessage('Error',
                "MSFormula Object must contain '.' to separate the different elements")
            except ImportError:
                raise ValueError, "MSFormula Object must contain '.' to separate the different elements"
        
        self.mass=None #mass of the formula
        self.smiles=smiles #smiles formula
        self.score=None #score
        self.compounds=[]  #will ba list of string (name)
        self.peaksGroup=None
    
    
    def calcMass(self, average=False):
        mass=0.     
        if average:
            for element in self.iterkeys():
                mass+=element.massAv*self[element]
            return mass
        for element in self.iterkeys():
            mass+=element.massMo*self[element]
        return mass
                
    def allElement(self):
        return [el.symbol for el in self.iterkeys()]        
    
    def isIdentified(self):
        return not len(self.identifiers) == 0
        
    def numberOf(self, symbol):
        if symbol in self.alphabet:
            for element in self.iterkeys():
                if symbol == element.symbol:
                    return self[element]
    
    def __str__(self):
        formula =""
        for element in sorted(self.keys(), key=lambda x:x.symbol):
            formula += element.symbol
            if self[element] > 1:
                formula += str(self[element])
        return formula
    
    def addElement(self, element, nb=1):
        found=False
        for el in self.keys():
            if el.symbol==element.symbol:
                self[el]+=nb
                found=True
                return
        if not found:
            self[element]=nb
    
    def removeElement(self, element):
        for el in self.keys():
            if el.symbol==element.symbol:
                if self[el] == 1:
                    del self[el]
                else:
                    self[el]-=1
                return
        print("element %s not found in formula %s"%(element.symbol, self.allElement()))
        
    def copy(self):
        return deepcopy(self)
    
    
    def resolutionAdjustment(self, l, errormass, fwhm=None):
        """
        merge peaks when the distance between them is inferior to the deltam parameter
        to test, but seems to be good...
        l : list of tuple (mass, prob)
        ppm: incertitude on the mass high res: generally (10/10**6)*peak.mass()
        fwhm:  for the convolution...to have a nice isotopic cluster  
        """
        sortedlist = sorted(l, key=lambda x:x[0])
        final=[];i=0
        while i < len(sortedlist)-1:#we miss the last one...
            m, M= sortedlist[i], sortedlist[i+1]
            peaks=[]
            while M[0]-m[0] < errormass and i <len(sortedlist)-2:
            #while M[0]-m[0] < ppm*M[0] and i <len(sortedlist)-2:
                peaks.append(m); peaks.append(M)
                i+=1
                m, M =sortedlist[i], sortedlist[i+1]      
            if peaks:
                mass=sum([peak[0] for peak in peaks])/len(peaks)#ponderate mean peak[0]*peak[1]
                prob=sum([peak[1] for peak in peaks])
                #if mass >0.:
                final.append((mass,prob))
            else:
                final.append(m)
                if i == len(sortedlist)-2:
                    final.append(sortedlist[len(sortedlist)-1])
            i+=1
        
        #lastone = final if final else sortedlist
        #return reversed(sorted(final, key=lambda x:x[1]))#final sorted by the largest peak in the first place an then decrease 
        #final.sort(key=lambda x:x[1]); #final.reverse()
        return final
#    if fwhm:
#        return array([x[0] for x in final]), convolve(array([x[1] for x in final]), normal(scale=fwhm))
    def patternGeneration(self, ppm, limitp=15e-6):
        #from MetProcessing import resolutionAdjustment, isoPatternCalculation
        self.mass=self.calcMass()
        limitp=limitp
        mp=isoPatternCalculation(self)
        return mp#self.resolutionAdjustment(mp, self.mass*ppm/1e6)


