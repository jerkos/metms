#usr/bin/python

from core import MetObjects as obj
from core import MetDataObjects as obj
from controller.MetBaseControl import MSModel
import os.path as p
import re

class MSBioCycParser(MSModel):
        """
        Parser flat file biocyc
        """
        
        def __init__ (self, biocyc_file):
            MSModel.__init__(self, biocyc_file)
            self.data =[]
            
        def parsing(self):
            """Parsing Function"""
            with open(self.model) as f:
                line =f.readline()
                while  line != "":
                    transformed_line = line.split('\t')
                    d= {'MASS':transformed_line[4], 
                            'FORMULA':transformed_line[3], 
                            'NAME':transformed_line[2],
                            'KEGG':transformed_line[1],  
                            'BIOCYC':transformed_line[0]}
                    line =f.readline()
                    self.data.append(d)
        def idata(self):
            for e in self.data:
                yield e




class MSKeggParser(MSModel):

    # only looking for for wanted formula, to much RAM if we take all
    
    def __init__(self, kegg_file):
        MSModel.__init__(self, kegg_file)
        self.data=[]
        
    def parsing (self):
        #lst =[]
        entry = re.compile ('ENTRY\s+(C\d+).+\n')
        mass = re.compile('MASS\s+(\d+\.\d+)\n')
        corrupted = False
        with open(self.model) as f:
            line =f.readline()
            #continue until EOF
            while line != "" :
                corrupted =False
                if entry.match(line):
                    dico ={}
                    dico["ENTRY"] = entry.match(line).group(1)
                    lines =[];
                    while mass.match(line) is None and not corrupted:
                        line =f.readline()
                        #corrupted don't find mass before a new ENTRY
                        if line.split(" ")[0] == "ENTRY":
                            corrupted =True
                        lines.append(line)
                    #exclude corruption
                    if not corrupted:
                            #line
                        dico["MASS"] = mass.match(line).group(1)
                        for l in lines:
                            if l.split(" ")[0] == "NAME":
                                dico["NAME"] = l.split(" ")[8]
                                #try to get all the name
                                if len(l) > 8:
                                    for i in xrange (8, len(l)):
                                        dico["NAME"] += l[i]
                                
                            elif l.split(" ")[0] == "FORMULA":
                                dico["FORMULA"] = l.split(" ")[5].split("\n")[0]
                        self.data.append(dico)
                        #yield dico
                                #if l.split(" ")[5].split("\n")[0] == formula:
                                #    return dico
                            #condition to break
                    else:
                        del dico
                line =f.readline()
            #return lst
                
    
    def fast_parsing (self, formula):
        form = re.compile ('FORMULA\s+(.+)\n')
        with open(self.data) as f:
            line =f.readline()
            while line is not False:
                if form.match(line):
                    if form.match(line).group(1) == formula:
                        return True
                line =f.readline()
            return False
        
    def _genData(self):
        for e in self.data:
            yield e

class MSMetjpParser(MSModel):
    
    def __init__(self, config_file):
       MSModel.__init__(self, config_file)
       self.data=[]
    
    def parsing(self):
        with open(self.model) as f:
            l =f.readline()
            while l != "" :
                sl =l.split('\t')
                dico ={"MASS":sl[0],
                       "FORMULA":sl[1],
                       "NAME":sl[2]}
                self.data.append(dico)
                l =f.readline()
    def idata(self):
        for e in self.data:
            yield e