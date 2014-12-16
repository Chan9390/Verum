#!/usr/bin/env python
"""
 AUTHOR: Gabriel Bassett
 DATE: 12-17-2013
 DEPENDENCIES: a list of modules requiring installation
 Copyright 2014 Gabriel Bassett

 LICENSE:
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.

 DESCRIPTION:
 Functions necessary to enrich the context graph

"""
# PRE-USER SETUP
from datetime import timedelta

########### NOT USER EDITABLE ABOVE THIS POINT #################


# USER VARIABLES
CONFIG_FILE = "/tmp/verum.cfg"
# Below values will be overwritten if in the config file or specified at the command line
NEO4J_HOST = 'localhost'
NEO4J_PORT = '7474'



########### NOT USER EDITABLE BELOW THIS POINT #################


## IMPORTS
import argparse
import logging
from datetime import datetime # timedelta imported above
# todo: Import with IMP and don't import the titan graph functions if they don't import
try:
    from bulbs.titan import Graph as TITAN_Graph
    from bulbs.titan import Config as TITAN_Config
    from bulbs.model import Relationship as TITAN_Relationship
    titan_import = True
except:
    titan_import = False
try:
    from py2neo import Graph as py2neoGraph
    neo_import = True
except:
    neo_import = False
try:
    from yapsy.PluginManager import PluginManager
    plugin_import = True
except:
    plugin_import = False
import ConfigParser
import sqlite3
import networkx as nx
import os
print os.getcwd()

## SETUP
__author__ = "Gabriel Bassett"
# Read Config File - Will overwrite file User Variables Section
config = ConfigParser.SafeConfigParser()
config.readfp(open(CONFIG_FILE))
#TODO: Fix Config Parse
if config.has_section('TITANDB'):
    if 'host' in config.options('TITANDB'):
        TITAN_HOST = config.get('TITANDB', 'host')
    if 'port' in config.options('TITANDB'):
        TITAN_PORT = config.get('TITANDB', 'port')
    if 'graph' in config.options('TITANDB'):
        TITAN_GRAPH = config.get('TITANDB', 'graph')
if config.has_section('NEO4j'):
    if 'host' in config.options('NEO4J'):
        NEO4J_HOST = config.get('NEO4J', 'host')
    if 'port' in config.options('NEO4J'):
        NEO4J_PORT = config.get('NEO4J', 'port')
if config.has_section('Core'):
    if 'plugins' in config.options('Core'):
        PluginFolder = config.get('Core', 'plugins')

# Parse Arguments - Will overwrite Config File
# TODO: Remove Arg Parse
parser = argparse.ArgumentParser(description='This script processes a graph.')
parser.add_argument('-d', '--debug',
                    help='Print lots of debugging statements',
                    action="store_const", dest="loglevel", const=logging.DEBUG,
                    default=logging.WARNING
                   )
parser.add_argument('-v', '--verbose',
                    help='Be verbose',
                    action="store_const", dest="loglevel", const=logging.INFO
                   )
parser.add_argument('--log', help='Location of log file', default=None)
parser.add_argument('--plugins', help="Location of plugin directory", default=PluginFolder)
parser.add_argument('--titan_host', help="Host for titanDB database.", default=TITAN_HOST)
parser.add_argument('--titan_port', help="Port for titanDB database.", default=TITAN_PORT)
parser.add_argument('--titan_graph', help="Graph for titanDB database.", default=TITAN_GRAPH)
parser.add_argument('--neo4j_host', help="Host for Neo4j database.", default=NEO4J_HOST)
parser.add_argument('--neo4j_port', help="Port for Neo4j database.", default=NEO4J_PORT)

## Set up Logging
args = parser.parse_args()
if args.log is not None:
    logging.basicConfig(filename=args.log, level=args.loglevel)
else:
    logging.basicConfig(level=args.loglevel)
# <add other setup here>


