#!usr/bin/python

"""Processing functions essentially differents ways to construct chromatograms
and spectra"""

__version__ = '$Revision1'
__author__ = ('marco', 'cram@hotmail.fr')

import string

from numpy import (array, arange, convolve, ones, matrix, ediff1d, sort, r_,
                   hanning, hamming, bartlett, blackman, diff, vstack, int)
#import numexpr as ne
from numpy.random import normal
from PyQt4.QtCore import QThread, SIGNAL

import MetObjects as obj
#from utils.MetHelperFunctions import memo, bisection
from utils.decorators import memo
from utils.bisection import bisection, mean, sum_f



def asAMatrix(spl):
    if isinstance(spl, obj.MSSample) or not spl.spectra:
        return
    matrix_=[]
    for spectrum in spl.spectra:
        matrix.append(spectrum.x_data)
    return matrix(matrix_)
        
        




def chromatoCreation(scans, *args):
    """create all chromatograms, little bit slow"""
    chromatoList = []
    clusters = {}
    for scan in scans:
        if not (scan.precursor(), scan.fragment()) in clusters.keys():
            clusters[(scan.precursor(), scan.fragment())] = [], []
        clusters[(scan.precursor(), scan.fragment())][0].append(scan.rt())
        clusters[(scan.precursor(), scan.fragment())][1].append(scan.intensity())
    for keys in sorted(clusters.iterkeys()):
            chromatogram= obj.MSChromatogram(x_data=array(clusters[keys][0]), 
                                             y_data=array(clusters[keys][1]),
                                             massrange=(keys[0], keys[1], 0.),
                                             sample=args[0])
            chromatoList.append(chromatogram)
    del clusters
    return chromatoList




def loadOneChromato(scans, trans_prec):
    """return only one chromatogram specified by the value as argument"""
    """FIXME:see if trans_prec could not be a transition object """
    x =array('f', )
    y =array('f', )
    transition = None
    for scan in scans:
        transition = obj.MS2Transition(tuple(scan.precursor(), scan.fragment()))
        if scan.precursor() == trans_prec:
            x.append(scan.rt)
            y.append(scan.intensity)
    if not x and not y:
        raise ValueError("Requested Values do not exist")
    yield obj.MSChromatogram(x, y, transition)



def chromCreationsBySpectra(spectra, mass):
    """avoid to create all the chromatograms loaded dynamically"""
    x_data = array('f',)
    y_data = array('f',)
    if isinstance(mass, obj.MS2Transition):
        transition = mass
    else:
        transition = obj.MS2Transition([mass,0])    
    for spectr in spectra:
        for x, y in zip(spectr.x_data, spectr.y_data):
            if x == mass:
                x_data.append(spectr.rt_min)
                y_data.append(y)
    return obj.MSChromatogram(x_data, y_data, transition=transition)




def spectraCreation(scans, min_time, max_time, time_window, sample=None):
        """create all spectra"""
        
        time_windows = []
        groupedScan = {}
        spectrumList = []
        time=float(min_time)
        time_windows.append(time)
        
        while float(max_time) - time > time_window:
            time += time_window
            time_windows.append(time)
        #lost_time=float(max_time) - time_windows[-1]
        
        real_scan = max_range=0
        last_key = (time_windows[1], time_windows[2]) # initialisation allow first iteration
        for scan in scans:
            real_scan += 1
            while time_windows[max_range] < scan.rt() and max_range < len(time_windows)-1:
                    max_range += 1
            key=(time_windows[max_range-1], time_windows[max_range])
            if key != last_key:
                groupedScan[key] = [], []
            groupedScan[key][0].append(scan.precursor())
            groupedScan[key][1].append(scan.intensity()) #obj.Data2D change to add only required Fields
            last_key = tuple(key)
        for key in sorted(groupedScan.iterkeys()):
            spectr= obj.MSSpectrum((key[0], key[1], 0.),array(groupedScan[key][0]), array(groupedScan[key][1]), sample=sample)
            spectrumList.append(spectr)
        del groupedScan
        return spectrumList




