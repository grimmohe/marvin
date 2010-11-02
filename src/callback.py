#!/usr/bin/env python
#coding=utf8

class Callback:
    
    def __init__(self):
        self.cblist=[]
        
    def call(self, attributes=None):
        for call in self.cblist:
            call.call(attributes)

    def add(self, callbackCall):
        self.cblist.append(callbackCall)
            
class CallbackCall:
    
    def __init__(self, method, attributes=None):
        self.method = method
        self.attributes = attributes
        
    def call(self, contextAttributes):
        
        if contextAttributes: 
            if self.attributes:
                contextAttributes.update(self.attributes)
        else: 
           contextAttributes = self.attributes
           
        self.method(contextAttributes)
    
class CallAttributes:
    
    def __init__(self, attriblist=None):
        if attriblist:
            self.attriblist = attriblist
        else:
            self.attriblist = {}

class CallbackList:
    
    def __init__(self, callbackNames=None):
        self.list = {}
        if callbackNames:
            self.add(callbackNames)
    
    def __getitem__(self, name):
        if self.list.has_key(name):
            if not self.list[name]:
                self.list[name] = Callback()
            return self.list[name]
        raise Exception("no callback with name: " + name)
    
    def call(self, name, attributes):
        if self.list[name]:
            self.list[name].call(attributes)
            
    def add(self, callbackNames):
        for callbackName in callbackNames: 
            self.list.update({callbackName: None})        
