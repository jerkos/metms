#!usr/bin/python
# -*- coding: utf-8 -*-

__author__ =("marco", "cram@hotmail.fr")



'''
Module implementing all mass spectrometry basics objets

''' 
#import os.path as path
from os import stat
import base64, struct

from xml.etree.cElementTree import iterparse
from io import open
from re import compile
from time import clock
from collections import defaultdict
from os.path import normcase
import numpy as np
from cmath import exp#, log

from scipy.optimize import leastsq
from scipy.integrate import quad
from scipy.ndimage import gaussian_filter1d as gaussSmoothing
from scipy.io import netcdf
from scipy.cluster.vq import kmeans2

#from graphics.MetMplCanvas import MSQtCanvas
from utils.decorators import slots, check#, guiDependant, sampleDependant, deprecated
from utils.misc import timeFormat, OrderedDict 
from utils.bisection import (abs,  _peaksInRtRange, mean, _loadSpectrum, _getAllEic)#, bisection)#_linearModel, _quadraticModel,
from dtw._dtw import Dtw #dynamic time warping
from core.libc import bisect, massExtract


'''
Constants
'''
MEAN_FWHM=12
MEAN_RTSHIFT=6


def _linearModel(p, x):
    return p[0]*x + p[1]


def _quadraticModel(p, x):
    return p[0] * x**2 + p[1] * x + p[2]


def _polynomialFit(p, x, order=3):
    if order > len(p):
        raise ValueError
    for i in reversed(xrange(order)):
        x += p[-i] * x**i
    return x

def _residuals(p, x, y):
    w = _polynomialFit(p, x)
    err = w - y
    err = err**2
    return err.sum()




class MSTransition(list):
    """
    Transition object used for MRM Data
    
    """
    @slots
    def __init__(self, masses=[], chroma=None):
        list.__init__(self, sorted(masses))
        if len(self) ==2:
            self.precursor=self[0]
            self.fragment=self[1]
        self.chroma=chroma#MSChromatogram expected here
                
    def __str__(self):
        return '/'.join(reversed([str(f) for f in self]))
    
    def __eq__(self, obj):
        """take in charge the inclusion"""
        return MSTransition(set(self).intersection(obj))
    
    def __neq__(self, obj):
        return not self == obj
    
    def msDegree( self):
        return len(self) 

      
    
class MSPeakList(list):
    """
    List of peaks(represents all peaks found by 
    XCMS software, provide some useful functions 
    for manipulating peaks data
    
    """
    @slots
    def __init__(self, pkl=[], sample=None):
        """
        Constructor, derivating from list object
        
        """
        list.__init__(self, pkl)
        self.sort(key=lambda x:x.mass())#sort peak by mass
        self.sample=sample#must be sample object

    
    def __getattr__(self, attrs):
        if attrs=='sample':
            raise AttributeError("")
        if hasattr(self.sample, attrs):
            return getattr(self.sample, attrs)#could possibly raise an AttributeError
        raise AttributeError("MSSample has no %s"%attrs)
        
    def __add__(self, pkl):
        return MSPeakList(list(self)+pkl, sample=self.sample)        
        
    
    def __eq__(self, peaklist):
        """
        TODO:rewrite with set stuff
        do not care about position
        can not check the initial length for determining if the two are equals
        
        """
#        if set(peaklist).issuperset(set(self)):
#            return True
#        return False
        s=sorted([peaklist, self], key=lambda x:len(x))
        ref, tested = s[0], s[1]
        for peak in ref.ipeaks():
            if peak not in tested:
                return False
        return True
    
    
    def __neq__(self, peaklist):
        return not self == peaklist
    
    
    def rmDuplicates(self):
        return MSPeakList(list(set(self)), sample=self.sample)
    
    
    def diff(self, other):
        """
        longest against the shortest one, used in the rtClustering
        may use set objects !, use INTERSECTION FUNCTION instead
        
        """
        if not isinstance(other, MSPeakList):
             return TypeError("error Intersect function, MSPeakList expected, got%s:"%(type(other)))
        return MSPeakList(list(set(self)-set(other)))
    
    
    def intersect(self, other):
        """
        proceed to the intersection of 2 peaklist
        
        """
        if not isinstance(other, MSPeakList):
            return TypeError("error Intersect function, MSPeakList expected, got%s:"%(type(other)))
        return MSPeakList(list(set(self).intersection(set(other))))

    
    def ipeaks(self):
        """
        return a iterator(generator) of peaks
        
        """
        for peak in self:
            yield peak
        
    
    #@check(MSChromatographicPeak) raise an error MSChromatographicPeak is not yet defined
    def addPeak(self, p):
        """just test if p is a chromatoPeak object then append"""
        if not isinstance(p, MSChromatographicPeak):
            raise TypeError("Expected MSChromatographicPeaks object got:%s"%type(p))
        self.append(p)
    
    
    def masses(self, asarray=False):
        """
        return masses as list or as array        
                
        """
        return [p.mass() for p in self.ipeaks()] if not asarray else \
        np.array([p.mass() for p in self.ipeaks()])
    
    
    def rts(self, asarray=False):
        """
        return masses as list or as array        

        """
        return [p.rt for p in self.ipeaks()] if not asarray else \
        np.array([p.rt for p in self.ipeaks()])
    
    def withSample(self, s_, fullNameEntry=False):
        """
        return the first peak in the peaklist with the specified sample
        
        """
        pkl = MSPeakList()
        sample = None
        if isinstance(s_, str):            
            for p in self.ipeaks():
                if p.sample.shortName() == s_:
                    sample = p.sample                    
                    pkl.append(p)
                    
        elif isinstance(s_, MSSample):
            for p in self.ipeaks():
                if p.sample == s_:
                    sample = p.sample
                    pkl.append(p)
        pkl.sample = sample
        return pkl
    
    
    def peaksInRTRange(self, rt, r, rinf=None, rsup=None):
        """
        support for asymmetrical slicing ?
        numpy code 3x slower than normal python code
        using wrong functions?
                
        """
#        r_inf=rt-r if rinf is None else rt-rinf
#        r_sup =rt+r if rsup is None else rt+rsup
#        
#        s=MSPeakList(sorted(self, key=lambda x:x.rt))
#        if len(s) == 1:
#            return MSPeakList([s[0]] if s[0].rt > r_inf and s[0].rt < r_sup else [], 
#                              sample=self.sample)
#        indexes = bisection(s.rts(asarray=True), rt, r_inf, r_sup)
#        if not indexes:
#            return MSPeakList(sample=self.sample)
#        return MSPeakList([s[i] for i in set(indexes)], sample=self.sample)
        r_inf = -1. if rinf is None else rinf
        r_sup = -1. if rsup is None else rsup        
        #s=MSPeakList(sorted(self, key=lambda x: x.rt))        
        idx = _peaksInRtRange(self.rts(asarray=True), rt, r, r_inf, r_sup)
        return MSPeakList([self[i] for i in xrange(idx[0], idx[-1]+1)], sample=self.sample)
    
    def peaksInMZRange(self, m, deltam=None, inf=None, sup=None):
        """
        return a list of peak between a mass + -  deltam
        not need to sort the array cause already sorted        
        
        """  
        if deltam is None and self.sample is None:
            raise ValueError("missing one information")
        deltam= deltam if deltam is not None else self.sample.ppm * m / 1e6
        m_inf=m-deltam if inf is None else m-inf
        m_sup =m+deltam if sup is None else m+sup
        res = bisect(self.masses(asarray=True), m, m_inf, m_sup)
        return MSPeakList([self[i] for i in res], sample=self.sample)
    
    
    def ipeaksInMZRange(self, mass, deltam=None):
        """
        return a generator of peak between a mass + -  deltam
        
        """
        return (x for x in self.peaksInMZRange(mass, deltam))
    
    
    def peaksInMZRTRange(self, m, rt, deltart, deltam=None):
        """
        combination of two selection first on
        mass then on rt dimension
        
        """
        p=self.peaksInMZRange(m, deltam)
        if not p:
            return MSPeakList(sample=self.sample)
        return p.peaksInRTRange(rt, deltart)
    

    def peakAt(self, mass, rt):
        """
        TODO: check if it works
        return a specified peak with mass and rt in rawdata
        add an argument which specify the kind of peak list
        to search in
        does not work if we test floats instead of strings
        must the way of python manage floating ???
        
        """
        pkl=self.peaksInMZRTRange(mass, rt, deltart=MEAN_RTSHIFT/2., deltam=self.sample.ppm)
        if not pkl:
            print "peak at %f, %f does not seem to exist"%(mass, rt)
        return sorted(pkl, key=lambda x: abs(mass-x.mass()))[0]
        return None
    