def highResSpectraCreation(sample, masses, intensities, indexes, tot_intensity, scan_acquisition_time):
    """simply create scans object from extracted data from a netcdf files"""
    spectra = []
    for i in range(len(indexes)-1):
        spectrum = obj.MSSpectrum((scan_acquisition_time[i],
                                   scan_acquisition_time[i+1],
                                   0.),
                                  masses[indexes[i]:indexes[i+1]], 
                                  intensities[indexes[i]:indexes[i+1]],
                                  sample=sample)
        spectra.append(spectrum)
    return spectra




    
def massExtractionBisectAlgo(sample, mass):#, massrange):
    """
    mass: mass to consider
    massrange: error on mass, 0.01 ? typically for high resolution 
    """
    x_data,y_data=[],[]
    diff=(sample.ppm*mass)/1e6
    for spectrum in sample.ispectra():
        i = bisection(spectrum.x_data, mass, mass-diff, mass+diff)#massrange, mass+massrange)
        if i:
            for indexes in i:
                x_data.append(spectrum.rt_min)
                y_data.append(spectrum.y_data[indexes])
    return x_data, y_data
    
    

def applyCutOff(data, value):
    """FIXME:think about optimization"""
    import warnings
    warnings.warn("Lead to a lost of information")
    return [t for t in (t for t in data) if t[1]> value]
        
import math
def applyLog(data, base=math.e):
    import warnings
    warnings.warn("Lead to a lost of information")
    return [math.log(t, base) for t in (t for t in data)]

    
    
def readXCMSPeaks(file, lspl, keep_failure=True):
    """
    doing the same than function up, but using a MSParserBasis
    ??? still gonna use this ?
    """    
    
    reader = MSParserBasis(file, sep=";")
    def checkString(string):
        if ',' in string:
            if LOW_RES:
                return string.split(",")[0]
            else:
                return string.replace(',','.')
        return string
    
    """needed...strange"""
    #for spl in lspl:
    #    spl.peaks = obj.MSPeakList()
    
    reader.parsing(interestingFields=['"into"', '"rtmin"', '"rt"', '"rtmax"', '"mz"', '"sample"'])
    #assume the several files to parse are in the order
    for dict_ in reader._genData():
        i = int(dict_['"sample"'])-1
        xdata =None; ydata=None; chromatogram=None
        try:
            if len(lspl[i].chroma) >1:
                chromatogram = lspl.sampleWithTransition(lspl[i].xmlfile, 
                                                        float(checkString(dict_['"mz"'])))
            
                x_data, y_data = chromatogram.sliceOnValues(
                                                            float(checkString(dict_[ '"rtmin"'])), 
                                                            float(checkString(dict_['"rtmax"']))
                                                       )
            peak = obj.MSChromatographicPeak(float(checkString(dict_['"rt"'])), 
                                             float(checkString(dict_['"rtmin"'])), 
                                             float(checkString(dict_['"rtmax"'])), 
                                             obj.MS2Transition((float(checkString(dict_['"mz"'])),0)), 
                                             float(checkString(dict_['"into"'])),
                                             x_data=xdata,
                                             y_data=ydata,  
                                             chromatogram=chromatogram)
            lspl[i].peaks.append(peak)
        except ValueError:
            print ("Unexpected Error du to XCMS")
  
        
    
    
def mergingPeaks(lspl):
    peaks = obj.MSPeakList()
    for spl in lspl:
        peaks.extend(spl.peaks)
    return peaks    
        

def mergingChroma(lspl):
    chrom =[]
    for spl in lspl:
        chrom.extend(spl.chroma)
    return chrom
    
    
def mergingSpectra(lspl):
    spectr =[]
    for spl in lspl:
        spectr.extend(spl.spectra)
    return spectr





