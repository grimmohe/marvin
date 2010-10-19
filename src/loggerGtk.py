#!/usr/bin/env python
#coding=utf8

import logger
import pygtk
pygtk.require('2.0')
import gtk.gdk as gdk

class logger(logger.logger):

    def __init__(self, buffer):
        self.buffer = buffer

    def log(self,text):
        gdk.threads_enter()
        self.buffer.insert_at_cursor(text+"\n")
        gdk.threads_leave()
        print text