class MSClusterList(MSPeakList):
    """
    handling fragment, and isotopic_cluster
    
    """
    @slots
    def __init__(self, peaklist=[], parent=None):
        MSPeakList.__init__(self, peaklist)
        self.interR ="NA"
        self.intraR ="NA"
        self.parent=parent#reference to the peak whiwh own this cluster
    
    def calcIntraR(self):
        pass   
    

class MSAbstractTypes(object):
    """
    Abstract class for handling Spectrum, Chromatogram class
    
    """
    @slots
    def __init__(self, rtinfo=(0., 0., 0.), x_data=None, y_data=None, **k):
        """
        Constructor parameters:list x, list y
        
        """    
        #if x_data is not None and y_data is not None:
        #    if len(x_data) != len(y_data):
        #       raise IndexError, "x_data and y_data must the same size"
        
        self.x_data = x_data#np.array(x_data) #must be a numpy array
        self.y_data = y_data#np.array(y_data)

        self.rtmin = rtinfo[1] 
        self.rtmax = rtinfo[2]
        self.rt = rtinfo[0]
        self.sample = k.get('sample')#none by default
        
    
    def __getitem__(self, i):
        """
        return a tuple chrom[i] is a tuple
        
        """
        return self.x_data[i], self.y_data[i]
    
    
    def __delitem__(self, i):
        """
        del the i-th item of both
        x_data and y_data
        
        """
        del self.x_data[i]
        del self.y_data[i]
    
    
    def setitem(self, i, val, axis=0):
        """
        set the i-th item to val
        axis design x axis if 0 else the y axis
        
        """
        if axis == 0:
            self.x_data[i]=val
        else:
            self.y_data[i]=val
               
    
    def points(self):
        """
        return all data points in form
        of list of tuples
        
        """
        return zip(self.x_data, self.y_data)
    
    
    def ipoints(self):
        """
        return a generator of the list
        
        """
        return (x for x in self.points())
    
    
    def sliceValues(self, x, x_, axis=0):
        """
        Emulation of the special method __getslice__ which 
        need integers got float instead, must be redefined 
        in spectra, cause here supposed this is not sorted        
        
        """
        if x > x_:
            print ("Warning in sliceValues function !")
            x, x_ = x_, x
        data = self.x_data if axis==0 else self.y_data
        idx = bisect(data, np.array([x, x_].mean(), x, x_))
        return self.x_data[idx], self.y_data[idx]
        
            
    
    def isliceValues(self, x, x_, axis=0):
       """
       same as before but return a generator instead
       
       """
       return ((x,y) for x, y in self.sliceValues(x, x_, axis))
    
#===============================================================================
#Plotting functions
    def plot(self, embbedInGui=True):
        """
        this method is optionnal
        may disappear soon, use for scripting
        capabilities
        
        """
        if embbedInGui:
            instanceRunning=False            
            try:
                from PyQt4.QtGui import QApplication
                
                instance = QApplication.instance()
                if instance is not None:
                    instanceRunning = True 
            except ImportError:
                print ("can not plot with the embbedInGui set to True")
            finally:
                if instanceRunning:
                    self.showCanvas(instance)
        else:
            try:
                import pylab
                pylab.plot(self.x_data, self.y_data)
                pylab.show()
            except ImportError:
                print "can not plot"
    
    def showCanvas(self, instance):
        """
        to be overloaded in subclasses
        called in plot        
        """
        pass

#-------------------------------------------------------------------------------
    def applyLog(self):
        """
        apply a log to the y_data
        
        """
        return np.log(self.y_data)
    
    
    def cutOff(self, value):
        """
        remove all datapoints < to value
        never used after i think...
        
        """    
        value = float(value)
        m = self.y_data.max()
        if m < value:
            raise ValueError("cut off value must be < to the max of the data")
        return np.clip(self.y_data, value, m)
        
    @staticmethod
    def computeBaseLine(y_data, quantile=40, smooth=True, sigma=1, order=0):
        """
        computing baseline
        put one value max
        sigma can be assimilated to an fwhm of common peak
        
        """
        cut=np.sort(y_data)[int((quantile*y_data.shape[0])/100.)]
        print "Max value of baseline: %f"%cut
        l=np.clip(y_data, 0, cut) 
        return gaussSmoothing(l, sigma, order=order) if smooth else l
    
    @staticmethod    
    def averageSmoothing(x, window_len=30, window='flat'):
        """     
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.
        
        """
        if x.ndim != 1:
            raise ValueError, "smooth only accepts 1 dimension arrays."
        if x.size < window_len:
            raise ValueError, "Input vector needs to be bigger than window size."
        if window_len<3:
            return x
        if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
            raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"
        s= np.r_[2*x[0]-x[window_len-1::-1],x,2*x[-1]-x[-1:-window_len:-1]]
        if window == 'flat': #moving average
            w=np.ones(window_len,'d')
        else:
            w=eval(window+'(window_len)')
        y= np.convolve(w/w.sum(), s, mode='same')
        return y[window_len:-window_len+1]
            
    
    @staticmethod
    def SGSmoothing(y, window_size=17, order=4, deriv=0):
        """
        y : array_like, shape (N,), the values of the time history of the signal.
        window_size : int, the length of the window. Must be an odd integer number.
        order : int, the order of the polynomial used in the filtering.
            Must be less then `window_size` - 1.
        deriv: int, the order of the derivative to compute (default = 0 means only smoothing)
       
        """
        try:
            window_size = np.abs(np.int(window_size))
            order = np.abs(int(order))
        except ValueError:
            raise ValueError("window_size and order have to be of type int")
        if window_size % 2 != 1 or window_size < 1:
            raise TypeError("window_size size must be a positive odd number")
        if window_size < order + 2:
            raise TypeError("window_size is too small for the polynomials order")
        order_range = range(order+1)
        half_window = (window_size -1) // 2
        # precompute coefficients
        b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
        m = np.linalg.pinv(b).A[deriv]
        # pad the signal at the extremes with
        # values taken from the signal itself
        firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
        lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
        y = np.concatenate((firstvals, y, lastvals))
        return np.convolve( m, y, mode='valid')    
    
    
    @staticmethod
    def makeGaussianPeak(mz, ai, base=0., fwhm=0.1, points=500):
        """
        Make Gaussian peak.
            mz: (float) peak m/z value
            ai: (float) peak ai value
            base: (float) peak baseline value
            fwhm: (float) peak fwhm value
            points: (int) number of points
        
        """
        x_data, y_data =[], []     
        minX = mz - (5*fwhm)
        maxX = mz + (5*fwhm)
        step = (maxX - minX) / points
        width = fwhm/1.66
        x = minX
        intensity = ai - base
        for i in xrange(points):
            y = intensity*exp(-1*(pow(x-mz,2))/pow(width,2)) + base
            y_data.append(y)            
            x_data.append(x)
            x += step
        return np.array(x_data), np.array(y_data)
    
    
    def globalIntensity(self):
        """
        for calculating TIC MRM
        
        """
        return self.rtmin, self.y_data.sum()
        
    
    def merge(self, others):
        """
        binning the x_data
        
        """
        #if not others:
        #    return
        #if not all([isinstance(o, MSAbstractTypes) for o in others]):
        #    raise TypeError
        others = list(set(others + [self]))
        minRt=np.array([o.x_data.min() for o in others]).min()
        maxRt = np.array([o.x_data.max() for o in others]).max()
        maxlen=np.array([o.x_data.shape[0] for o in others]).min()
        
        xbinning= np.array([minRt + i*((maxRt-minRt)/maxlen) for i in xrange(maxlen)])
        intensity=np.zeros(maxlen)
        
        for e in others:

            _bin=((np.array(e.x_data)-minRt ) / (maxRt-minRt) * maxlen).astype(int)
            _bin = _bin.clip(0, min(maxlen-1, e.y_data.shape[0]-1))
            intensity[_bin] += e.y_data[_bin]
        
        return xbinning, intensity/len(others), minRt, maxRt
        


