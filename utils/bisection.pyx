cimport numpy as np
import numpy as np
cimport cython
from collections import defaultdict
#from core.MetObjects import MSPeakList
from libc.stdlib cimport calloc, free
#from _bisect import bisect_left

@cython.wraparound(False)
@cython.boundscheck(False)
cdef int bisect_left(np.ndarray[np.float64_t, ndim=1] a, float x, int lo=0, int hi=0):
    """Return the index where to insert item x in list a, assuming a is sorted.

    The return value i is such that all e in a[:i] have e < x, and all e in
    a[i:] have e >= x.  So if x already appears in the list, a.insert(x) will
    insert just before the leftmost x already there.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """
    cdef int mid
    if lo < 0:
        return -1
    hi = a.shape[0]
    while lo < hi:
        mid = (lo+hi)//2
        if a[mid] < x: 
            lo = mid+1
        else: 
            hi = mid
    return lo


@cython.wraparound(False)
@cython.boundscheck(False)
cpdef bisection(np.ndarray[double, ndim=1] a,  float x, float minm, float maxm):
    """
    @summary:
    This function is mainly used to find indexes of certain values in a SORTED list(reducing 
    complexity)
    @a :list or np.array
    @x:value
    @minvalue
    @maxvalue
    """
    cdef int i, j, N = a.shape[0], min_=0, max_=0
    if N == 0:
        return np.arange(min_, max_) 
    
    i = bisect_left(a, x)
    if i == -1:
        return np.arange(min_, max_) 
        
    if a[i] < maxm and a[i] > minm and i !=N:
        j=i+1
        while j < N and a[j] < maxm:
            j+=1
        max_ = j
        j=i-1
        while j > 0 and  a[j] > minm:
            j-=1
        min_ = j
        return np.arange(min_, max_)
    min_ = N-1
    max_ = N
    return np.arange(min_, max_)


"""
abs redefinition much more rapid in C
"""
cpdef inline float abs(float a): return a if a >=0 else -a

#===============================================================================
# Mass extraction and spetrum
#===============================================================================
@cython.wraparound(False)
@cython.boundscheck(False)
cpdef tuple _loadSpectrum(np.ndarray[np.float_t, ndim=1] masses, np.ndarray[int, ndim=1] intensity, np.ndarray[np.float_t, ndim=1] scan_acq, np.ndarray[int, ndim=1] scan_index, int i):
    return scan_acq[i], scan_acq[i+1], masses[scan_index[i]:scan_index[i+1]], intensity[scan_index[i]:scan_index[i+1]]

@cython.wraparound(False)
@cython.boundscheck(False)
cpdef tuple _getAllEic(np.ndarray[np.float_t, ndim=1] masses, np.ndarray[int, ndim=1] intensities, np.ndarray[np.float_t, ndim=1] scan_acq, np.ndarray[int, ndim=1] scan_index, float m,  float diff):
    cdef list x_data=[], y_data=[]
    cdef list i
    cdef np.ndarray[np.float_t, ndim=1] mass
    cdef np.ndarray[int, ndim=1] intensity        
    cdef Py_ssize_t N, k, j
    cdef np.float_t x, y
    for j from 0 <= j < scan_index.shape[0]-1:
        x, y, mass, intensity = _loadSpectrum(masses, intensities, scan_acq, scan_index, j)            
        i = bisection(mass, m, m-diff, m+diff)#massrange, mass+massrange)
        if not i:
            continue
        N = len(i)
        for k from 0 <= k < N:
            x_data.append(x)
            y_data.append(intensity[i[k]])#max_l(intensity))
    return x_data, y_data
#
#
#cpdef _getEic(np.ndarray[np.float_t, ndim=1] masses, np.ndarray[int, ndim=1] intensity, np.float_t m, np.float_t diff, np.float_t rt, list x_data, list y_data):
#    cdef list i
#    cdef Py_ssize_t N
#    i = bisection(masses, m, m-diff, m+diff)
#    if not i:
#        return
#    N = len(i)
#    
#    #for k from 0 <= k < N:
#    x_data.append(rt)
#    y_data.append(max_l(intensity[i]))
    #return x_data, y_data
    

#===============================================================================
# MIN MAX FUCNTIONS
#===============================================================================
cpdef inline float max(float a, float b): return a if a > b else b


