# mlpy setup file

from distutils.core import setup, Extension
from distutils.sysconfig import *
from distutils.util import *
from Cython.Distutils import build_ext
import os
import numpy

data_files = []



## Extra compile args
extra_compile_args = ['-Wno-strict-prototypes']

# Python include
py_include = get_python_inc()

# NumPy include
numpy_lib = os.path.split(numpy.__file__)[0]
numpy_include = os.path.join(numpy_lib, 'core/include')

# NumPy support include
numpysupport_include = 'mlpy/numpysupport'

# Base include
base_include  = [py_include, numpy_include]


# Setup
setup(name = 'MLPY',
      version='2.2.2',
      description='mlpy - Machine Learning Py - ' \
          'High-Performance Python Package for Predictive Modeling',
      author='mlpy Developers - FBK-MPBA',
      author_email='albanese@fbk.eu',
      url='https://mlpy.fbk.eu',
      license='GPLv3',
    
      cmdclass = {'build_ext': build_ext},
      ext_modules=[Extension('dtw', ['dtw.c'],
                             include_dirs=base_include,
                             extra_compile_args=extra_compile_args),
                   
                   ],
      data_files=data_files
      )