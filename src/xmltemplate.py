#coding=utf8

import re
import glob
import os
import xml.sax

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
TEMPLATE_TURN_ANGLE = 8
TEMPLATE_TURN_HIT = 16

HEAD_UP = 0
HEAD_DOWN = 100

DIRECTION_LEFT = 0
DIRECTION_RIGHT = 1
DIRECTION_KEYS = (DIRECTION_LEFT, DIRECTION_RIGHT)
DIRECTIONS = ("left", "right")

_templateList = []

def addTemplate(type, baseSensor=None, untouchedSensor=None, direction=None, compare=None,
                targetAngle=None, distance=None, headMovement=None):
    """ used as callback method to add an assignment, still in form of template type and the required variables """
    global _templateList
    tki = TemplateKeyInformation(type)

    if type in (TEMPLATE_DISCOVER, TEMPLATE_TURN_HIT):
        if not (baseSensor <> None and untouchedSensor <> None and direction in DIRECTION_KEYS):
            raise Exception("there are parameters missing")

        tki.add(TemplateVariable("direction", direction))
        if direction == DIRECTION_LEFT:
            tki.add(TemplateVariable("opposite-direction", DIRECTION_RIGHT))
        else:
            tki.add(TemplateVariable("opposite-direction", DIRECTION_LEFT))

        # one entry for every device name
        for dev in baseSensor:
            tki.add(TemplateVariable("base-sensor", dev))
        for dev in untouchedSensor:
            tki.add(TemplateVariable("untouched-sensor", dev))

    elif type == TEMPLATE_DRIVE:
        if not untouchedSensor <> None:
            raise Exception("there are parameters missing")

        if distance:
            tki.add(TemplateVariable("distance", distance))

        for dev in untouchedSensor:
            tki.add(TemplateVariable("untouched-sensor", dev))

    elif type == TEMPLATE_HEAD:
        if not headMovement in (HEAD_DOWN, HEAD_UP):
            raise Exception("there are parameters missing")

        tki.add(TemplateVariable("head-target", headMovement))
        if headMovement == HEAD_DOWN:
            tki.add(TemplateVariable("head-movement", "down"))
        else:
            tki.add(TemplateVariable("head-movement", "up"))

    elif type == TEMPLATE_TURN_ANGLE:
        if not (targetAngle and direction in DIRECTION_KEYS):
            raise Exception("there are parameters missing")

        tki.add(TemplateVariable("direction", direction))
        tki.add(TemplateVariable("target-angle", targetAngle))

    else:
        raise Exception("unknown template type")

    _templateList.append(tki)


def clear():
    global _templateList
    _templateList = []

def getTransmissionData():
    data = ""
    global _templateList
    for tki in _templateList:
        data += tki.toXml()
    return data

def readTransmissionData(data):
    xml.sax.parseString(data, TransmissiondataXmlHandler())

def processTemplates(xmlHandler):
    global _templateList
    for tki in _templateList:
        data = getTemplateData(tki.type)
        xmlHandler.getVar = tki.lookup
        xml.sax.parseString(data, xmlHandler)

def getTemplateData(type):
    """ loads the template file to return as string """
    filename = "templates"
    if type == TEMPLATE_DISCOVER:
        filename += "/discover.xml"
    elif type == TEMPLATE_DRIVE:
        filename += "/drive.xml"
    elif type == TEMPLATE_HEAD:
        filename += "/head.xml"
    elif type == TEMPLATE_TURN_ANGLE:
        filename += "/turn-angle.xml"
    elif type == TEMPLATE_TURN_HIT:
        filename += "/turn-hit.xml"
    else:
        raise Exception("unknown template type")

    try:
        input = open(filename, "r")
        data = input.read()
    finally:
        input.close()

    return data

class TransmissiondataXmlHandler(xml.sax.ContentHandler):
    """
    Handles XML.SAX events to create ActionlogEntry
    """

    def __init__(self):
        self.tki = None

    def startElement(self,name,attrs):
        global _templateList
            
        if name == "tki":
            type = None
            for attr,val in attrs.items():
                if attr == "type":
                    try:
                        type = int(val)
                    except ValueError:
                        continue
            if type:
                self.tki = TemplateKeyInformation(type)
                _templateList.append(self.tki)
        elif name == "tv":
            n = None
            v = None
            for attr,val in attrs.items():
                if attr == "n":
                    n = val
                elif attr == "v":
                    v = val
            if self.tki:
                self.tki.varlist.append(TemplateVariable(n, v))
        return 0

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

    def __init__(self, varname="", value=""):
        self.name = varname
        self.value = value

    def toXml(self):
        return '<tv n="' + self.name + '" v="' + str(self.value) + '"/>'

class TemplateKeyInformation:

    def __init__(self, type):
        self.varlist = []
        self.type = type

    def add(self, var):
        if not self.lookup(var.name):
            self.varlist.append(var)

    def lookup(self, varname):
        ret = ""
        for var in self.varlist:
            if var.name == varname:
                ret += "," + var.value
        return ret.lstrip(",")

    def toXml(self):
        data = '<tki type="' + str(self.type) + '">'
        for var in self.varlist:
            data += var.toXml()
        data += "</tki>"
        return data