class MSChromatogram(MSAbstractTypes):
    """
    Chromatogram object 
    
    """
    @slots
    def __init__(self,  rtinfo=(0.,0.,0.), x_data=None, y_data=None, **kw): 
        """
        Constructor 
        @rtinfo
        @x_data
        @y_data
        
        """
        MSAbstractTypes.__init__(self, rtinfo, x_data, y_data, **kw)
        
        massrange = kw.get('massrange', (0.,0.,0.))
        self.mz= massrange[0]
        self.mzmin = massrange[1]
        self.mzmax = massrange[2]
            
        self.baseline = None 
        self.peaks = MSPeakList(sample=self.sample)#will contain index of each detected peak#non xcms peak
        
        
    def __str__(self):
        pass
    
    
    def mass(self, mode=''):
        """
        special keyword:mode
        return transition if mode==Transition object else
        return the precursor value
        
        """
        if hasattr(self, 'transition'):
            #if mode == 'transition':
            #    return self.transition
            return self.transition.precursor
        return self.mz
    
    def showCanvas(self, instance):
        instance.view.addMdiSubWindow(MSQtCanvas([self], 
                                                  title=str(self.mass()))) 
    
    def merge(self, others):
        x, y, minRt, maxRt = MSAbstractTypes.merge(others)
        return MSChromatogram((0., minRt, maxRt),
                              x_data=x,
                              y_data=y,  
                              sample=self.sample)
    
    def _gaussFit(self, x, x_,  order=0):
        """        
        apply a gaussian filter
        then use the leastsquare optimization
        used in integrationBtw
        
        """        
        if x > x_:
            print ("Warning: swaping the 2 values")
            x, x_ = x_, x
            
        fitgauss=lambda p, x :p[0] * np.exp( - ((x-p[1]) ** 2) / (p[2] ** 2)) + p[3]
        rt, intensity=self.sliceValues(x, x_)
        gaussintens=gaussSmoothing(intensity, 1., order=order)
        p0=[intensity.max(), self.mz, abs(x_-x)/1.66, 0.]
        p1, success = leastsq(fitgauss, p0, gaussintens)
        return p1, success
    
    def integrationBtw(self, inf, sup): 
        """
        solution:
            fit the curve with a gaussian
            then integrate the approximative function between to x-values
        @inf specify an inferior xvalue
        @sup specify the superior xvalue
        
        """
        p1, success = self._gaussFit(inf, sup)
        if len(p1)==0:
            raise ValueError, "Enable to calculate integrale"
        #print "parameters, success", p1, success
        fitgauss=lambda x:p1[0] *np.exp(-((x-p1[1])**2)/(p1[2]**2))+p1[3]      
        area, error = quad(fitgauss, inf, sup)
        return p1, success, area, error
                
    
    def _computePeaksPos(self, computeBaseline=False):
        """
        will computute the peak positions, this function is useful for
        finding textlabel items positions; see mplWidget(graphics package)
        is useful when using the find peak boundaries method too
        
        """
        #self.baseline=self.computeBaseLine(self.y_data, quantile=65., smooth=False)
        #cutValue=sorted(self.y_data)[int((92. * len(self.y_data))/100)]
        z=gaussSmoothing(self.y_data, 1, order=0)
        if computeBaseline:
            z = self.computeBaseLine(z, 92.)
        #z=self.averageSmoothing(self.y_data, 30)
        values, indexes=[], []
        i=0
        while i < z.shape[0]-1:
            while z[i+1] >= z[i] and i < z.shape[0]-2:
                i+=1
            values.append(self[i])            
            indexes.append(i) 
            while z[i+1] <= z[i] and i < z.shape[0]-2:
                i+=1
            i+=1
        for i, v in enumerate(sorted(values, key = lambda x: x[1])[-10:]):
            p=MSChromatographicPeak()
            p.isXCMSPeak=False
            p.mz=self.mass()
            p.pos=indexes[i]
            p.rt=v[0]
            p.height=v[1]
            p.sample=self.sample
            self.peaks.append(p)
    
    
    
    def _computePeaksBounds(self):
        """
        compute the boundaries with the help of the baseline calculation
        actually an very ugly function 
        TODO: think about baseline
        """
        #if not len(self.y_data):
        #    print "Error y_data is empty"
        #    return
        cutValue=sorted(self.y_data)[int((92. * self.y_data.shape[0]) / 100)]
        #print "cutValue", cutValue
        for i in xrange(len(self.peaks)):
            apex = self.peaks[i].pos
            ii, jj = apex-1, apex+1
 
            while self.y_data[ii] >= cutValue and ii > 0:
                ii-=1                
            #walk to the right           
            while self.y_data[jj] >= cutValue and jj < len(self.y_data) - 1:                
                jj+=1
            #if ii < 0 or jj > len(self.y_data):
            #    print "error at the beginning of finding peaks bounds"
            self.peaks[i].minpos==ii
            self.peaks[i].rtmin=self.x_data[ii]
            
            self.peaks[i].maxpos==jj
            self.peaks[i].rtmax=self.x_data[jj]
    
    def _computePeaksInfo(self):
        """
        calculate for each peak, the peakAreaTop, peakArea, baselineRatio...
        we can use the integration algorithm i wrote to see if means something 
        or not
        
        """
        for p in self.peaks.ipeaks():
            p.areaTop = p.height + self.y_data[p.pos-1] + self.y_data[p.pos+1]
            x, y= self.sliceValues(p.rtmin, p.rtmax, axis=1)
            p.summedArea = int(y.sum())
    
    
    def findNonXCMSPeaks(self, computeInfos=False):
        """
        This a convenience function, find all peak in a chromatogram...
        
        """
        self._computePeaksPos()
        self._computePeaksBounds()
        if computeInfos:
            self._computePeaksInfo()
    
    
    