#####################On Array
@cython.wraparound(False)
@cython.boundscheck(False)
cpdef int max_l(np.ndarray[int, ndim=1] a):
    cdef int m = 0, N = a.shape[0], i
    for i from 0 <= i < N:
        if a[i] > m:
            m = a[i]
    return m

@cython.wraparound(False)
@cython.boundscheck(False)
cpdef float max_f(np.ndarray[np.float_t, ndim=1] a):
    cdef float m = 0.
    cdef int N = a.shape[0], i
    for i from 0 <= i < N:
        if a[i] > m:
            m = a[i]
    return m
    
@cython.wraparound(False)
@cython.boundscheck(False)
cpdef int min_l(np.ndarray[int, ndim=1] a):
    cdef int m = int(1e12), N = a.shape[0], i
    for i from 0 <= i < N:
        if a[i] < m:
            m = a[i]
    return m

@cython.wraparound(False)
@cython.boundscheck(False)
cpdef float min_f(np.ndarray[np.float_t, ndim=1] a):
    cdef float m = 1e12
    cdef int N = a.shape[0], i
    for i from 0 <= i < N:
        if a[i] < m:
            m = a[i]
    return m

@cython.wraparound(False)
@cython.boundscheck(False)
cpdef float mean(np.ndarray[np.float_t, ndim=1] a):
    cdef float result = 0.
    cdef int i
    for i from 0 <= i < a.shape[0]:
        result += a[i]
    return result / a.shape[0]

@cython.wraparound(False)
@cython.boundscheck(False)
cpdef float sum_f(np.ndarray[np.float_t, ndim=1] a):
    cdef float res = 0.
    cdef Py_ssize_t i, n=a.shape[0]
    for i in xrange(n):
        res += a[i]
    return res

#===============================================================================
# Help for clustering module
#===============================================================================
@cython.wraparound(False)
@cython.boundscheck(False)
cpdef list massGenPerGroup(list rtGroup, np.ndarray[np.float_t, ndim=2] adducts, float ppm):

    cdef int N = len(rtGroup), i, k, M, O#, index, P
    cdef float minmz, maxmz, mz, value#, mass, diff, d
    cdef np.ndarray[np.float_t, ndim=1] maxtest
    cdef list final = [], masses
    cdef object isIncluded
    
    for i from  0 <= i < N:
        maxtest = np.array([x.mass() for x in rtGroup[i]])
        minmz, maxmz = min_f(maxtest), max_f(maxtest)        
        results=defaultdict(list)
        M = len(rtGroup[i])
        for j from 0 <= j < M:
            O = adducts.shape[0]
            for k from 0 <= k < O:   
                #check for dimer trimer etc...
                mz = <float>(rtGroup[i][j].mass() / adducts[k][1]) + adducts[k][0]
                if not mz < maxmz and mz > minmz:
                    continue
                isIncluded=False
                for value in results.iterkeys():
                    if <float>abs(mz - value) < <float> (ppm * max(mz, value)):
                        if rtGroup[i][j] not in results[value]:
                            results[value].append(rtGroup[i][j])
                            isIncluded=True
                        break
                if not isIncluded:
                    results[mz].append(rtGroup[i][j])
        final.append(results)
    return final


cpdef tuple makeAnnotations(np.ndarray[np.float_t, ndim=2] adducts, a, float pmass, float ppm):
    cdef int N = adducts.shape[0]
    cdef float p, sup, inf
    for i from 0 <= i < N:
        p = pmass * adducts[i][1] + adducts[i][0]
        sup = p + pmass*ppm
        inf = p - pmass * ppm
        if pmass > inf and pmass < sup:
            return adducts[i], a[adducts[i]]
            #f.annotation[annot]=adducts[annot]

#===============================================================================
# Help for isotopic detection
#===============================================================================
cpdef object _getMatchingPeaks(object peaks, object peak, float mass, float ppm, float rtError):
    
    cdef list matchingRtPeaks
    cdef Py_ssize_t i, j, k, m, n
    cdef float massToCheck, diff, d 
    cdef object pk, pic
            
    massToCheck=peak.mass()+mass
                
    p = peaks.peaksInMZRange(massToCheck, <float> ppm*massToCheck) #deltart
    matchingRtPeaks = []#will contain all matching peak in rt
    n = len(p)    
    for k in xrange(len(p)):    
        if abs(<float>peak.rt - p[k].rt) <= rtError:
            matchingRtPeaks.append(p[k])
    
    if matchingRtPeaks:
        diff = 1e3
        pic = matchingRtPeaks[0]
        m = len(matchingRtPeaks)
        for j from 0 <= j < m:
            d = peak.mass() - matchingRtPeaks[j].mass()
            if d < diff:
                diff = d
                pic = matchingRtPeaks[j]
        return pic
    return None
