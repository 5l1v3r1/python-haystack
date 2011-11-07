#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

__author__ = "Loic Jaquemet loic.jaquemet+python@gmail.com"

import argparse
import logging
import os
import sys
from collections import defaultdict

from haystack import config
from haystack.reverse import utils


# extract graph 
def depthSubgraph(source, target, nodes, depth):
  if depth == 0:
    return
  depth-=1
  for node in nodes:
    neighbors = source.successors(node)
    target.add_edges_from( source.edges(node) )
    depthSubgraph(source, target, neighbors, depth)
  return 

def make(opts):
  fname = opts.gexf

import reversers
from reversers import *  # by the pickle of my thumb
context = reversers.getContext('../../outputs/skype.1.a')

import networkx
import matplotlib.pyplot as plt

digraph=networkx.readwrite.gexf.read_gexf(  '../../outputs/skype.1.a.gexf')

# clean solos
isolates = networkx.algorithms.isolate.isolates(digraph)
digraph.remove_nodes_from(isolates)

# clean solos clusters
graph = networkx.Graph(digraph) #undirected
subgraphs = networkx.algorithms.components.connected.connected_component_subgraphs(graph)
isolates1 = set( utils.flatten( g.nodes() for g in subgraphs if len(g) == 1) ) # self connected
isolates2 = set( utils.flatten( g.nodes() for g in subgraphs if len(g) == 2) ) 
isolates3 = set( utils.flatten( g.nodes() for g in subgraphs if len(g) == 3) ) 
digraph.remove_nodes_from(isolates1)
digraph.remove_nodes_from(isolates2)
digraph.remove_nodes_from(isolates3)

#
#graph = digraph.to_undirected()
#subgraphs = networkx.algorithms.components.connected.connected_component_subgraphs(graph)
subgraphs = [g for g in subgraphs if len(g)>3]
isolatedGraphs = subgraphs[1:100]


# group by nodes number
isoDict = defaultdict(list)
[isoDict[len(g)].append(g) for g in isolatedGraphs]

# test isomorphism
isoGraphs = dict()
for numNodes, graphs in isoDict.items():
  numgraphs = len(graphs)
  if numgraphs == 1:
    continue
  isoGraph = networkx.Graph()
  # quick find isomorphisms
  todo = set(graphs)
  for i,g1 in enumerate(graphs):
    for g2 in graphs[i+1:]:
      if networkx.is_isomorphic(g1, g2):
        print 'numNodes:%d graphs %d, %d are isomorphic'%(numNodes, i, i+1)
        isoGraph.add_edge(g1,g2, {'isomorphic':True})
        if g2 in todo:  todo.remove(g2) 
        if g1 in todo:  todo.remove(g1) 
        break # we can stop here, chain comparaison will work between g2 and g3
    
  if len(isoGraph) > 0:
    isoGraphs[numNodes] = isoGraph

# draw the isomorphisms
for i,item in enumerate(isoGraphs.items()):
  num,g = item
  #networkx.draw(g)
  for rg in g.nodes():
    networkx.draw(rg)
  fname = os.path.sep.join([config.Config.imgCacheDir, 'isomorph_subgraphs_%d.png'%(num) ] )
  plt.savefig(fname)
  plt.clf()
# need to use gephi-like for rendering nicely on the same pic


bigGraph = networkx.DiGraph()
bigGraph.add_edges_from( digraph.edges( subgraphs[0].nodes() ) )

stack_addrs = utils.int_array_cache( config.Config.getCacheFilename(config.Config.CACHE_STACK_VALUES, context.dumpname)) 
stack_addrs_txt = set(['%x'%(addr) for addr in stack_addrs]) # new, no long

stacknodes = list(set(bigGraph.nodes()) & stack_addrs_txt)
print 'stacknodes left',len(stacknodes)
orig = list(set(graph.nodes()) & stack_addrs_txt)
print 'stacknodes orig',len(orig)

