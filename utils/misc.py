#================================================
#HELPING FUNCTIONS
#================================================
def timeFormat(tim, flags='s'):
    """processing data format during parsing"""

    #cor_time=""
    #for i in xrange(2,len(tim)-1):
    #    cor_time+=tim[i]
    c= float(tim.strip('PTS'))#cor_time)
    if flags =='min':
        return c/60.
    return c



def dataNormalization1(self, data_list, maxi, value):
    """ 
    helping function to normalize data
    TODO use numpy to do that !
    """
    new_data =list()
    for x in data_list:
        if x == maxi:
            new_data.append(value)
        else:
            new_data.append((x*value)/maxi)
    return new_data
        



def dataNormalization(data_list, value):
    maxi =max(data_list)
    new_data =list()
    for x in data_list:
        if x == maxi:
            new_data.append(value)
        else:
            new_data.append((x*value)/maxi)
    return new_data


#===============================================================================
# Class ORDERED DICT
#===============================================================================
from UserDict import DictMixin
class OrderedDict(dict, DictMixin):
    """
    Explicit name, provide a ordered dictionnary object (order is made during the object 
    constructions), does not exist in python <2.7
    """

    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        try:
            self.__end
        except AttributeError:
            self.clear()
        self.update(*args, **kwds)

    def clear(self):
        self.__end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.__map = {}                 # key --> [key, prev, next]
        dict.clear(self)

    def __setitem__(self, key, value):
        if key not in self:
            end = self.__end
            curr = end[1]
            curr[2] = end[1] = self.__map[key] = [key, curr, end]
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        key, prev, next = self.__map.pop(key)
        prev[2] = next
        next[1] = prev

    def __iter__(self):
        end = self.__end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.__end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def popitem(self, last=True):
        if not self:
            raise KeyError('dictionary is empty')
        if last:
            key = reversed(self).next()
        else:
            key = iter(self).next()
        value = self.pop(key)
        return key, value

    def __reduce__(self):
        items = [[k, self[k]] for k in self]
        tmp = self.__map, self.__end
        del self.__map, self.__end
        inst_dict = vars(self).copy()
        self.__map, self.__end = tmp
        if inst_dict:
            return (self.__class__, (items,), inst_dict)
        return self.__class__, (items,)

    def keys(self):
        return list(self)

    setdefault = DictMixin.setdefault
    update = DictMixin.update
    pop = DictMixin.pop
    values = DictMixin.values
    items = DictMixin.items
    iterkeys = DictMixin.iterkeys
    itervalues = DictMixin.itervalues
    iteritems = DictMixin.iteritems

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, self.items())

    def copy(self):
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d

    def __eq__(self, other):
        if isinstance(other, OrderedDict):
            return len(self)==len(other) and self.items() == other.items()
        return dict.__eq__(self, other)

    def __ne__(self, other):
        return not self == other