#        
#ctypedef np.ndarray[np.float_t, ndim=1] ND_ARRAY
@cython.wraparound(False)
@cython.boundscheck(False)
cpdef list _resolutionAdjustment(list sortedlist, float errormass, float limitp=1e-6, object adaptError=False):
    #def resolutionAdjustment(l, errormass, fwhm=None, adaptError=False):
    """
    merge peaks when the distance between them is inferior to the deltam parameter
    to test, but seems to be good...
    l : np.array of tuple (mass, prob) sorted !!!!!
    ppm: incertitude on the mass high res: generally (10/1e6)*peak.mass()
    fwhm:  for the convolution...to have a nice isotopic cluster
    """
    cdef list final=[], peaks
    cdef tuple m, M
    cdef Py_ssize_t i= 0, n = len(sortedlist), y
    cdef float mass, prob    
    #cdef np.ndarray[np.float_t, ndim=2] a
    
    while i < n-1:#we miss the last one...
        m = sortedlist[i]
        M = sortedlist[<int>i+1]
        peaks=[]
        while <float>M[0]-m[0] < errormass and i < <int>n-2:
            peaks.append(m)
            peaks.append(M)
            i+=1
            m = sortedlist[i] 
            M = sortedlist[<int>i+1]      
        if peaks:
            y = len(peaks)
            mass = sum([<float>peak[0]*peak[1] for peak in peaks])/y#ponderate mean peak[0]*peak[1]
            prob = sum([peak[1] for peak in peaks])/y
            if prob > limitp:
                final.append((mass,prob))
        else:
            final.append(m)
            if i == n-2:
                final.append(sortedlist[<int>n-1])
        i+=1
    
    #lastone = final if final else sortedlist
    #return reversed(sorted(final, key=lambda x:x[1]))#final sorted by the largest peak in the first place an then decrease 
    #final.sort(key=lambda x:x[1]); #final.reverse()
    return final


cdef np.ndarray[np.float_t, ndim=1] mult(np.ndarray[np.float_t, ndim=2] l):
    cdef Py_ssize_t n = l.shape[0],i
    cdef np.ndarray[np.float_t, ndim=1] res = np.zeros(n)    
    for i in xrange(n):
        res[i] = l[i,0] * l[i,1]
    return res
        


#===============================================================================
# Peaks In RT Range
#===============================================================================
cpdef list _peaksInRtRange(np.ndarray[np.float_t, ndim=1] rts, float rt, float r, float rinf=-1., float rsup=-1.):
    cdef float r_inf, r_sup    
    r_inf=rt-r if rinf==-1. else rt-rinf
    r_sup =rt+r if rsup==-1. else rt+rsup
    cdef Py_ssize_t i
    cdef list indexes = []    
    for i from 0 <= i < <int>rts.shape[0]:
        if rts[i] > r_inf and rts[i] < r_sup:
            indexes.append(i)
    return indexes


#===============================================================================
# FITTING MODEL
#===============================================================================
@cython.boundscheck(False)
cpdef _linearModel(np.ndarray[np.float_t, ndim =1] array, np.ndarray[np.float_t, ndim =1] params):
    """
    function used for fitting
    
    """
    if len(params) < 2:
        raise ValueError, 'params must be at least an array of length 2'
    cdef Py_ssize_t i
    cdef int N = len(array)
    for i from 0 <= i < N:
        array[i]= params[0] * array[i] + params[1]


@cython.boundscheck(False)
cpdef _quadraticModel(np.ndarray[np.float_t, ndim =1] x, np.ndarray[np.float_t, ndim =1] params):
    """
    use for fitting
    quadratic model
    
    """
    if len(params) < 3:
        raise ValueError, 'params must be at least an array of length 3'
    cdef Py_ssize_t i
    cdef int N = len(x)
    for i from 0 <= i < N:
        x[i]= params[0] * x[i]**2 + params[1] * x[i] +params[0]