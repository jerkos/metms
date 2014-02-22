from libcpp.vector cimport vector
from libcpp cimport bool
from libc.stdlib cimport free
#import numpy as np
#cimport numpy as np

cdef extern from "string" namespace "std":
    cdef cppclass string:
        char* c_str()

cdef extern from "generator.h":
    cdef cppclass Element:
            Element(char*, double, float, char*, int, int, int, int)
            char* sym
            double mass	
            float val
            char* key
            int min
            int max
            int cnt
            int save
    
    cdef cppclass MSFormulaGenerator:
        MSFormulaGenerator(double, double, char*)
        vector[Element] el
        double electron
        int nr_el
        double charge
        double mz
        double tol
        
        vector[string] formulas
        vector[double] massDifference
        
        void split(string&, char, vector[string]&)
        double  calc_mass()
        float calc_rdb()
        vector[string] do_calculations()
        bool calc_element_ratios(bool)
        string toString(int)
        
        vector[string] getFormulas()
        vector[double] getMassDifference()


cdef class pyFormulaGenerator:
    cdef MSFormulaGenerator *ptr
    
    def __cinit__(self, double a, double b, char* c):
        self.ptr = new MSFormulaGenerator(a, b, c)
    
    def __dealloc__(self):
        del self.ptr
    
    def doCalculations(self):
        cdef :
            list results=[], pyDiff=[]#np.ndarray['string', ndim=1] results
            Py_ssize_t i
            vector[string] f
            vector[double] diff
            #np.ndarray[float, ndim=1] pyDiff        
            
        f = self.ptr.do_calculations()
        diff = self.ptr.getMassDifference()        
        #results = np.zeros(r.size(), 'string')
        #pyDiff = np.zeros(<int>f.size(), float)
        for i in xrange(<int>f.size()):
            results.append(f[i].c_str())
            pyDiff.append(diff[i])
        return results,  pyDiff
    
        
        