class MSChromatographicPeak(MSChromatogram):
    """ 
    chromatographic peak Object, may not be inherited by
    a chromatogram in the future ?
    
    """    
    @slots
    def __init__ (self, rtinfo=(0.,0.,0.), intinfo=(0.,0.,0.,0.), x_data=None, y_data=None, **kw):
        """
        constructor handles variables args
        
        """
        MSChromatogram.__init__(self, rtinfo, x_data, y_data,**kw)
        self.area=intinfo[0]# area under the peak shape            
        self.corrarea=intinfo[1]
        self.sn=intinfo[2]
        self.height=intinfo[3]         
        
        self.isoCluster=kw.get('isoCluster', MSClusterList())
        self.fragCluster=kw.get('fragCluster', MSClusterList())#may be a list will contains several peakList of different fragments
        self.spectra=kw.get('spectra', [])
        self.isoSpectra=[]#None#mass, prob tuple 
        
        self.r_coef =0.            
        self.idms = None
        self.parentPeak=[]
        
        self.annotation = {}#dictionnary containing the relationship between one peak and his mass difference
        self.formulas = OrderedDict() #dictionnary key formula generated for this mass and infmation about this formulas
        self.isFoundInDatabase = False
        
        self.isGood=True#identified as a goodPeak
        
        self.pos=0
        self.minpos=0
        self.maxpos=0
        
        self.isXCMSPeak = True

    
    def __hash__(self):
        """
        to allow chromatoPeak object to be a key in dict
        
        """
        return id(self)
    
    def __str__(self):
        """
        redefine str for chromatoPeak object
        
        """
        return '/'.join([str(self.mass()), str(self.rt)])    
    
    def ispectra(self):
        """
        return a generator on peak's spectra
        
        """
        for s in self.spectra:
            yield s
           
#    def __getattr__(self, attr):
#        """
#        wrapping of the methods of MSClusterList
#        """
#        m=None
#        if hasattr(self.isoCluster, attr):
#            m=getattr(self.isoCluster, attr)
#        elif hasattr(self.fragCluster, attr):
#            m=getattr(self.fragCluster, attr)
#        elif hasattr(self, 'transition') and hasattr(self.transition, attr):
#            m=getattr(self.transition, attr)
#        if m:
#            return m
#        raise NameError(attr)
    
    
    def belongToCluster(self, attribute_name):
        if self.parentPeak:
            if hasattr(self.parentPeak, attribute_name):
                return self in getattr(self.parentPeak, attribute_name), self.parentPeak 
        return False
    
    #def plot(self):   
    #    return MSMplCanvas([self], flags='peak')#, self.x_data, self.y_data)
    
    def getSons(self, include_M0=False):
        if not include_M0:
            return self.isoCluster.hstack(self.fragCluster)
        else:
            l =self.isoCluster.hstack(self.fragCluster)
            l.append(self)
            return l
    
    def isoAreas(self, includeM0=True):
        if includeM0:
            return np.array([p.area for p in self.isoCluster].insert(0, self.area))      
        return np.array([p.area for p in self.isoCluster])
            
    def fragAreas(self, includeM0=True):
        if includeM0:
            return [p.area for p in self.fragCluster].insert(0, self.area)
        return [p.area for p in self.fragCluster]
    
    def pCalcBasedOnPeakShape(self):
        from core.MetClustering import calcIntraR
        calcIntraR(self)
    
    
            

class Scan(dict):
    """
    Only a temporary object
    May disappear soon
    Scan object directly based on mzXML file a dict may be too heavy
    
    """
    @slots
    def __init__(self, fields={}):
        dict.__init__(self, fields)
    
    def rt(self):
        return self['retentionTime']
    
    def fragment(self):
        return self['basePeakMz']
    
    def intensity(self):
        return self['basePeakIntensity']
    
    def precursor(self):
        return self['precursorMz']
    
    def scantype(self):
        return self['scanType']
    
    def byteOrder(self):
        return self['byteOrder']
    
    def compression(self):
        return self['compression']
    
    def precision(self):
        return self['precision']
    
    def polarity(self):
        return self['polarity']



class MSSpectrum(MSAbstractTypes):
    """
    Pseudo-Spectrum in MRM, one scan in high res profile
    
    """
    @slots    
    def __init__(self, rtinfo=(0.,0.,0.), x_data=None, y_data=None, **kw):
        MSAbstractTypes.__init__(self, rtinfo, x_data, y_data, **kw) 
        
    def __str__(self):
        return str(self.rt)
    
    def encode64(self):
        """
        peaks encoded under base64
        
        """
        scanbyte=""
        for tupl in self.points():
            scanbyte+=struct.pack("!ff", *tupl)
        return base64.b64encode(scanbyte)
     
    def decode64 (self, code):
        """
        decode peaks from 64 base
        
        """
        list_tuple = base64.b64decode(code)
        for tuple_ in list_tuple:
            self.x_data.append(tuple_[0])
            self.y_data.append(tuple_[1])
            
    def showCanvas(self, instance):
        instance.addMdiSubWindow(MSQtCanvas([self], title="spectrum"))
    
    def imassPeakInRange(self, m, deltam):
        '''
        use dichotomic research,return a generator list of tuple, each tuple
        contains x_data, y_data, same as 'massPeakInRange' but returns a
        generator instead of a list
        
        '''
        idx = bisect(self.x_data, m, m-deltam, m+deltam)
        return (self[i] for i in idx)
           
    
    def massPeakInRange(self, m, deltam=None):
        '''
        use dichotomic research return a list of tuple, each tuple
        contains x_data, y_data
        
        '''
        deltam=np.float((self.sample.ppm*m)/1e6) if deltam is None else deltam
        if self.sample.kind == 'MRM':
            deltam = 1.
        idx = bisect(self.x_data, m, m-deltam, m+deltam)
        return [(self.x_data[i], self.y_data[i]) for i in idx]
    
    def merge(self, others):
        x, y, minmz, maxmz = MSAbstractTypes.merge(self, others)
        return MSSpectrum((minmz, maxmz, 0.),
                              x_data=x,
                              y_data=y, 
                              sample=self.sample)


class MSSample(object):
    """
    Represents all information found in a xml file each attribute is private    
    
    """    
    kindPossibility={'HighRes':"netcdf", 'MRM':'mzXML'}
    peakModelLabel = ["mass", "rt", "intensity", "sn", "r_coef"]
    clusterModelLabel = ["mass", "rt", "intensity", "isotopic_cluster", "fragments/adducts cluster"]
    idModelLabel = ["mass", "rt", "mmu", "formulas", "score", "name"]
    
    @slots
    def __init__(self, xmlfile, **k):
        if not isinstance(xmlfile, str):
            raise TypeError('Sample xmlfile must be a non empty string')
       
        self.xmlfile = xmlfile#full fullname, xmlfile old name to say file
        self.kind = k.get('kind', 'HighRes')
        self.msLevel = None
        self.peaksOnly = k.get('peaksOnly', False)#when a sample come from a peaklist so
        #does not have any data points
        self.ppm = k.get('ppm')
        if self.ppm is None:
            self.ppm = 1. if self.kind !='HighRes' else 10.#/1e6
        self.checked = True#for plotting
        self.color = None#3tuple
        
        self.isC13Labeled=False
        self.isN15Labeled=False
        
        self.classes = k.get('classes', 'A')
        self.metaData=None #get the metadata from the cdf file
        
        self.header = ''
        self.spectra = []
        self.chroma = [] # TIC in fact, for MRM style
        
        #series of peaklist
        self.rawPeaks = MSPeakList(sample=self)#k.get('peaks')#first raw peaks just after the xcmsSet function
        self.corrPeaks=MSPeakList(sample=self)#peaks after grouping and retention time correction
        self.mappedPeaks=MSPeakList(sample=self)#interesting peaks
        self.isotopicPeaks=MSPeakList(sample=self)
        self.adductPeaks=MSPeakList(sample=self)
        
        self.isRef = False #alignment
        self.restriction = None

#------------------------------------------------------------------------------ 
    def shortName(self):
        return self.xmlfile.split('/')[-1]

