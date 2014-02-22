from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext


module = Extension('_generator',
                    sources = ['gen.pyx','generator.cpp'],
                    language='c++')

setup (name = 'generator',
       version = '1.0',
       description = 'This package allow to create all possible chemical formulas given a certain mass',
       ext_modules = [module],
        cmdclass={'build_ext': build_ext})