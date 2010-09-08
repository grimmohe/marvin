#coding=utf8

import re
import glob
import os

"""
known template variables:
$untouched-sensor           # liste der sensoren, die keine berührung haben sollten
$base-sensor                # sensor mit bewusster berührung
$direction                  # left|right
$opposite-direction         # gegenteil von $direction
$compare                    # g|l|e wird für vergleiche benutzt
$target-angle               # zu erreichender winkel in grad
$distance                   # distanz die gefahren werden soll
$head-movement              # up|down bewegung der sensoren / des saugkopfes
$head-target                # 0|100 ist ziel der bewegung von $head-movement

If a varaible contains a comma seperated list, the tag in which it is used will be repeated for
each entry.
"""

TEMPLATE_DISCOVER = 1
TEMPLATE_DRIVE = 2
TEMPLATE_HEAD = 4
TEMPLATE_TURN_BLIND = 8
TEMPLATE_TURN_ANGLE = 16
TEMPLATE_TURN_HIT = 32

_templateList = []

def addTemplate(typ, baseSensor=None, untouchedSensor=None, direction=None, compare=None,
                targetAngle=None, distance=None, headMovement=None):
    pass

def clear():
    _templateList = []

def getTransmissionData():
    pass

def readTransmissiondata():
    pass

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
        self.varlist=TemplateKeyInformation("")
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
        return rc

    def fill(self):
        """ replaces all variables with its values """
        res=self.content
        for var in self.varlist.varlist:
            res=res.replace("$" + var.name, var.value)
        return res


class TemplateVariable:

    def __init__(self, varname, value=""):
        self.name = varname
        self.value = value

class TemplateKeyInformation:

    def __init__(self, typ):
        self.varlist = []
        self.typ = typ

    def lookup(self, varname):
        for var in self.varlist:
            if var.name == varname:
                return var
        return None

    def add(self, var):
        if not self.lookup(var.name):
            self.varlist.append(var)