# identify strongly referenced structures
degreesList = [ (bigGraph.in_degree(node),node)  for node in bigGraph.nodes() ]
degreesList.sort(reverse=True)

##### important struct
def printImportant(ind):
  import structure
  nb, saddr = degreesList[ind]
  addr = int(saddr,16)
  s1 = context.structures[addr]
  #s1 = s1._load() #structure.cacheLoad(context, int(saddr,16))
  s1.decodeFields()
  print s1.toString()
  # strip the node from its predecessors, they are numerously too numerous
  impDiGraph = networkx.DiGraph()
  root = '%d nodes'%(nb)
  impDiGraph.add_edge(root, saddr)
  depthSubgraph(bigGraph, impDiGraph, [saddr], 2 )
  print 'important struct with %d structs pointing to it, %d pointerFields'%(digraph.in_degree(saddr), digraph.out_degree(saddr))
  #print 'important struct with %d structs pointing to it, %d pointerFields'%(impDiGraph.in_degree(saddr), impDiGraph.out_degree(saddr))
  fname = os.path.sep.join([config.Config.imgCacheDir, 'important_%s.png'%(saddr) ] )
  networkx.draw(impDiGraph)
  plt.savefig(fname)
  plt.clf()
  # check for children with identical sig
  for node in impDiGraph.successors(saddr):
    st = context.structures[int(node,16)]
    st.decodeFields()
    st.resolvePointers(context.structures_addresses, context.structures)
    #st.pointerResolved=True
    st._aggregateFields()
    print node, st.getSignature(text=True)
  # clean and print
  s1._aggregateFields()
  impDiGraph.remove_node(root)
  save_graph_headers(context, impDiGraph, '%s.subdigraph.py'%(saddr) )
  return s1

printImportant(0) # la structure la plus utilisee.





#s1._aggregateFields()

#s2 = utils.nextStructure(context, s1)
#s2b should start with \x00's


def save_graph_headers(context, graph, fname):
  fout = file( os.path.sep.join([Config.cacheDir, fname])  ,'w')
  towrite = []
  structs = [context.structures[int(addr,16)] for addr in graph.nodes()]
  for anon in structs:
    anon.decodeFields()
    anon.resolvePointers(context.structures_addresses, context.structures)
    #anon.pointerResolved=True
    anon._aggregateFields()
    towrite.append(anon.toString())
    if len(towrite) >= 10000:
      try:
        fout.write('\n'.join(towrite) )
      except UnicodeDecodeError, e:
        print 'ERROR on ',anon
      towrite = []
      fout.flush()
  fout.write('\n'.join(towrite) )
  fout.close()
  return



def argparser():
  rootparser = argparse.ArgumentParser(prog='haystack-reversers-graph', description='Play with graph repr of pointers relationships.')
  rootparser.add_argument('--debug', action='store_true', help='Debug mode on.')
  rootparser.add_argument('gexf', type=argparse.FileType('rb'), action='store', help='Source gexf.')
  rootparser.set_defaults(func=make)  
  return rootparser

def main(argv):
  parser = argparser()
  opts = parser.parse_args(argv)

  level=logging.INFO
  if opts.debug :
    level=logging.DEBUG
  
  flog = os.path.sep.join([config.Config.cacheDir,'log'])
  logging.basicConfig(level=level, filename=flog, filemode='w')
  
  #logging.getLogger('haystack').setLevel(logging.INFO)
  #logging.getLogger('dumper').setLevel(logging.INFO)
  #logging.getLogger('structure').setLevel(logging.INFO)
  #logging.getLogger('field').setLevel(logging.INFO)
  #logging.getLogger('progressive').setLevel(logging.INFO)
  logging.getLogger('graph').addHandler(logging.StreamHandler(stream=sys.stdout))

  log.info('[+] output log to %s'% flog)

  opts.func(opts)


if __name__ == '__main__':
  main(sys.argv[1:])