#------------------------------------------------------------------------------ 
    def getInfos(self):
        """
        return a string which contains most of informations
        about one sample
        
        """
        s=""
        s+="<b>FullName</b>: %s<br/>"%self.xmlfile
        s+="<b>Kind</b>: %s<br/>"%self.kind
        s+="<b>Ppm</b>: %s<br/>"%str(self.ppm)
        s+="<b>Class</b>: %s<br/>"%self.classes
        s+="<b>isC13Labeled</b>: %s<br/>"%str(self.isC13Labeled)
        s+="<b>nb Spectra</b>: %s, mintime: %s, maxtime: %s"%(str(len(self.spectra)), 
                                                      str(self.spectra[0].rtmin) if self.spectra else "NaN", 
                                                      str(self.spectra[-1].rtmin)if self.spectra else "NaN")
#        s+="minmz: %s, maxmz: %s\n"%(str(min(map(min, [s.x_data for s in self.spectra]))), 
#                                   str(max(map(max, [s.x_data for s in self.ispectra()]))))
        return s
    
#------------------------------------------------------------------------------ 
    def loadData(self, xmlfile=None, rounding=(4, 4), time_conv=False):
        """will load the data stored in a netcdf file
        @rounding;tuple number of digits data will be rounded to for masses
        and for time
        
        """
        if xmlfile is None and self.xmlfile is None:
            raise ValueError("please give a namefile !")
        if xmlfile is None:
            xmlfile=self.xmlfile
        t=clock()
        try:
            root = netcdf.netcdf_file(self.xmlfile)
            var = root.variables
        except Exception: 
            print (','.join(['the file', self.xmlfile, 'does not seem to be a good cdf!']))
            return
        
        mass_data = np.round(var['mass_values'][:], rounding[0]).astype(np.float)
        #print 'type intensity', type(var['intensity_values'][:].view(dtype=var['intensity_values'][:].dtype))
        intensity_data = var['intensity_values'][:].astype(np.int)#.view(dtype=np.int8, type=np.ndarray)
        scan_index = var['scan_index'][:]#.view(dtype=np.int8, type=np.ndarray)
        tot_intensity = var['total_intensity'][:].astype(np.int)#.view(dtype='i4', type=np.ndarray)
        scan_acquisition_time = var['scan_acquisition_time'][:].astype(np.float)
        
        self.ionization=str(root.__dict__['test_ionization_polarity']).split(' ')[0].lower()
        self.detector=root.__dict__['test_detector_type']
        self.experiment=str(root.__dict__['experiment_type']).split(' ')[0].lower()
        self.netcdf=root.__dict__['netcdf_revision']
  
        self.spectra = self._highResSpectraCreation(mass_data, 
                                                    intensity_data,
                                                    scan_index,
                                                    scan_acquisition_time)
        self.chroma.append(MSChromatogram((0.,
                                           scan_acquisition_time[0],
                                           scan_acquisition_time[-1]),
                                           scan_acquisition_time,
                                           tot_intensity, sample=self))
        print clock()-t
    
#------------------------------------------------------------------------------ 
    def _highResSpectraCreation(self, masses, intensities, indexes, 
                                scan_acquisition_time):
        """
        simply create scans object from extracted data from a netcdf files
        
        """
        spectra = []

        for i in xrange(len(indexes)-1):
            spectrum = MSSpectrum((scan_acquisition_time[i],
                                   scan_acquisition_time[i+1],
                                   0.),
                                   masses[indexes[i]:indexes[i+1]],#None if QApplication.instance().lowMemory else ], 
                                   intensities[indexes[i]:indexes[i+1]],#None if QApplication.instance().lowMemory else ,
                                   sample=self)
            spectra.append(spectrum)
        return spectra    
 
#------------------------------------------------------------------------------ 
    def loadMZXMLData (self, timeOpts='s'):
        #first check if file is empty
        #TODO: not useful in fact remove that 2 lines ?
        if stat(self.xmlfile)[6] == 0:
            print "The file seems to be empty..."
            return
        
        max_time, min_time, scan_count, prefix = self._getInfos()
        self.header = self._getHeader()
        t = clock()
        scans = []
        #load the validator ?;import cStringIO
        #f = cStringIO.StringIO(open(path.normcase('utils/mzXML_3_1.xsd')).read())
        #xmlschema = XMLSchema(file=path.normcase("utils/mzXML_3_1.xsd")) does not work actually
        try:
            context = iterparse(self.xmlfile, events=('end',))
        except Exception:
            print "could not parse %s"%self.xmlfile
            return
        for action, elem in context:
            if elem.tag == "".join([prefix, "scan"]) and action == 'end':
                scan = Scan({'scanNumber':int (elem.attrib.get('num', 0)),
                            'msLevel': int (elem.attrib.get('msLevel', 1)),
                            'scanType':elem.attrib.get('scanType', ""),
                            'retentionTime':timeFormat(elem.attrib['retentionTime']),
                            'basePeakMz':float(elem.attrib.get('basePeakMz', 0)),
                            'basePeakIntensity': float(elem.attrib.get('basePeakIntensity', 0)),
                            'polarity':elem.attrib.get('polarity', "")})
                if scan['msLevel'] == 1:
                    #get data points
                    for e in elem.getchildren():
                        if e.tag == "".join([prefix, "peaks"]) and action == 'end':
                            scan['points'] = e.text
                            break
                elif scan['msLevel'] == 2:
                    #dont need to get datapoint
                    #we reconstrcut MS1 spectra in fact
                    for e in elem.getchildren():
                        if e.tag == "".join([prefix, "precursorMz"]) and action=='end':
                            try:
                                scan['precursorMz'] = float(e.text)
                            except ValueError, TypeError:
                                pass
                            finally:
                                break
                scans.append(scan)
            #warning the next line cause everything to be None
            #after !
            #elem.clear()
        del context
        #parsing ended 
        #Sample construction
        self.msLevel = scans[0]['msLevel']#assume that all scans have the same msLevel
        if self.msLevel == 2:
            time_window = self._estimateRuntime(scans, parameters=(max_time, min_time, scan_count))
            self.spectra = self._spectraCreation(scans, min_time, max_time, time_window)
        elif self.msLevel == 1:
            self.spectra = self._spectraCreationByScans(scans)
        self.chroma.append(self._ticCreation(self.spectra))
        #settings basic stuff
        self.polarity='negative' if scans[0].polarity()=='-' else 'positive'
        del scans
        print clock()-t
 
 
#------------------------------------------------------------------------------ 
    def _spectraCreationByScans(self, scans):
        
        def decode_spectrum(line):
             decoded = base64.decodestring(line)
             tmp_size = len(decoded)/4
             unpack_format1 = ">%dL" % tmp_size
    
             idx = 0
             mz = []
             intensity= []
    
             for tmp in struct.unpack(unpack_format1, decoded):
                 tmp_i = struct.pack("I", tmp)
                 tmp_f = struct.unpack("f", tmp_i)[0]
                 if(idx % 2 == 0):
                     mz.append( float(tmp_f) )
                 else:
                     intensity.append( float(tmp_f) )
                 idx += 1
             return mz, intensity
        
        spectrumList = []
        for i in xrange (len(scans)-1):
            #print "code:%s len:%d"%(scans[i]['points'], len(scans[i]['points']))
            x_data, y_data = decode_spectrum(scans[i]['points'])
            #print x_data, y_data
            spectrumList.append(MSSpectrum((scans[i].rt(),
                                           scans[i+1].rt(),
                                           0),
                                           x_data=x_data, 
                                           y_data=y_data,
                                           sample=self))
        return spectrumList
    
