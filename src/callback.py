#!/usr/bin/env python
#coding=utf8

class Callback:
    
    def __init__(self, callback=None):
        self.cblist=[]
        if callback:
            self.add(callback)
        
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

    def getValue(self, name):
        return self.attriblist[name]
    
class CallbackList:
    
    def __init__(self, callbacks):
        if callbacks:
            self.list = callbacks
        else:
            self.list = {}
            
    def lookup(self, name):
        if self.list.has_key(name):
            return self.list[name]
        raise Exception("no callback with name: " + name)
    
    def __getitem__(self, name):
        return self.lookup(name)
    
    def call(self, name, attributes):
        if self.lookup(name):
            self.list[name].call(attributes)
     