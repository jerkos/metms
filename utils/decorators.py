#-*- coding: utf-8 -*-

"""
Some useful functions and decorators
"""

#========================================
#decorators
#usage: 'func' a usual function
#
#@decorators
#def func(*args, **kwargs)
#
#========================================
def memo(func):
   cache = {}
   def init(*args, **kw):
      try:
         return cache[args]
      except KeyError:
         value = func(*args, **kw)
         cache[args] = value
         return value
   return init
     



def slots(func):
    """
    provide a decorator for putting attributes in the __slot__ tuple
    useful when you have to create objects of the same kinds 
    
    """
    def init(*args, **kwargs):
        inst=args[0]
        func(*args, **kwargs)
        if hasattr(inst, '__slots__'):
            slots = list(inst.__slots__)
            for name in list(inst.__dict__.keys()):
                if name not in slots:
                    slots.append(name)
            slots.append('__dict__')#warning
            inst.__slots__ = tuple(slots)
        else:
            inst.__slots__ =list(inst.__dict__.keys())
    return init
    


def check(type_):
    """
    decorator for checking type of instance before adding
    """
    def wrapper(func):
        def init(*args, **kw):
            if not isinstance(type_, type):
                print ('Bad use of the check decorator')
                return
            if not isinstance(args[1], type_):#case its instance methods
                raise TypeError
            func(*args, **kw)
        return init
    return wrapper
    



def careAttributes(func):
    """protect a function from AttributeError"""
    def init(*args, **kwargs):        
        try:
            func(*args, **kwargs)
        except AttributeError:
            print ("Error on an attribute when calling %s"(func.__name__))
    return init       
            

def guiDependant(func):
    """just raise a warn """
    def init(*args, **kwargs):
        try:
            import PyQt4
            return func(*args, **kwargs)
        except ImportError:
            import warnings
            warnings.warn("this a PyQt4 dependant function, PyQt4 is not installed")
    return init



import warnings
def deprecated(func):
    """just raise a warn """
    def init(*args, **kwargs):
        warnings.warn("deprecated function:%s"%func.__name__, DeprecationWarning)
        return func(*args, **kwargs)
    return init


def sampleDependant(string):
    """
    decorator for checking type of instance before adding
    """
    def wrapper(func):
        def init(*args, **kw):
            if string not in ('MRM', 'HighRes'):
                print ('Bad use of the sample dependant decorator')
                return
            if not args[0].kind or args[0].kind != string:
                raise ValueError
            func(*args, **kw)
        return init
    return wrapper 