#------------------------------------------------------------------------------        
    def _spectraCreation(self, scans, min_time, max_time, time_window):
        """    
        create all spectra
        
        """
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
            spectr= MSSpectrum((key[0], key[1], 0.), np.array(groupedScan[key][0]), np.array(groupedScan[key][1]), sample=self)
            spectrumList.append(spectr)
        del groupedScan
        return spectrumList
        
#------------------------------------------------------------------------------    
    def _ticCreation(self, spectra):
        x=np.zeros(len(spectra))
        y=np.zeros(len(spectra))
        for i, s in enumerate(spectra):
            x[i], y[i]=s.globalIntensity()
        return MSChromatogram((0., x.min(), x.max()), x, y, sample=self)
    
#------------------------------------------------------------------------------ 
    def _chromatoCreation(self, scans):
        """
        create all chromatograms, little bit slow
        
        """
        chromatoList = []
        clusters = {}
        for scan in scans:
            if not (scan.precursor(), scan.fragment()) in clusters.keys():
                clusters[(scan.precursor(), scan.fragment())] = [], []
            clusters[(scan.precursor(), scan.fragment())][0].append(scan.rt())
            clusters[(scan.precursor(), scan.fragment())][1].append(scan.intensity())
        for keys in sorted(clusters.iterkeys()):
                chromatogram= MSChromatogram(x_data=np.array(clusters[keys][0]), 
                                             y_data=np.array(clusters[keys][1]),
                                             massrange=[keys[0], keys[1]],
                                             sample=self)
                chromatoList.append(chromatogram)
        del clusters
        return chromatoList
    
#------------------------------------------------------------------------------ 
    def _getInfos (self):
        """
        case we have a mzxml file, get run length and number of scans
        sentinel MAX
        """
        p = compile('\s+<msRun\sscanCount="(\d+)"\sstartTime=\"PT(\d+\.\d+|\d+)S"\sendTime=\"PT(\d+\.\d+)S"\s>')
        q = compile('<mzXML\sxmlns="(.+)"') #to get the namespace
        MAX=10 #ten lines max the skip
        with open(self.xmlfile) as fd:
            line = fd.readline()
            i=0
            while q.match(line) is None and i<MAX:
                line = fd.readline()
                i+=1
            prefix = "{"+ q.match(line).group(1)+"}"
            line = fd.readline()
            i=0
            while p.match(line) is None and i<MAX:
                line = fd.readline()
                i+=1
            scan_count = int(p.match(line).group(1))
            max_time = float(p.match(line).group(3))
            min_time = float(p.match(line).group(2))
                
        return  max_time, min_time, scan_count, prefix
        
        
    def _getHeader(self):
        """
        get the header of file until "scan" balise starts 
        useful for creating new xml files
        
        """
        MAX=10
        p = compile ('\s+<scan\snum="1"\n')
        header=""
        with open(self.xmlfile) as fd:
            line = fd.readline() 
            i=0
            while p.match(line) is None and i<MAX:
                header += line
                line = fd.readline()
                i+=1
            if i==9:
                print header
                header=""
        return header

    
    @staticmethod
    def _estimateRuntime(scans, **kw):
        """
        estimate the time of one scan if user does not get it
        
        """
        #find first good reference
        i,c=0,0
        while c <=2 and i <len(scans):
            c+=1;i+=1
        if i < len(scans)-1:
            ref =(scans[i].precursor(), scans[i].rt())
            i+=1        
            while i < len(scans):
                if scans[i].precursor() == ref[0]:
                    return (scans[i].rt()-ref[1])
                i+=1
        p = kw.get('parameters') if kw.get('parameters') else False
        if p:
            return p[1]-p[0]/float(p[2])
        return p
    
    
    def peakAt(self, m, rt=None):
        '''return a specified peak with mass and rt in rawdata'''
        '''add an argument which specify the kind of peak list
        to search in'''
        '''does not work if we test floats instead of strings
        must the way of python manage floating ???
        
        '''        
        try:
            if isinstance(m, str):
                return [p for p in self.rawPeaks.ipeaks() if m==str(p)][0]
            if isinstance(m, MSChromatographicPeak):
                    return [p for p in self.rawPeaks.ipeaks() if m==p][0]
            return [p for p in self.rawPeaks.ipeaks() if "/".join([str(m), str(rt)])==str(p)][0]
        except IndexError:
            return None
    
    
    def getCluster(self, m, rt=None):
        try:
            if isinstance(m, str):
                return [p for p in self.mappedPeaks.ipeaks() if m==str(p)][0]
            if isinstance(m, MSChromatographicPeak):
                    return [p for p in self.mappedPeaks.ipeaks() if m==p][0]
            return [p for p in self.mappedPeaks.ipeaks() if "/".join([str(m), str(rt)])==str(p)][0]
        except IndexError:
            return None
    
    
    def ispectra(self):
        """return a spectra generator"""
        for spectrum in self.spectra:
            yield spectrum
            
    def ichromas(self):
        """return a chromas generator"""
        for chromatogram in self.chroma:
            yield chromatogram
        
    
    def irawPeaks(self):
        """return a peak generator, wraps peaks method"""
        return self.rawPeaks.ipeaks()
    
    def imappedPeaks(self):
        return self.mappedPeaks.ipeaks()
    
    @check(MSChromatographicPeak)
    def addMappedPeak (self, p):
        self.mappedPeaks.append(p)
        
    
    @check(MSChromatographicPeak)
    def addRawPeak(self, p):
        self.rawPeaks.append(p)
    
        
    def massExtraction(self, mass, ppm=10., asChromatogram=True):
        """
        mass: mass to consider
        massrange: error on mass, 0.01 ? typically for high resolution 
        
        """
        t=clock()
#        x_data,y_data=[],[]
        diff = ppm * mass / 1e6 if self.kind=='HighRes' else 1.
