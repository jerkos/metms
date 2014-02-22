#-*-coding:utf-8-*-

"""
This file is part of metMS software.
Copyright: Marco
MetMS is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published 
by the Free Software Foundation, either version 3 of the License, 
or (at your option) any later version.

MetMS is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with MetMS. If not, see <http://www.gnu.org/licenses/>.


naming conventions(for developers):
all modules of this software start with the key-word 'Met'. So on, all 
classes name start with the prefix 'MS'. We use 'CapitalizeWords' for 
classes' name and 'mixedCase' for methods' name; variables and attributes, 
how we are used to.
in order keeping a readable code we strongly encourage developpers to 
avoid to prefix private attributes with two underscores (namespaces conflicts). 
"""

import numpy as np
import time
#from math import *
from collections import defaultdict
from core.MetObjects import MSPeakList, MSClusterList
from core.MetProcessing import massExtractionBisectAlgo, resolutionAdjustment
#from utils.bisection import bisection
from utils.bisection import abs, max, bisection
from utils.bisection import max_f, min_f, massGenPerGroup, makeAnnotations#_resolutionAdjustment, _getMatchingPeaks#massGeneration
#from core.isotopicFinder import bisection






def covMatrix(lspl, **k):
    """
    idea use the leastsq method to calculate the covariance matrix
    
    """
    #depacking the arguments
    rtError = k.get('rtError')
    ppm = k.get('ppm')
    matrix = []
    for sple in lspl:
        treatedPeaks=MSPeakList()
        for peak in sple.peaks:
            if peak not in treatedPeaks:
                peaks=MSPeakList()
                rValues =[]
                rValues.append((peak.mass(), peak.rt, sple.xmlfile))
                peaks.append(peak)
                for s in lspl:
                    if s != spl:
                        common = s.peaks.peakInMZRTRange(peak.mass(), peak.rt, ppm, rtError)
                        if len(common) > 1:
                            #do something eliminate some peaks to get the closest in rt and mz
                            treatedPeaks.extend(common)
                            peaks.extend(common)
                            if not common:
                                pass
                #treat peak
                for i in range(len(peaks)):
                    corr =0.
                    isosA, fragsA = peaks[i].isoAreaList(includeM0=True), peaks[i].fragAreaList()
                    for j in range(i+1, len(peaks)):
                        #mean of the frags and the iso 
                        #idea ponderate with the length more length more weighted
                        isosB, fragsB = peaks[j].isoAreaList(includeM0=True), peaks[j].fragAreaList()
                        corr+=r_coef(isosA, isosB)
                        corr+=r_coef(fragsA, fragsB)
                        rValues.append(corr/2.)
                        matrix.append(rValues)
    return matrix



def valueElimination(A, B):
    """
    in order to compute Pearson coefficient calculation, both vectors x, y must have the same dimension
    reducing dimension by removing values that are out of mean - var 
    """
    if len(A) == len(B):
         return A, B #no need to do something
    s = sorted([A,B], key=lambda x:len(x))
    shortest, longest = s[0], s[1]
    var= np.array(longest).var()
    mean = sum(longest)/len(longest)
    index = 0
    #newL = []
    while len(longest) > len(shortest):
        longest.pop()
    """
    while  index < len(longest):
        if longest[index] < mean + var or  longest[index] > mean - var :
             newL.append(longest[index])
        index +=1
    # if A still longer than B... remove the last values until both vector have the same dimension
    if len(newL) > len(shortest):
        
    #else:
    while len(newL) < len(B):
        for val in longest:
            if val not in newL:
                newL.append(val)
                break
    print "newl", len(newL), "shortest", len(shortest)
    """
    #return newL, shortest
    return longest, shortest

def r_coef(la, lb):
    """
    calculate r coef with numpy
    """
    if not la.shape[0] or not lb.shape[0]: 
        return 0.
    a, b = valueElimination(la.tolist(), lb.tolist())
    return np.corrcoef(a, b)[1][0]
    
    



#===============================================================================
#  CORRELATION
#===============================================================================
def intraSampleCorr(spl):
    for peak in spl.peaks.ipeaks():
        calcIntraR(peak)
        

    