## EXECUTION
if module_import_success:
    class PluginOne(IPlugin):
        neo4j_config = None

        def __init__(self):
            pass


        def configure(self):
            """

            :return: return list of [configure success (bool), name, description, list of acceptable inputs, resource cost (1-10, 1=low), speed (1-10, 1=fast)]
            """
            config_options = config.options("Configuration")

            ... TODO: Fill in configuration stuff here

            # TODO: Ensure neo4j libraries loaded correctly

            # Create titan config
            # TODO: Import host, port, graph from config file
            self.set_neo4j_config(args.neo4j_host, args.neo4j_port)

            # TODO: If config is successful, return


        def set_neo4j_config(self, host, port):
            self.neo4j_config = "http://{0}:{1}/db/data/".format(host, port)


        def removeNonAscii(self, s): return "".join(i for i in s if ord(i)<128)


        def run(self, g):  # Neo4j
            """

            :param g: networkx graph to be merged
            :param neo4j: bulbs neo4j config
            :return: Nonetype

            Note: Neo4j operates differently from the current titan import.  The neo4j import does not aggregate edges which
                   means they must be handled at query time.  The current titan algorithm aggregates edges based on time on
                   merge.
            """
            #neo4j_graph = NEO_Graph(neo4j)  # Bulbs
            neo_graph = py2neoGraph(self.neo4j_config)
            nodes = set()
            node_map = dict()
            edges = set()
            settled = set()
            # Merge all nodes first
            tx = neo_graph.cypher.begin()
            cypher = ("MERGE (node: {0} {1}) "
                      "ON CREATE SET node = {2} "
                      "RETURN collect(node) as nodes"
                     )
            # create transaction for all nodes
            for node, data in g.nodes(data=True):
                query = cypher.format(data['class'], "{key:{KEY}, value:{VALUE}}", "{MAP}")
                props = {"KEY": data['key'], "VALUE":data['value'], "MAP": data}
                # TODO: set "start_time" and "finish_time" to dummy variables in attr.
                # TODO:  Add nodes to graph, and cyper/gremlin query to compare to node start_time & end_time to dummy
                # TODO:  variable update if node start > dummy start & node finish < dummy finish, and delete dummy
                # TODO:  variables.
                tx.append(query, props)
            # commit transaction and create mapping of returned nodes to URIs for edge creation
            for record_list in tx.commit():
                for record in record_list:
        #            print record, record.nodes[0]._Node__id, len(record.nodes)
                    for n in record.nodes:
        #                print n._Node__id
                        attr = n.properties
                        uri = "class={0}&key={1}&value={2}".format(attr['class'], attr['key'], attr['value'])
                        node_map[uri] = int(n.ref.split("/")[1])
        #                node_map[uri] = n._Node__id
        #    print node_map  # DEBUG

            # Create edges
            cypher = ("MATCH (src: {0}), (dst: {1}) "
                      "WHERE id(src) = {2} AND id(dst) = {3} "
                      "CREATE (src)-[rel: {4} {5}]->(dst) "
                     )
            tx = neo_graph.cypher.begin()
            for edge in g.edges(data=True):
                try:
                    relationship = edge[2].pop('relationship')
                except:
                    # default to 'described_by'
                    relationship = 'describedBy'

                query = cypher.format(g.node[edge[0]]['class'],
                                      g.node[edge[1]]['class'],
                                     "{SRC_ID}",
                                     "{DST_ID}",
                                      relationship,
                                      "{MAP}"
                                     )
                props = {
                    "SRC_ID": node_map[edge[0]],
                    "DST_ID": node_map[edge[1]],
                    "MAP": edge[2]
                }

                # create the edge
                # NOTE: No attempt is made to deduplicate edges between the graph to be merged and the destination graph.
                #        The query scripts should handle this.
        #        print edge, query, props  # DEBUG
                tx.append(query, props)
        #        rel = py2neoRelationship(node_map[src_uri], relationship, node_map[dst_uri])
        #        rel.properties.update(edge[2])
        #        neo_graph.create(rel)  # Debug
        #        edges.add(rel)

            # create edges all at once
            #print edges  # Debug
        #    neo_graph.create(*edges)
            tx.commit()