#        for spectrum in self.ispectra():
#            #_getEic(spectrum.x_data, spectrum.y_data, mass, diff, spectrum.rt, x_data, y_data)
#            idx = bisect(spectrum.x_data, mass, mass-diff, mass+diff)#massrange, mass+massrange)
#            x_data += [spectrum.rtmin for x in xrange(idx.shape[0])]            
#            y_data += spectrum.y_data[idx].tolist()
        x_data, y_data = massExtract(self, mass, ppm)
        print clock()-t

        if asChromatogram:
            return MSChromatogram(massrange=(mass, mass-diff, mass+diff),
                                  x_data=np.round(x_data, 4), 
                                  y_data=np.array(y_data, dtype=np.int), 
                                  sample=self)
        return np.round(x_data, 4), np.array(y_data, dtype=np.int)
    
    getEic=massExtraction #an alias
        
    
    def spectraInRTRange(self, rt, rtmin=0., rtmax=0.):
        """
        return iterator of spectra which rt is in the range rtmin, rtmax 
        
        """
        rts = np.array([spectra.rtmin for spectra in self.ispectra()])        
        m = mean(rts)#c'est pas la moyenne des differences plutot ??? TODO:check    
        rtmin = rt - m if rtmin==0. else rtmin
        rtmax = rt + m if rtmax==0. else rtmax
        idx = bisect(rts, rt, rtmin, rtmax)
        return [self.spectra[i] for i in idx]
    
    def ispectraInRTRange(self, rt, rtmin=1, rtmax=1):
        return (s for s in self.spectraInRTRange(rt, rtmin, rtmax))
                    
    
    def _calibration(self, data, polyDegree=3):
        """
        Calculate calibration constants for given references.
        data: (list) pairs of (measured mass, reference mass)
        model: ('linear' or 'quadratic')
        
        """
        measured, reference  = np.array([d[0] for d in data]), np.array([d[1] for d in data])
        p1 = np.polyfit(measured, reference)
        polynome = np.poly1d(p1)        
        return polynome
    
    
    def applyCalibration(self, data, model='quadratic'):
        """
        apply the result function and parameters from
        the calibration method
        
        """
        polynome = self._calibration(data, model)
        for spectra in self.ispectra():
            spectra.x_data = polynome(spectra.x_data)

    def spectrumAt(self, t):
        """
        TODO: improved this method with bisect algorithm
        return the spectrum a the exact specified time
        use spectraInRTRange if you have a range of time
        
        """
        s = self.spectraInRTRange(t)
        if not s:
            print "Error, spectra not found with this time %f"%t
            return
        return sorted(s, key=lambda s: abs(t-s.rt))[0]
    
    
    def doClustering(self, **p):
        """
        convenience function

        """
        from MetClustering import clusteringWrapper
        clusteringWrapper(self, **p)
    
    
    def normalize(self, p):
        """
        Normalize peak area by a float value
        TODO: don't forget to erase mappedPeaks of the treeView why ?
                
        """
        if not self.rawPeaks:
            print "No peaks detected..."
            return
        factor = p.area if isinstance(p, MSChromatographicPeak) else p
        for peak in self.irawPeaks():
            peak.area /= factor
        #print "erasing current Clusters if any"
        #self.mappedPeaks = MSPeakList(sample=self)
    
    def resizeSpectraLength(self, min_, max_):
        i = 0
        while i < len(self.spectra)-1 and self.spectra[i].rtmin < min_:
            i+=1
        i+=1
        minidx=i
        while i < len(self.spectra) and self.spectra[i].rtmin < max_:
            i+=1
        maxidx=i
        self.spectra = self.spectra[minidx:maxidx]
        #reperuction on TIC
        s = (self.chroma[0].x_data > min_) & (self.chroma[0].x_data < max_)
        self.chroma[0].x_data = self.chroma[0].x_data[s]
        self.chroma[0].y_data = self.chroma[0].y_data[s]
        self.restriction = (min_, max_)
    
    
    def exportPeakList(self, nameFile):
        if not self.rawPeaks:
            return
        with open(nameFile, 'w') as f:
            f.write("n, mass, rt, rtmin, rtmax, area, height\n")
            for i, peak in enumerate(self.imappedPeaks()):
                f.write(','.join([str(i+1), str(peak.mass()), str(peak.rt), 
                                  str(peak.rtmin), str(peak.rtmax), str(peak.area), str(peak.height), '\n']))
    
    def loadSpectrum(self, index):
        root = netcdf.netcdf_file(self.xmlfile)
        var = root.variables        
        mass_data = np.round(var['mass_values'][:].astype(np.float), 4) 
        intensity_data = var['intensity_values'][:].astype(np.int)
        scan_acquisition_time = np.round(var['scan_acquisition_time'][:].astype(np.float), 4)
        scan_index = var['scan_index'][:].astype(np.int)
        root.close()
        min_, max_, masses, intensity = _loadSpectrum(mass_data, intensity_data, 
                                                      scan_acquisition_time, 
                                                      scan_index, index)        
        return MSSpectrum((min_, max_, 0.), masses, intensity, sample=self)
    
    def loadAndExtract(self, mass, ppm=10., asChromatogram=True):
        t = clock()
        x_data,y_data=[],[]
        diff = ppm * mass / 1e6
        root = netcdf.netcdf_file(self.xmlfile)
        var = root.variables        
        mass_data = np.round(var['mass_values'][:].astype(float), 4) 
        intensity_data = var['intensity_values'][:].astype(int)
        scan_acquisition_time = np.round(var['scan_acquisition_time'][:].astype(float), 4)
        scan_index = var['scan_index'][:].astype(int)
        root.close()
        x, y = _getAllEic(mass_data, intensity_data, scan_acquisition_time,
                          scan_index, mass, diff)
        print clock()-t
        if asChromatogram:
            return MSChromatogram(massrange=(mass, mass-diff, mass+diff),
                                  x_data=np.round(x, 4), 
                                  y_data=np.array(y, dtype=np.int), 
                                  sample=self)
        return np.round(x, 4), np.array(y, dtype=int)
        

class MSSampleList(list):
    """
    Implementing a sample list
    
    """
    @slots
    def __init__(self, samples=[], kind='HighRes'):
        list.__init__(self, samples)
        self.kind=kind
        self.classes=None
        
#------------------------------------------------------------------------------ 
    def isamples(self):
        """
        return a generator on samples
        """
        for sample in self:
            yield sample
    
#------------------------------------------------------------------------------ 
    @check(MSSample)
    def addSample (self, sample):
        """
        check the instance then simple append
        """
        self.append(sample)
    
#------------------------------------------------------------------------------ 
    def getFiles(self, asShortName=False):
        """return the list of the name files"""
        return [spl.shortName() for spl in self.isamples()] if asShortName \
            else[spl.xmlfile for spl in self.isamples()] 

#------------------------------------------------------------------------------ 
    def sample(self, xmlfile, fullNameEntry=True):
        """return a sample object with specified name"""
        if fullNameEntry:
            for spl in self.isamples():
                if spl.xmlfile == xmlfile:
                    return spl
            print ("requested sample not found")
            return None
        for spl in self.isamples():
            if spl.shortName() == xmlfile:
                return spl
        return None

#------------------------------------------------------------------------------ 
    def removeSample(self, n):
        """
        Remove one sample by its name or by the object itself
        may raise an ValueError when Sample is not in the MSSampleList
        
        """
        if isinstance(n, MSSample):
            sample = n    
            try:
                self.remove(sample)
            except ValueError:
                print "%s can not be removed"%sample.shortName()
            del sample
            return    
        i =0
        while i < len(self):
            if self[i].shortName() == n:
                try:
                    self.remove(self[i])
                    del self[i]
                except ValueError:
                    print "%s can not be removed"%normcase(n).split('/')[-1]
                return
            i+=1
 
#------------------------------------------------------------------------------ 
    def peakGroup(self, p, rt=None, rtError=MEAN_RTSHIFT/2.):
        """
        make a peak group (under the form of a MSPeakList)
        given a mass or a chromatographic peak, rt and a rtError
        we specify an rt Error in case the peakList does not have parnet
        
        """
        pkl=MSPeakList()
        mass = p.mass() if isinstance(p, MSChromatographicPeak) else p
        rt = p.rt if isinstance(p, MSChromatographicPeak) else rt
        for i, s in enumerate(self.isamples()):
            peakList=s.rawPeaks.peaksInMZRTRange(mass, rt, rtError, deltam= 2 * s.ppm / 1e6 * mass)
            if not peakList:
                #pkl.append(None)
                pkl.append(MSChromatographicPeak(sample=s))
            else:
                pkl.addPeak(sorted(peakList, key=lambda x:abs(x.mass()-mass))[0])
        return pkl
    
#------------------------------------------------------------------------------ 
    def peaksGrouping(self):
        """
        TODO: use this function in the next functions
        return a dictionnary containing tuple(meanMass, meanRt)        
        
        """
        if not self:
            return
        treated = MSPeakList()
        commonPeaks = {}
        for spl in self.isamples():
            for peak in spl.irawPeaks():
                if not peak.isGood or peak in set(treated):
                    continue
                group = self.peakGroup(peak)
                if not group:
                    continue
                #group = MSPeakList([p for p in group if p is not None])
                treated += group
                mass, rt = group.masses(asarray=True), group.rts(asarray=True)
                s = mass>0
                meanMass, meanRt = mass[s].mean(), rt[s].mean()
                commonPeaks[(meanMass, meanRt)] = group
        return commonPeaks
    