def calcIntraR(peak):

    chrom = peak.sample.massExtraction(peak.mass(), peak.sample.ppm)
    x, y = chrom.sliceValues(peak.rtmin, peak.rtmax)
    pcorr,icorr,fcorr = 0.,0.,0.
    if peak.isoCluster:
        for iso in peak.isoCluster:
            chrom_ = peak.sample.massExtraction(iso.mass(), iso.sample.ppm)
            x_, y_ = chrom_.sliceValues(iso.rtmin, iso.rtmax)
            r = r_coef(y, y_)
            icorr+=r
            pcorr+=r
        #peak.isoCluster.intraR = icorr/len(peak.isoCluster)
    if peak.fragCluster:
        for frag in peak.fragCluster:
            chrom_ = peak.sample.massExtraction(frag.mass(), frag.sample.ppm)
            x_, y_ = chrom_.sliceValues(frag.rtmin, frag.rtmax)            
            r = r_coef(y, y_)
            fcorr+=r
            pcorr+=r
        #peak.fragCluster.intraR = fcorr/len(peak.fragCluster)
    #print "pcorr", pcorr
    if peak.fragCluster or peak.isoCluster:
        peak.r_coef = pcorr/(len(peak.isoCluster)+len(peak.fragCluster))
    else:
        peak.r_coef = pcorr
        


def interSamplesCorr(lspl, **kw):
    """
    TODO:redo that stuff
    take one reference then calculated 2 by 2 correlation
    
    """
    if not lspl:#can not calculate intercorrelation
        return 
    group = lspl.peaksGrouping()
    if not group:
        return
#    fcorr, icorr =[], []
#    for peaks in group.itervalues():
#        #for p in peaks
#        isosA, fragsA = p.isoAreas(includeM0=True), p.fragAreas(includeM0=True)
#        #mean of the frags and the iso 
#        #idea ponderate with the length more length more weighted
#        icorr.append(r_coef(isos, isosA))
#        fcorr.append(r_coef(frags, fragsA))
#    if fcorr:
#        peak.fragCluster.interR = sum(fcorr)/len(fcorr)
#    if icorr:
#        peak.isoCluster.interR = sum(icorr)/len(icorr)
        
				


#===============================================================================
#    ISOTOPIC AND IDMS FINDER
#===============================================================================

def difference(probability):
    ref = probability[0]
    return [probability[i]-ref for i in range(1, len(probability))]
        


def inSpectraFinder(peaks, isomasses, **k):
    """
    complementary algorihtm to look for isotopic 
    cluster in the sepctra rather than in the peak
    list, should be more effective
    """

    ppm=np.float(peaks[0].sample.ppm/1e6)        
    decreaseOrder = k.get('decreaseOrder', False) #we use the less restrictive...
    mode=peaks[0].sample.kind    
    MAX_GAP_ALLOWED = np.int(k.get('gap', 0) +1) #a gap definition to avoid gap 
    isomasses = sorted(isomasses, key=lambda x:x[0])
    
    for peak in peaks.ipeaks():#generator
        isores=[]#dict containing results for each spectra
        for i, s in enumerate(peak.ispectra()):
            
            gap=np.int(0)
            isos = defaultdict(float)#OrderedDict()
            #for i in range(1,3):#some testing if we are close or far
            p=s.massPeakInRange(peak.mass(), ppm * peak.mass())#list pairs(mass, intensity)
            
            if not p:
                #count+=1
                continue
        
            pmass, pintensity = sorted(p, key=lambda x: abs(x[0]-peak.mass()))[0]            
            
            #print "setting the base peak"
            isos[pmass]+=pintensity#= #setting the base peak
            #isores.append(matched)            
            
            if mode == 'Highres':
                errormass=(pmass*ppm)/1e6
                adjustedIsos = resolutionAdjustment(isomasses, errormass) if mode=='HighRes' else isomasses
            else:
                adjustedIsos = isomasses
            
            for isomass in adjustedIsos:
                #for i in range(1,3):
                m=s.massPeakInRange(pmass+isomass[0], (pmass+isomass[0])*ppm)
                    #if m:break
                #if m.size:
                if m:
                    mass = sorted(m, key=lambda x: abs(x[0]-(pmass+isomass[0])))[0]
                    if decreaseOrder:#majority
                        if isos[isos.keys()[-1]] < mass[1]:
                        #if isores[-1]<mass[1]:
                            break#idms found ???
                    isos[mass[0]]+=mass[1] #= #mass:intensity pairs 
                    #isores.append(mass)
                else:#no peak found in this spectra
                    gap+=1
                    if gap >MAX_GAP_ALLOWED:
                        break
            isores.append(isos) 
        #isores=resolutionAdjustment(isores, ppm, adaptError=True)
        if isores:
            s=sorted(isores, key=lambda x:len(x))
            ref, isoext = s[-1], s[:-1] #take the longest one
            #if ref:
            #isoext = [x for x in isores if x != ref] #extraction
            for d in (x for x in isoext):#xiterates over dictionnaries
                
                checked=set()
                
                for mp in d.iterkeys():#iterates over masses
                    mp_included =False
                    
                    for mprime in ref.iterkeys():#iterate over reference
                        t = ppm * max(mprime,mp) if mode =='HighRes' else 2
                        if abs(mprime-mp) < t:#ppm * max(mprime,mp) :#mError#considering they are the same, change 
                            
                            if mprime in checked:
                                continue
                            #if mprime not in checked:
                            ref[mprime]+=d[mp]
                            checked.add(mprime)
                            mp_included=True
                            break
                    
                    if not mp_included:
                        ref[mp]+=d[mp]
            #setting the isotopes
            peak.isoSpectra= ref.items()#[(key, val) for key, val in ref.iteritems()]
        else:
            print ("no masspeak found in corresponding spectra for peak %s"%str(peak))
            print ("This peak may not be good !")
            peak.isGood=False
    return peaks
            


