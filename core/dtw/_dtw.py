## This code is written by Davide Albanese, <albanese@fbk.eu>
## (C) 2009 Fondazione Bruno Kessler - Via Santa Croce 77, 38100 Trento, ITALY.

## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.

## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.

__all__ = ['Dtw']

import numpy as np
import dtw


def dtwc(x, y, derivative=False, startbc=True, steppattern='symmetric0',  wincond = "nowindow", r=0.0, onlydist=True):
    """Dynamic Time Warping.

    Input
    
      * *x* - [1D numpy array float / list] first time series
      * *y* - [1D numpy array float / list] second time series
      * *derivative* - [bool] Derivative DTW (DDTW).
      * *startbc* - [bool] (0, 0) boundary condition
      * *steppattern* - [string] step pattern ('symmetric', 'asymmetric', 'quasisymmetric')
      * *wincond* - [string] window condition ('nowindow', 'sakoechiba') 
      * *r* - [float] sakoe-chiba window length
      * *onlydist* - [bool] linear space-complexity implementation. Only the current and previous
        columns are kept in memory.
        
    Output

      * *d* - [float] normalized distance
      * *px* - [1D numpy array int] optimal warping path (for x time series) (for onlydist=False)
      * *py* - [1D numpy array int] optimal warping path (for y time series) (for onlydist=False)
      * *cost* - [2D numpy array float] cost matrix (for onlydist=False)
    """


    if steppattern == 'symmetric0':
        sp = 0
    elif steppattern == 'asymmetric0':
        sp = 1
    elif steppattern == 'quasisymmetric0':
        sp = 2
    else:
        raise ValueError('step pattern %s is not available' % steppattern)
    
    if wincond == 'nowindow':
        wc = 0
    elif wincond == 'sakoechiba':
        wc = 1
    else:
        raise ValueError('window condition %s is not available' % wincond)
    
        
    if derivative:
        xi = dtw.der(x)
        yi = dtw.der(y)
    else:
        xi = x
        yi = y

    return dtw.dtw(xi, yi, startbc=startbc, steppattern=sp, onlydist=onlydist, wincond=wc, r=r)


class Dtw(object):
    """Dynamic Time Warping.

    Example:

    >>> import numpy as np
    >>> import mlpy
    >>> x = np.array([1,1,2,2,3,3,4,4,4,4,3,3,2,2,1,1])
    >>> y = np.array([1,1,1,1,1,1,1,1,1,1,2,2,3,3,4,3,2,2,1,2,3,4])
    >>> dtw = mlpy.Dtw(onlydist=False)
    >>> dtw.compute(x, y)
    0.36842105263157893
    >>> dtw.px
    array([ 0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  2,  3,  4,  5,  6,  7,  8,
            9, 10, 11, 12, 12, 12, 13, 14, 15], dtype=int32)
    >>> dtw.py
    array([ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 14, 14,
           14, 15, 15, 16, 17, 18, 19, 20, 21], dtype=int32)
    """

    def __init__(self, derivative=False, startbc=True, steppattern='symmetric0', wincond="nowindow", r=0.0, onlydist=True):
        """
        :Parameters:
          derivative : bool
                     derivative DTW (DDTW)
          startbc : bool
                  forces x=0 and y=0 boundary condition
          steppattern : string ('symmetric', 'asymmetric', 'quasisymmetric')
                      step pattern
          wincond : string ('nowindow', 'sakoechiba') 
                  window condition
          r : float
            sakoe-chiba window length
          onlydist : bool
                   linear space-complexity implementation. Only the current
                   and previous columns are kept in memory.
        """

        
        self.derivative = derivative
        self.startbc = startbc
        self.steppattern = steppattern
        self.wincond = wincond
        self.r = r
        self.onlydist=onlydist

        self.px = None
        self.py = None
        self.cost = None

    def compute(self, x, y):
        """
        :Parameters:
          x : 1d numpy array
            first time series
          y : 1d numpy array
            second time series

        :Returns:
          d : float
            normalized distance

        :Attributes:
          Dtw.px : 1d numpy array (int32)
                 optimal warping path (for x time series) (if onlydist=False)
          Dtw.py : 1d numpy array (int32)
                 optimal warping path (for y time series) (if onlydist=False)
          Dtw.cost : 2d numpy array
                   cost matrix (if onlydist=False)          
        """


        res = dtwc(x=x, y=y, derivative=self.derivative, startbc=self.startbc, steppattern=self.steppattern,
                   wincond=self.wincond, r=self.r, onlydist=self.onlydist)

        if self.onlydist == True:
            return res

        else:
            self.px = res[1]
            self.py = res[2]
            self.cost = res[3]
            
            return res[0]
