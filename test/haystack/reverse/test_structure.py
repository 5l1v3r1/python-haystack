#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for haystack.reverse.structure."""

import logging
import struct
import operator
import os
import unittest
import pickle
import sys

from haystack.config import Config
from haystack.reverse import structure
from haystack.reverse import reversers

__author__ = "Loic Jaquemet"
__copyright__ = "Copyright (C) 2012 Loic Jaquemet"
__license__ = "GPL"
__maintainer__ = "Loic Jaquemet"
__email__ = "loic.jaquemet+python@gmail.com"
__status__ = "Production"

sys.path.append('test/src/')
import ctypes3

import ctypes 

class TestStructure(unittest.TestCase):

  @classmethod
  def setUpClass(self):
    context = reversers.getContext('test/src/test-ctypes3.dump')
    context.reset()      

  def setUp(self):  
    self.context = reversers.getContext('test/src/test-ctypes3.dump')

  def test_init(self):
    for s in self.context.listStructures():
      if len(s) == 12 : #Node + padding, 1 pointer on create
        self.assertEqual( len(s.getFields()), len(s.getPointerFields()))
      elif len(s) == 20 : #test3, 1 pointer on create
        self.assertEqual( len(s.getFields()), len(s.getPointerFields()))
    return  

  def test_decodeFields(self):
    for s in self.context.listStructures():
      s.decodeFields()
      if len(s) == 12 : #Node + padding, 1 pointer on create
        self.assertEqual( len(s.getFields()), 3 ) # 1, 2 and padding
        self.assertEqual( len(s.getPointerFields()), 1)
      elif len(s) == 20 : #test3, 1 pointer on create
        # fields, no heuristic to detect medium sized int
        # TODO untyped of size < 8 == int * x
        self.assertEqual( len(s.getFields()), 3 )
        self.assertEqual( len(s.getPointerFields()), 1)
    return  

  def test_resolvePointers(self):
    for s in self.context.listStructures():
      s.resolvePointers()
    self.assertTrue(True) # test no error

  def test_resolvePointers2(self):
    for s in self.context.listStructures():
      s.decodeFields()
      s.resolvePointers()
      if len(s) == 12 : #Node + padding, 1 pointer on create
        self.assertEqual( len(s.getFields()), 3 ) # 1, 2 and padding
        self.assertEqual( len(s.getPointerFields()), 1)
  

  '''
  def test_guessField(self):
    self.assertEqual( None, None)
    return  

  def test_aggregateZeroes(self):
    return  
    
  def test_fixGaps(self):
    return  
  
  def test_fixOverlaps(self):
    return  
  
  def test_getOverlapping(self):
    return  
  
  def test_resolvePointers(self):
    return  
  
  def test_resolvePointerToStructField(self):
    return  
  '''
  def test_aggregateFields(self):
    return  



if __name__ == '__main__':
  unittest.main(verbosity=0)
  #suite = unittest.TestLoader().loadTestsFromTestCase(TestFunctions)
  #unittest.TextTestRunner(verbosity=2).run(suite)