def isotopicPeakListFinder(peaks, isomasses, **kwargs):
    """
    assign an isotopic cluster for each peak, and try to find an idms
     we may use a system like the CAMERA algorithm to see...
    input:
        list of peak must an obj.MSPeakList object
        clusterLength = 6  never go to six in LOW_RES
                        size expected of an isotopic cluster
        rtError: maximum drift of the retention time
        decreaseOrder: allow or not allow that the successive peak of the isotopic cluster
                        intensity are going down, can be confusing for finding idms
    output:
        two MSPeakList, the first one corresponding to the peaks with an isotopic cluster
        and the other one all peaks belonging to an isotopic cluster
    """
   
    #unpacking parameters
    print "Isotopic cluster calculation..."
    
    rtError = np.float(kwargs.get('rtError', 6))
    ppm=np.float(peaks[0].sample.ppm/1e6)
    MAX_GAP_ALLOWED = np.int(len(isomasses))
    decreaseOrder = kwargs.get('decreaseOrder', True)  #we use the less restrictive...
    mode =  kwargs.get('mode', 'Highres')
    #sort isomasses
    #isomasses = sorted(isomasses, key=lambda x:x[0])
    
    peaks_with_iso =MSPeakList()               
    peaks_without_iso = MSPeakList()#peaks without isotopic cluster but which does not have a isotopic cluster
    list_iso = set()#MSPeakList()

    t = time.clock()    
    
    for peak in peaks.ipeaks():#iterating over peaks
        
        if peak in list_iso:
            continue#avoid to calculate for every peaks
        
        isoCluster= MSClusterList()
        gap = 0
        #isos = resolutionAdjustment(isomasses, peak.mass()*ppm) if mode=='HighRes' else isomasses
        for i, isomass in enumerate(sorted(isomasses, key=lambda x:x[0])):
            #pic = _getMatchingPeaks(peaks, peak, isomass[0], ppm, rtError)
            
            mass=isomass[0]
            massToCheck=peak.mass()+mass
                        
            p = peaks.peaksInMZRange(massToCheck, deltam=ppm*massToCheck if mode=='HighRes' else 1.) #deltart
            matchingRtPeaks = MSPeakList()#will contain all matching peak in rt
            for pk in p.ipeaks():
                if pk != peak:
                    if abs(peak.rt - pk.rt) <= rtError:
                        matchingRtPeaks.append(pk)
            
            if matchingRtPeaks:
         
                pic = sorted(matchingRtPeaks, key=lambda pics: abs(pics.mass()-peak.mass()))[0] #take the closest in mass
                if pic is not None:
                    if decreaseOrder:#we want peak area inferior a peak
                        #if isoCluster:
                        areaToCompare=isoCluster[-1].area if isoCluster else peak.area 
                        if areaToCompare < pic.area:#idms found ???
                           break
                      
                    if pic not in list_iso:#pic not in isoCluster and
                        isoCluster.append(pic)
                        list_iso.add(pic)
            else:
                gap+=1
                if gap >=MAX_GAP_ALLOWED:
                    break
        
        # #set parent for all peaks found
        if isoCluster:
            for pics in isoCluster:
                #pics.parentPeak=peak
                pics.parentPeak.append(peak)
            peak.isoCluster = isoCluster
            peaks_with_iso.addPeak(peak)
        else:
            peaks_without_iso.addPeak(peak)
      
    
