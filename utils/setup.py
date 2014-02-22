from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [Extension("bisection", ["bisection.pyx"],
                            extra_compile_args=['-IC:\\Python27\\Lib\\site-packages\\numpy\\core\\include'])]

setup(
  name = 'bisection',
  cmdclass = {'build_ext': build_ext},
  ext_modules = ext_modules
)