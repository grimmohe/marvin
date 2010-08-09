
import re
import glob
import os

class TemplateList:
    
    def __init__(self):
        self.basepath='../templates/*'
        self.templates=[]
        self.load()
        
    def load(self):
        res = glob.glob(self.basepath)
        for file in res:
            print file
            self.templates.append(Template(file))
            
    def lookup(self, xmlfilename):
        for tmplt in self.templates:
            if os.path.basename(tmplt.filepath) == xmlfilename:
                return tmplt
        return None
        
class Template:
    
    def __init__(self,path):
        self.filepath=path
        self.varlist=None
        self.content=''
        self.load()
        
    def load(self):
        """ loads the template an read available variables """
        self.varlist=TemplateVariableList()
        ofile = os.open(self.filepath, os.O_RDONLY)
        rc=1
        stream = ""
        while True:
            fread = os.read(ofile, 2048)
            stream += fread
            if len(fread) > 0:
                rc = 0
            else:
                break
        os.close(ofile)
        self.content=stream
        res = re.findall("[\$][a-zA-Z\-]*", stream)
        for var in res:
            self.varlist.add(TemplateVariable(var))
                
    def fill(self):
        """ replaces all variables with its values """
        res=self.content
        for var in self.varlist.varlist:
            res=res.replace(var.name, var.value)
        return res
            

class TemplateVariable:
    
    def __init__(self,varname):
        self.name=varname
        self.value=''
        
class TemplateVariableList:

    def __init__(self):
        self.varlist=[]
        
    def lookup(self,name):
        for var in self.varlist:
            if var.name == name:
                return var
        return None
     
    def add(self,item):
        if not self.lookup(item.name):
            self.varlist.append(item)

    