#    for p in peaks.ipeaks():
#        if p not in peaks_with_iso and p not in list_iso:
#            peaks_without_iso.addPeak(p)
    
    
    print time.clock()-t
    print "peaks with isotopes: " ,len(peaks_with_iso)
    print "list isotopes: " ,len(list_iso)
    print "peaks without isotopes: " ,len(peaks_without_iso)
    return peaks_with_iso+peaks_without_iso, list_iso

                    

#===============================================================================
#     CAMERA CLUSTERING      
#===============================================================================
def clusteringCAMERA(peaks, adducts, **kwargs):
    """
    arguments needed:
        error_rt:rt_ drift
        ppm:precision
        useCorrelation: if we calculate correlations
    """
    t=time.clock()
    #unpack parameters
    error_rt = kwargs.get('rtError', 6)
    #ppm = float(kwargs.get('ppm'))/10**6
    ppm=peaks[0].sample.ppm/1e6
    mode=kwargs.get('mode', 'HighRes')
    resolveConflicts=kwargs.get('resolveConflicts', False)
    peaks_with_iso=peaks
    print "peaklist length",len(peaks)
    adducts_to_check=np.array(adducts.keys())
    #===========================================================================
    #START CAMERA ALGORITHM
    print ("RT Grouping ...")
    #RT_peak=peaks_with_iso.rtClustering(error_rt)
    #3,find for each peak peaks which matches with retention time
    rtPeak =[]
    for i, peak in enumerate(peaks_with_iso.ipeaks()):
        
        l=MSPeakList()
        l.addPeak(peak)
        for j, peak_ in enumerate(peaks_with_iso.ipeaks()):
            if i!=j:
                if abs(peak.rt - peak_.rt) < error_rt:
                    l.append(peak_)
        isIncluded=False
        index=[]        
        for k, rtClust in enumerate(rtPeak):
            if  set(l)<=(set(rtClust)):#inclusion test of l already in rt ? seen as 'equivalent to'
                isIncluded=True
                break
            
            if set(rtClust) <= (set(l)):
                index.append(k)
                #break
        #del rtPeak[index]
        rtPeak= [rtPeak[i] for i in xrange(len(rtPeak)) if i not in index] 
        if not isIncluded:        
            rtPeak.append(MSPeakList(l))
                #isIncluded=True
            #else:
            #    if rtClust.__eq__(l):
            #        rtPeak[k]=l
            #        break                    
                    #isIncluded=True
        #if not isIncluded:
            #l.sort(key=lambda x:x.mass())
            
    
#    with open('test1.txt', 'w') as f:
#        for r in rtPeak:
#            s=""
#            for i, p in enumerate(r):
#                s+=str(p)+';' if i<len(r)-1 else str(p)+'\n'
#            f.write(s)

    #EXPERIMENTAL CODE            