#------------------------------------------------------------------------------ 
    def nonXCMSPeakGroup(self, m, rt=None, rtError=MEAN_RTSHIFT/2.):
        """
        The same than previous but for non XCMS Peaks
        
        """
        pkl=MSPeakList()
        mass = m.mass() if isinstance(m, MSChromatographicPeak) else m
        rt_ = m.rt if isinstance(m, MSChromatographicPeak) else rt    
        for s in self.isamples():
            c=s.massExtraction(mass, asChromatogram=True)
            c.findNonXCMSPeaks()
            p=c.peaks.peaksInMZRTRange(mass, rt_, rtError, deltam=2 * s.ppm / 1e6 * mass)
            if not p:
                continue
            pkl.append(sorted(p, key=lambda x:abs(mass-x.mass()))[0])
        return pkl

#------------------------------------------------------------------------------
    def kmeansClustering(self, nbClust=3):
        """
        simplest implementation of the kmeans algorihtm
        return:
            @km :centroids
            @idx: each observation belongs to cluster
            @group: peaks used to compute kmeans
        """
        l =[]
        group = self.peaksGrouping()
        for v in group.itervalues():
            #no so long inner for boucle
            for x in v:
                if x is None:
                    x = 0.
            l.append(v)
        km, idx = kmeans2(np.array(l), nbClust)
        return km, idx, group
            
        
        
#------------------------------------------------------------------------------ 
    def alignRawData(self, sampleList, polyDegree=3):
        if not sampleList:
            print "Empty sample list"
            return
        refSample = sorted(sampleList, key=lambda x:len(x.spectra))[-1]
        refrt = np.array([s.rtmin for s in refSample.ispectra()])
        others = [s for s in sampleList if s != refSample]
        for sample in others:
            rts = np.array([s.rtmin for s in sample.ispectra()])
            minLength = min(refrt.shape[0], rts.shape[0])
            parameters = np.polyfit(rts[:minLength], rts[:minLength], polyDegree)
            polynome = np.poly1d(parameters)            
            shiftCalc = polynome(rts)
            for i in xrange(len(shiftCalc)):
                sample.spectra[i].rtmin = shiftCalc[i]
            tot_intensity = sample.chroma[0].y_data[:]
            sample.chroma=[]
            sample.chroma.append(MSChromatogram((0.,
                                          0.,
                                          0.),
                                          np.array([0.]+[s.rtmin for s in sample.ispectra()]),
                                          tot_intensity,
                                          sample=sample))
                                          
#------------------------------------------------------------------------------ 
    def alignPeaksInRTDimension(self, sampleList, polyDegree=3, minfrac=50., errorRt=6.):
        """
        alignment of chromtographic peaks
        sampleList ? why not on itself ? for more flexibility ? staticmethod ?        
        minfrac: the peak is used for aligning if it is found in 75 %
        of samples
        
        """
        if not sampleList:
            return
        if not all([sample.rawPeaks for sample in sampleList]):            
            print "Error, at least one sample has no detected peaks"
            print "aligning on RT only ?"
            return    
        refSample = sorted(sampleList, key=lambda x:len(x.rawPeaks))[-1]
        print "refSample:", refSample.shortName()        
        others = [s for s in sampleList if s != refSample]
        #first get peaks of refsample found > to the threshold
        peaksRef=defaultdict(MSPeakList)        
        for peak in refSample.rawPeaks.ipeaks():
            if not peak.isGood:
                continue
            for s_ in others:
                match = s_.rawPeaks.peaksInMZRTRange(peak.mass(), peak.rt, s_.ppm, errorRt/2.)
                if not match:
                    continue
                bestMatch = sorted(match, key=lambda x:(peak.mass() - x.mass()))[0]
                peaksRef[peak].append(bestMatch)
            if not len(peaksRef[peak]) / float(len(sampleList)) > minfrac/100.:
                del peaksRef[peak]
        if not peaksRef:
            print "Cannot group peaks... try increasing errorRt parameters or decreasing threshold parameters"
            return
        for s_ in others:
            #aligning the spectra
            measured, expected = [], []
            for i, p in enumerate(peaksRef.iterkeys()):
                l =  [p__ for p__ in peaksRef[p] if p__.sample == s_]                       
                if not l:
                    continue
                p_ = l[0]
#                measured.append(p_.rt)
#                expected.append(p.rt)
                for j in xrange(min(len(p.spectra), len(p_.spectra))):
                    measured.append(p_.spectra[j].rtmin)
                    expected.append(p.spectra[j].rtmin)
            #starts the fitting
            expected = np.array(expected)
            measured = np.array(measured)
            #shift = measured - expected
            #shift = expected - measured            
            #parameters,  success = leastsq(_residuals, initials[:], args=(expected, shift))
            
            #parameters = np.polyfit(expected, shift, polyDegree)
            parameters = np.polyfit(measured, expected, polyDegree)
            #print parameters            
            #print "paramters optimized:", parameters            
            spectra_ = np.array([sp.rtmin for sp in s_.ispectra()])
            polynome = np.poly1d(parameters)            
            shift = polynome(spectra_)
            print shift
            #print 'len shift', shift.shape[0]
            for peak in s_.rawPeaks.ipeaks():                           
                minidx = s_.spectra.index(peak.spectra[0])
                maxidx = s_.spectra.index(peak.spectra[-1])
                meanshift = mean(shift[minidx:maxidx])
                #print shift[minidx:maxidx]
                peak.rt = meanshift                
                peak.rtmin = shift[minidx]
                peak.rtmax = shift[maxidx]
            #apply the fitting to Spectra
            for i in xrange(len(s_.spectra)):
                s_.spectra[i].rtmin = shift[i]

#------------------------------------------------------------------------------ 
    def alignRawDataByDtw(self, sampleList, deriv, showImg=False):
        """
        deriv is a boolean
        
        """
        refSample = sorted(sampleList, key=lambda x:len(x.spectra))[0]
        refrt = np.array([s.rtmin for s in refSample.ispectra()])
        others = [s for s in sampleList if s != refSample]
        dtws={}
        for i, sample in enumerate(others):
            rts = np.array([s.rtmin for s in sample.ispectra()])
            d = Dtw(derivative=deriv, onlydist=False)
            d.compute(refrt, rts)
            if showImg:
                dtws[sample] = (d.px, d.py, None) if i < len(others)-1 else (d.px, d.py, d.cost.T)
                #matrix is very expensive
            else:
                dtws[sample] = (d.px, d.py, None) 
            del d
        return dtws, refSample, others
    
    def applyDtwChanges(self, dtws, ref, others):
        pass
#------------------------------------------------------------------------------ 
    def exportClusterMatrix(self, nameFile):
        """
        write information about clusterized peaks on a csv file
        
        """
        treated = MSPeakList()
        names = [spl.shortName() for spl in self.isamples()]
        with open(nameFile, 'w') as f:
            f.write(','.join(['peak']+ names +['\n']))
            for spl in self.isamples():
                for peak in spl.imappedPeaks():
                    if peak in treated:
                        continue
                    group = self.peakGroup(peak)
                    treated += group
                    f.write(str(peak)+',')
                    s=[0] * len(names)
                    for p in group:
                        if p is None:
                            continue
                        idx = names.index(p.sample.shortName())
                        s[idx] = p.area
                    f.write(','.join(map(str, s)))
                    f.write('\n')
    
#------------------------------------------------------------------------------ 
    def pearsonIntraCalculation(self):
        for spl in self.isamples():
            for p in spl.imappedPeaks():
                p.pCalcBasedOnPeakShape()
        
#------------------------------------------------------------------------------ 
    def pearsonInterCalculation(self):
        groups = self.peaksGrouping()
        if not groups:
            return
        corr = 0.
    
                    