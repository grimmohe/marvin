#!/usr/bin/env python
#coding=utf8

class logger:

    def log(self, text):
        print text


class loggerTextBuffer(logger):

    def __init__(self, buffer):
        self.buffer = buffer

    def log(self,text):
        self.buffer.insert_at_cursor(text+"\n")