#    cl=[]
#    for cluster in rtPeak:
#        list_=[];datapoints={}
#        for i, p in enumerate(cluster):
#            correspondingPeaks=set()
#            correspondingPeaks.add(p)
#            for j in xrange(i+1, len(cluster)):
#                #put caching on that to avoid recalculation each time of the datapoints
#                try:
#                    r=r_coef(list(datapoints[p]), list(datapoints[cluster[j]]))
#                except KeyError:
#                    y, y_= None, None                    
#                    try:
#                        y=datapoints[p]                        
#                    except KeyError:                        
#                        x, y= massExtractionBisectAlgo(p.sample,p.mass(), ppm)
#                        datapoints[p]=y
#                        
#                    try:
#                        y_=datapoints[cluster[j]]
#                    except KeyError:
#                        x, y_= massExtractionBisectAlgo(cluster[j].sample, cluster[j].mass(), ppm)
#                        datapoints[cluster[j]]=y_
#                    r=r_coef(y, y_)
#                if r >= threshold:
#                    correspondingPeaks.add(cluster[j])
#            list_.append(correspondingPeaks)
#        
#        for i, p in enumerate(list_):
#            for j in xrange(i+1, len(list_)):
#                if list_[j].issubset(p):
#                    continue
#                else:
#                    cl.append(MSPeakList(list(p)))
    #merging step again
#    print "cluster length, same without replicates",len(cl), len(set(map(set, [x for x in cl])))
#    with open('test2.txt', 'w') as f:
#        for r in cl:
#            s=""
#            for i, p in enumerate(r):
#                s+=str(p)+';' if i<len(r)-1 else str(p)+'\n'
#            f.write(s)
#            
    #END EXPERIMENTAL CODE
    print 'len RTpeak', len(rtPeak)
    print ("Creating possible M0...")
    #Cython code
    finalList = massGenPerGroup(rtPeak, adducts_to_check, ppm)   
    print("Mapping of calculated mass on peaklist...")
    #4,see if one matches with peak in the raw peaklist
    goodPeak=[]#list will contain good peak per rtCluster    
    for i, dic in enumerate(finalList):
        matchingMass=defaultdict(list)
        for mass in dic.iterkeys():
            p = rtPeak[i].peaksInMZRange(mass, deltam=mass * ppm if mode=='HighRes' else 1.)#rtPeak[i] not necessarily sorted warning
            if not p:
                continue
            peak=sorted(p, key=lambda x:abs(mass - x.mass()))[0]
            #if peak not in matchingMass.keys():#may avoid this to see if one peak appears several times !then do 'set'
            #    matchingMass[peak]=[]                    
            matchingMass[peak] += dic[mass]
        goodPeak.append(matchingMass)
    
    #start new stuffs here
    print ("Merging informations...")
    #conflicts=False
    adds=MSPeakList()#object sor storing adducts found    
    newGoodPeaks=defaultdict(list)#{}
    for peaksInOneRtGroup in goodPeak:
        for peak in peaksInOneRtGroup.iterkeys():
            newGoodPeaks[peak] += peaksInOneRtGroup[peak]            
    for p in newGoodPeaks.iterkeys():
        p.fragCluster=MSClusterList(list(set(newGoodPeaks[p])))
        for f in p.fragCluster:
            f.parentPeak.append(p)
        adds += p.fragCluster
    finalPeaks=MSPeakList(newGoodPeaks.keys())
        
    print ("Resolving conflicts if any...")
    #removing peak that appears many times that is to say in different clusters
    def clusterComparison(list_):#receive a list of peak with clusters identified
        """
        return the best peak
        WARNING: p_ydata and p_.y_data are None
        TODO: 
        
        """        
        sortedList = sorted(list_, key=lambda x: len(x.fragCluster))
        longest=len(sortedList[-1].fragCluster)
        sameSizePeaks=MSPeakList()        
        
        for p in sortedList:
            if len(p.fragCluster) == longest:
                sameSizePeaks.append(p)
        
        if len(sameSizePeaks) == 1:
            return sameSizePeaks[0]
        corr=np.array([0.] * len(sameSizePeaks))
        #for i, p in enumerate(sameSizePeaks):
        #    for p_ in p.fragCluster:
        #        corr[i] += r_coef(p_.y_data, p.y_data)
        m=max_f(corr)
        return sameSizePeaks[np.where(corr == m)[0][0]]
                
    if resolveConflicts:
        for add in set(adds):
            if len(add.parentPeak) <= 1:
                #print "%s belong to several fragCluster"%str(add)
                continue
            #print "%s belong to several fragCluster"%str(add)
            goodParent=clusterComparison(add.parentPeak)
            #if goodParent is not None:
            #    add.parentPeak = [goodParent]            
            
            for parent in add.parentPeak:
                if parent != goodParent:
                    try:
                        parent.fragCluster.remove(add)
                    except ValueError:
                        print "Error removing %s from fragCluster of %s"%(str(add), str(parent))
            add.parentPeak = [goodParent] #the same of constructing a list 'toRemove then remove
            #print "after removing len add.parentPeak", len(add.parentPeak)
                    

    #make the annotation
    for peak in finalPeaks.ipeaks():
        for f in peak.fragCluster:
            #results = makeAnnotations(adducts_to_check, adducts, f.mass(), ppm)
            for annot in adducts.iterkeys():
                p = f.mass() / annot[1] + annot[0]
                diff = peak.mass()*ppm if mode =='HighRes' else 1
                if peak.mass() > p-diff and peak.mass() < p+diff:
                    f.annotation[annot]=adducts[annot]
                    break
    finalPeaks=checkingSons(finalPeaks)
    #5,second filter, correlation on the isotopic cluster between samples
