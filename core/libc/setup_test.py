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
      download_url='https://mlpy.fbk.eu/wiki/MlpyDownloads',
      license='GPLv3',
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Science/Research',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU General Public License (GPL)',
                   'Natural Language :: English',
                   'Operating System :: POSIX :: Linux',
                   'Operating System :: POSIX :: BSD',
                   'Operating System :: Unix',
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: Microsoft :: Windows',
                   'Programming Language :: C',
                   'Programming Language :: Python',
                   'Topic :: Scientific/Engineering :: Artificial Intelligence',
                   ],
      cmdclass = {'build_ext': build_ext},
      ext_modules=[Extension('_libc', ['libc.c', 'pylibc.pyx'],
                             include_dirs=base_include,
                             extra_compile_args=extra_compile_args),
                   
                   ],
      data_files=data_files
      )