from PyQt4 import QtCore
class MSMailThread(QtCore.QThread):
    """
    @summary:
        check the new emails...
        essentially used to know
        when a job running on a
        cluster ends
    """
    
    def __init__(self, **k):
        """
        @user: email
        @password: password of the email count
        @server: only imap server are supported
        """
        self.user=k.get('user')
        self.passw=k.get('passw')
        self.server=k.get('server')
    
    def run(self):
        import imaplib, email
        while True:
            m = imaplib.IMAP4_SSL(self.server)
            m.login(self.user, self.passw)
            m.select(readonly=True)
            newz = m.status('INBOX', '(RECENT UNSEEN MESSAGES)')[1][0]#list messages unseen
            if not newz:
                continue
            for el in newz:
                typ, msg_data = c.fetch(el, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_string(response_part[1])
                        for header in [ 'subject', 'to', 'from' ]:
                            if "support@genopole.fr" in msg[header]:
                                print ("job over, mail received...")
                                m.logout()
                                return
            QtCore.QThread.sleep(60)#sleep during one minute
     



class Colormap(object):

    def __init__(self, name, *args, **kwargs):
        ''' Build a new colormap from given (value,color) list.

           name: str
               Colormap name

           args: [(value,Color),...]
               Value/color couples to build colormap from.
               Values must be normalized between 0 and 1
        '''
        self.name = name
        self.vcolors = []
        self.alpha = 1.0
        for value,color in args:
            self._append(value, color)
        

    def _append(self, value, color):
        ''' Append a new value/color '''
        self.vcolors.append( [value,color] )
        self.vcolors.sort(lambda x,y: int(x[0]-y[0]))


    def _get_color (self, value, asQColor=False, alpha=0.5):
        ''' Get interpolated color from value '''

        if not len(self.vcolors):
            return (0.,0.,0.,self.alpha)
        elif len(self.vcolors) == 1:
            return self.vcolors[0][1]
        elif value < 0.0:
            return self.vcolors[0][1]
        elif value > 1.0:
            return self.vcolors[-1][1]
        sup_color = self.vcolors[0]
        inf_color = self.vcolors[-1]
        for i in xrange (len(self.vcolors)-1):
            if value < self.vcolors[i+1][0]:
                inf_color = self.vcolors[i]
                sup_color = self.vcolors[i+1]
                break
        r = (value-inf_color[0])/(sup_color[0]-inf_color[0])
        if not asQColor:
            return (sup_color[1][0]*r + inf_color[1][0]*(1-r), 
                    sup_color[1][1]*r + inf_color[1][1]*(1-r),
                    sup_color[1][2]*r + inf_color[1][2]*(1-r))
        
        from PyQt4.QtGui import QColor
        q = QColor()
        q.setRedF(sup_color[1][0]*r + inf_color[1][0]*(1-r))
        q.setGreen(sup_color[1][1]*r + inf_color[1][1]*(1-r))
        q.setBlueF(sup_color[1][2]*r + inf_color[1][2]*(1-r))
        q.setAlphaF(alpha)
        return q
    
    
    def getQColor(self, value):
        """
        DEPRECATED
        """
        if not len(self.vcolors):
            return (0.,0.,0.,self.alpha)
        elif len(self.vcolors) == 1:
            return self.vcolors[0][1]
        elif value < 0.0:
            return self.vcolors[0][1]
        elif value > 1.0:
            return self.vcolors[-1][1]
        sup_color = self.vcolors[0]
        inf_color = self.vcolors[-1]
        for i in xrange (len(self.vcolors)-1):
            if value < self.vcolors[i+1][0]:
                inf_color = self.vcolors[i]
                sup_color = self.vcolors[i+1]
                break
        r = (value-inf_color[0])/(sup_color[0]-inf_color[0])
        return (sup_color[1][0]*r + inf_color[1][0]*(1-r),
                sup_color[1][1]*r + inf_color[1][1]*(1-r),
                sup_color[1][2]*r + inf_color[1][2]*(1-r))
        



# Default colormaps
# ------------------------------------------------------------------------------
WithoutBlank = Colormap("WithoutBlank",
                      (0.00, (1.0, 0.0, 0.)),
                      (0.25, (0.5, 0.0, 0.5)),
                      (0.50, (0.0, 0.0, 1.0)),
                      (0.75, (0.0, 0.5, 0.5)),
                      (1.00, (0.0, 1.0, 0.0)))

GreenRed=Colormap("GreenRed",
                  (0.,(0.,1.,0.)),
                  (.5, (.5,.5,0.)),
                  (1.,(1.,0.,0.)))

IceAndFire = Colormap("IceAndFire",
                      (0.00, (0.0, 0.0, 1.0)),
                      (0.25, (0.0, 0.5, 1.0)),
                      (0.50, (1.0, 1.0, 1.0)),
                      (0.75, (1.0, 1.0, 0.0)),
                      (1.00, (1.0, 0.0, 0.0)))

IceAndFire2 = Colormap("IceAndFire",
                      (0.00, (0., 0.0, 1.0)),
                        (0.000001, (0., 0.5, 1.0)),
                        (0.000005, (1.0, 1.0, 1.0)),
                        (0.02, (1.0, 1., 0.0)),
                        (1.00, (1.0, 0.0, 0.0)))
Ice = Colormap("Ice",
               (0.00, (0.0, 0.0, 1.0)),
               (0.50, (0.5, 0.5, 1.0)),
               (1.00, (1.0, 1.0, 1.0)))
Fire = Colormap("Fire",
                (0.00, (1.0, 1.0, 1.0)),
                (0.50, (1.0, 1.0, 0.0)),
                (1.00, (1.0, 0.0, 0.0)))
Hot = Colormap("Hot",
               (0.00, (0.0, 0.0, 0.0)),
               (0.33, (1.0, 0.0, 0.0)),
               (0.66, (1.0, 1.0, 0.0)),
               (1.00, (1.0, 1.0, 1.0)))
               
Grey       = Colormap("Grey", (0., (0.,0.,0.)), (1., (1.,1.,1.)))
Grey_r     = Colormap("Grey_r", (0., (1.,1.,1.)), (1., (0.,0.,0.)))
DarkRed    = Colormap("DarkRed", (0., (0.,0.,0.)), (1., (1.,0.,0.)))
DarkGreen  = Colormap("DarkGreen",(0., (0.,0.,0.)), (1., (0.,1.,0.)))
DarkBlue   = Colormap("DarkBlue", (0., (0.,0.,0.)), (1., (0.,0.,1.)))
LightRed   = Colormap("LightRed", (0., (1.,1.,1.)), (1., (1.,0.,0.)))
LightGreen = Colormap("LightGreen", (0., (1.,1.,1.)), (1., (0.,1.,0.)))
LightBlue  = Colormap("LightBlue", (0., (1.,1.,1.)), (1., (0.,0.,1.))) 