#    if useCorrelation:
#        print "Calculating correlation between samples..."
#        interSamplesCorr(spl, **kwargs)
#        print  "Calculating correlation intra sample..."
#        intraSampleCorr(spl)
#    #6 merging
    print "Merging interesting peaks"
    for peak in peaks_with_iso.ipeaks():#wring merging must take out those which allow to construct this peak
        if peak not in finalPeaks and peak not in adds:#matching_peaks:
            finalPeaks.append(peak) #matching_peaks to
    if not finalPeaks:
        print ("no cluster found, please increase the ppm, or rt drift parameters")
    print ("finished, time elapsed:",time.clock()-t)
    return MSPeakList(sorted(finalPeaks, key=lambda x:x.mass)), adds#checkingSons(finalPeaks), adds


def clusteringWrapper(sample, **kw):
    """
    convenience function wrapping isotopic finders
    fragment adducts finder, put the data in MetHelperFunctions
    """
    badPeak=kw.get('badPeak', False)
    kw['mode'] = sample.kind
    mode = kw['mode']
    adducts = kw.get('frags')#contains the union of frags and adducts values
    clusterLength=kw.get('clusterLength', 3)
    isomasses=[]
    if mode=='HighRes': #tuple(mass, prob, nmol) nmol for calculating 2M+Na+ for example
        m=[(1.0033548378, 0.0107), (2.003241988,0.), #C Element
           (1.006276746, 0.000115), (2.008224235,0.), #H Element
           (0.997034893, 0.00368), #N Element
           (1.004216878,0.00038), (2.004245778,0.00205), #O Element, P got no isotopes
           (0.99938781,0.0076), (1.99579614,0.0429), (3.99501019,0.0002)] #S Element        
        for i in range(1, clusterLength+1):#setting isotopic stuffs 
            isomasses+=([(x[0]*i, x[1]**i) for x in m if x[0]*i < clusterLength])
       
    else:
        isomasses = [(float(i), 0.) for i in xrange(1, clusterLength+1)]#map(float, range(1, clusterLength+1))            
#        adducts={(18., 1):'H20', 
#                 (44.,1):'CO2',
#                 (79.,1):'PO3',
#                 (90.,1):'' ,
#                 (70.,1):'', 
#                 (68.,1):'', 
#                 (60.,1):'', 
#                 (59.,1):'', 
#                 (46.,1):'', 
#                 (45.,1):'', 
#                 (35.,1):'', 
#                 (32.,1):'', 
#                 (28.,1):'', 
#                 (17.,1):'', 
#                 (16.,1):'', 
#                 (14.,1):''}
        #change the adducts to be a dictionnary
    #isomasses.sort(key=lambda x:x[0])
    p= sample.rawPeaks if badPeak else MSPeakList([peak for peak in sample.rawPeaks if peak.isGood])
    sample.mappedPeaks, sample.isotopicPeaks = isotopicPeakListFinder(p, isomasses, **kw)#first remove isotopicPeaks in peaklist
    sample.mappedPeaks, sample.adductPeaks=clusteringCAMERA(sample.mappedPeaks, adducts, **kw)#second remove fragment/adducts off the peaklist
    print "raw vs mapped:", str(len(sample.rawPeaks)), str(len(sample.mappedPeaks))