class GLVertexCalculation(QThread):
    """rewrite passing only spectra by reference!
        rewrite using numpy    
    """
    def __init__(self, spectra=None, parent=None, **kw):
        QThread.__init__(self, parent)
        self.spectra = spectra
        self.massList=[]
        self.intensityList=[]
        self.rtList=[]
        self.corner_ = 100.
        self.near_ = 0.
        self.far_ = 600.
                        

        def extremeValueOf(list_, callable_):
            return callable_(map(callable_,list_))
            
           
        self.max_rt = max([spectrum.rtmin for spectrum in (spectra for spectra in self.spectra)])
        self.max_mass = extremeValueOf([spectrum.x_data for spectrum in (spectra for spectra in self.spectra)], max)
        self.min_mass = extremeValueOf([spectrum.x_data for spectrum in (spectra for spectra in self.spectra)], min)
        self.max_intensity = extremeValueOf([spectrum.y_data for spectrum in (spectra for spectra in self.spectra)], max)

    
    def normProcess(self):
        for spectrum in (spectra for spectra in self.spectra):
            self.massList.append(self._norm(spectrum.x_data, 2*self.corner_, self.max_mass, flag="mass"))
            self.intensityList.append(self._norm(spectrum.y_data,self.far_ -self.near_ -4*self.corner_, self.max_intensity))
            self.rtList.append(self._norm([spectrum.rtmin], 2*self.corner_, self.max_rt))
        
    def _norm(self, x_data, value, max_value, flag="Bouh"):
        """to rewrite lol"""
        data=[]
        for x in x_data:
            if flag == "mass":
                a = x - self.min_mass
                b = max_value - self.min_mass
            else:
                a = x
                b = max_value
                
            if a == b:
                data.append(a/b)
            else:
                data.append((a * value)/b)
        return data

    def vertexAndColors(self, *args, **kwargs):
        from utils.misc import Ice, Fire, Hot, IceAndFire, Grey
        self.vertexList, self.colors =[], []
        min_, max_ = min(map(min, self.intensityList)), max(map(max, self.intensityList))
        for i, mass_of_spectrum in enumerate(self.massList):
            
            for j, mass in enumerate(mass_of_spectrum):
                self.vertexList.append([ - self.corner_ +  mass, 
                                         -self.corner_, 
                                         - self.near_- 2*self.corner_ - self.rtList[i][0]])
                     
                self.vertexList.append([ - self.corner_ + mass, 
                                   - self.corner_ + self.intensityList[i][j], 
                                   - self.near_- 2*self.corner_ - self.rtList[i][0]])
        
                color =IceAndFire._get_color(self.intensityList[i][j]/max_)
                for n in xrange(2):
                    self.colors.append(color)
            QThread.usleep(10)
    
    
            
            
    def run(self):        
        self.normProcess()
        self.vertexAndColors()
        #self.surface()        
        self.emit(SIGNAL('end_calc'), self.vertexList, self.colors)
        



#===============================================================================
#                           ISOTOPIC PATTERN CALCULATION
#===============================================================================

def isotopicPatternCalculation(formula):
    """
    formula as a dict {C:6 ....}
    abundoncy as a dict {C: [0.98...,...]} determined by the reading file config element
    """
    
    massif = array([1.])
    for key in formula.iterkeys():
        for i in xrange (formula[key]):
            massif = convolve(key.abundoncy, massif)
    return massif


def highResIsotopicPatternCalculation(formula,limitp=0.0001, ppm=10., fwhm=10):
    l= isotopicClusterCalc(formula, limitp)    
    return resolutionAdjustment(l, ppm, fwhm)



def fastCalc(formula, limitp, fast):
    """
    isotopic pattern using factorial and denumbering
    """
    def comb(n, k):
        """
        combinaison C(n, k)= n!/(n-k)!k!
        """
        @memo
        def fact(n):
            if n < 2:
                return 1
            return n*fact(n-1)
            
        return fact(n)/(fact(n-k)*fact(k))
    
    results=[]
    for element in formula:
        atomcount = formula[element]
        for i in range (atomcount):
            peaks=[] #contains all masses, prob for this starting point
            nb = comb(atomcount, atomcount-i) #combinaison avec 1, 2 ... atoms of C12 for example
            peaks.append((nb*element.isomass[i],element.abundoncy[i]**nb))#probability of having nC12
            for j in range(i+1, len(element.isomass)):
                nb_iso=comb(atomcount, atomcount-i-j) #number of next isotope
                mass = nb*element.isomass[j]#calculation of the mass
                p = element.abundoncy[j]**nb_iso#calculation of the probability
                if p > limitp:
                    peaks.append((mass,p))
            mass, p = 0.,1.
            for peak in peaks:
                mass+=peak[0]
                p*=peak[1]
            results.append((mass,p))
    return results                
                