def checkingSons(peaks):
    """
    
    bring back both, actually works, may be used only for the display
    and not inside the data structure
    
    """
    toRemove=MSPeakList()
    
    def recursiveMerging(root):
        if not root in toRemove:
            for frag in root.fragCluster:
                if frag.fragCluster:
                    toRemove.addPeak(frag)
                    for son in frag.fragCluster:
                        if son != root:
                            root.fragCluster.append(son)
                            #toRemove.addPeak(son)#dont know if it is really necessary
                        #else:
                        #    print "must do other not yet implemented"
                    root.fragCluster=MSPeakList(list(set(root.fragCluster)))
                    recursiveMerging(frag)#before was just one step ahead                    
            return
        return
    for peak in peaks:
        recursiveMerging(peak)
    lastPeakList=MSPeakList()
    for p in peaks:
        if p not in toRemove:
            lastPeakList.append(p)
    return sorted(lastPeakList, key=lambda x:x.mass())


def clusteringBASIC(peaks, adds, **k):
    
    if not peaks:
        return
    t=time.clock()
    errorRt = k.get('rtError', 6)
    #ppm = float(kwargs.get('ppm'))/10**6
    ppm = k.get('ppm')
    if ppm is None:
        try:        
            ppm = peaks[0].sample.ppm/1e6
        except AttributeError:
            print "No value found for ppm setting to 10/1E6"
            ppm = 10./1e6
    #mode = k.get('mode', 'HighRes')
    resolveConflicts=k.get('resolveConflicts', False)
    addsToCheck=np.array(adds.keys())
    
    adductsFound = MSPeakList()    
    for i, p in enumerate(peaks):
        a = MSClusterList()        
        for v in addsToCheck:
            m = p.mz+v[0]
            match = peaks.peaksInMZRTRange(m, p.rt, errorRt, deltam= 2 * ppm * m)
            if match is None or not match:
                continue
            #take the closest in mass
            goodP = sorted(match, key=lambda x:abs(x.mz - (p.mz + v[0])))[0]
            #if goodP in set(adductsFound):
            #    if resolveConflicts:
            #        pass
            #else:
            if goodP is p:
                continue
            a.append(goodP)
            goodP.parentPeak=p
            adductsFound.append(goodP)
        p.fragCluster=MSPeakList(set(a))#prevent from duplicates
        
#    def clusterComparison(list_):#receive a list of peak with clusters identified
#        """
#        return the best peak
#        WARNING: p_ydata and p_.y_data are None
#        TODO: 
#        
#        """        
#        sortedList = sorted(list_, key=lambda x: len(x.fragCluster))
#        longest=len(sortedList[-1].fragCluster)
#        sameSizePeaks=MSPeakList()        
#        
#        for p in sortedList:
#            if len(p.fragCluster) == longest:
#                sameSizePeaks.append(p)
#        
#        if len(sameSizePeaks) == 1:
#            return sameSizePeaks[0]
#        corr=np.array([0.] * len(sameSizePeaks))
#        #for i, p in enumerate(sameSizePeaks):
#        #    for p_ in p.fragCluster:
#        #        corr[i] += r_coef(p_.y_data, p.y_data)
#        m=max_f(corr)
#        return sameSizePeaks[np.where(corr == m)[0][0]]
#        
#        if resolveConflicts:
#            for add in set(adductsFound):
#                if len(add.parentPeak) <= 1:
#                    #print "%s belong to several fragCluster"%str(add)
#                    continue
#                #print "%s belong to several fragCluster"%str(add)
#                goodParent=clusterComparison(add.parentPeak)
#                #if goodParent is not None:
#                #    add.parentPeak = [goodParent]            
#                
#                for parent in add.parentPeak:
#                    if parent != goodParent:
#                        try:
#                            parent.fragCluster.remove(add)
#                        except ValueError:
#                            print "Error removing %s from fragCluster of %s"%(str(add), str(parent))
#                add.parentPeak = [goodParent] #the same of constructing a list 'toRemove then remove
#                #print "after removing len add.parentPeak", len(add.parentPeak)
    print "TiemElapsed: %s"%str(time.clock()-t)
    return peaks, adductsFound
        