import string

#formula={"el_1":14,"el_2":2,"el_3":2,"Ca":5,"O":4} # formule elementaire de la molecule
limitp=1e-6

#mass={"el_1":[1.001,2.003], "el_2":[12.,13.01], "el_3":[14.012,15.023],"O":[15.994915,16.999131,17.999159],"Ca":[39.962591,41.958622,42.958770,43.955485,45.953689,47.952532]} # masse des differents isotopes de chaque element
#ab={"el_1":[0.95,0.05], "el_2":[0.9893,0.0107], "el_3":[0.9925,0.0075],"O":[0.99757,0.00038,0.00205],"Ca":[0.96941,0.00647,0.00135,0.02086,0.00004,0.00187]} # proportion des differents isotopes de chaque element


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

    
def resolutionAdjustment(l, errormass, fwhm=None, limitp=1e-6, adaptError=False):
    """
    merge peaks when the distance between them is inferior to the deltam parameter
    to test, but seems to be good...
    l : np.array of tuple (mass, prob)
    ppm: incertitude on the mass high res: generally (10/10**6)*peak.mass()
    fwhm:  for the convolution...to have a nice isotopic cluster
    
    
    the following numpy code is slower than the last one keep the last one!
     
        #masses=l[:,0];prob=l[:,1]
        #sortindexes=masses.argsort()    
        #masses=masses[sortindexes]#sort(l[:,0]) #avoid to loose l ?
        #prob=prob[sortindexes]
    #    sortedlist = sorted(l, key=lambda x:x[0])      
    #    #difference=diff([s[0] for s in sortedlist]).tolist()
    #    difference=[]
    #    for i in xrange (1,len(sortedlist)):
    #        difference.append(sortedlist[i][0]-sortedlist[i-1][0])
    #    #s=difference<errormass#boolean slice
    #    #indexes=s.where(difference)[0]
    #    final=[]
    #    N=len(difference)
    #    i=0    
    #    while i<N:
    #        n=i
    #        while difference[i]<errormass and i<N:
    #            #print s.size, i 
    #            i+=1
    #        mass=sum([s[0] for s in sortedlist[n:i+1]])/len(sortedlist[n:i+1])
    #        prob=sum([s[1] for s in sortedlist[n:i+1]])        
    #        final.append((mass, prob))
    #        i+=1
    #    return final
    """
        

    sortedlist = sorted(l, key=lambda x:x[0])
    final=[]
    i=int(0)
    n = int(len(sortedlist))
    while i < n-1:#we miss the last one...
        m, M= sortedlist[i], sortedlist[i+1]
        peaks=[]
        errormass=M[0]*errormass if adaptError else errormass
        while M[0]-m[0] < errormass and i < n-2:
            peaks.append(m); peaks.append(M)
            i+=1
            m, M =sortedlist[i], sortedlist[i+1]      
        if peaks:
            peaks = array(peaks)
            mass=mean(peaks[:,0] * peaks[:,1])#ponderate mean peak[0]*peak[1]
            prob=sum_f(peaks[:,1])
            if mass > limitp:
                final.append((mass,prob))
        else:
            final.append(m)
            if i == n-2:
                final.append(sortedlist[n-1])
        i+=1
    
    #lastone = final if final else sortedlist
    #return reversed(sorted(final, key=lambda x:x[1]))#final sorted by the largest peak in the first place an then decrease 
    #final.sort(key=lambda x:x[1]); #final.reverse()
    return final
#    if fwhm:
#        return array([x[0] for x in final]), convolve(array([x[1] for x in final]), normal(scale=fwhm))



#=================================================================================
#               Calculations
#=================================================================================


