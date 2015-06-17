#!/usr/bin/env python

__author__ = "Gabriel Bassett"
"""
 AUTHOR: {0}
 DATE: <DATE>
 DEPENDENCIES: <a list of modules requiring installation>
 Copyright <YEAR> {0}

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
 <ENTER DESCRIPTION>

""".format(__author__)
# PRE-USER SETUP
pass

########### NOT USER EDITABLE ABOVE THIS POINT #################


# USER VARIABLES
NX_CONFIG_FILE = "networkx.yapsy-plugin"
NAME = "Networkx Interface"


########### NOT USER EDITABLE BELOW THIS POINT #################


## IMPORTS
from yapsy.IPlugin import IPlugin
import logging
import networkx as nx
from datetime import datetime # timedelta imported above
import uuid
import ConfigParser
import inspect
import os.path


## SETUP
loc = inspect.getfile(inspect.currentframe())
ind = loc.rfind("/")
loc = loc[:ind+1]
config = ConfigParser.SafeConfigParser()
config.readfp(open(loc + NX_CONFIG_FILE))

if config.has_section('Core'):
    if 'name' in config.options('Core'):
        NAME = config.get('Core', 'name')
if config.has_section('Log'):
    if 'level' in config.options('Log'):
        LOGLEVEL = config.get('Log', 'level')
    if 'file' in config.options('Log'):
        LOGFILE = config.get('Log', 'file')

## EXECUTION
class PluginOne(IPlugin):
    context_graph = nx.MultiDiGraph()
    context_graph_file = None

    #  TODO: The init should contain anything to load modules or data files that should be variables of the  plugin object
    def __init__(self):
        if 'context_graph_file' in config.options("Configuration"):
            self.context_graph_file = config.get('Configuration', 'context_graph_file')

    #  TODO: Configuration needs to set the values needed to identify the plugin in the plugin database as well as ensure everyhing loaded correctly
    #  TODO: Current  layout is for an enrichment plugin
    #  TODO: enrichment [type, successful_load, name, description, inputs to enrichment such as 'ip', cost, speed]
    #  TODO: interface [type, successful_load, name]
    #  TODO: query [TBD]
    #  TODO: minion [TBD]
    def configure(self):
        """

        :return: return list of [type, successful_load, name]
        """
        config_options = config.options("Configuration")

        if os.path.isfile(self.context_graph_file):
            try:
                self.context_graph = self.read_graph(graph_file) 
            except:
                pass

        if 'type' in config_options:
            plugin_type = config.get('Configuration', 'type')
        else:
            logging.error("'Type' not specified in config file.")
            return [None, False, NAME]

        return [plugin_type, True, NAME]


    #  TODO: The correct type of execution function must be defined for the type of plugin
    #  TODO: enrichment: "run(self, <thing to enrich>, start_time, any specific attributes.  MUST HAVE DEFAULTS)
    #  TODO: interface: enrich(self, graph)
    #  TODO: query [TBD]
    #  TODO: minion [TBD]
    #  TODO: Enrichment plugin specifics:
    #  -     Created nodes/edges must follow http://blog.infosecanalytics.com/2014/11/cyber-attack-graph-schema-cags-20.html
    #  -     The enrichment should include a node for the <thing to enrich>
    #  -     The enrichment should include a node for the enrichment which is is statically defined & key of "enrichment"
    #  -     An edge should exist from <thing to enrich> to the enrichment node, created at the end after enrichment
    #  -     Each enrichment datum should have a node
    #  -     An edge should exist from <thing to enrich> to each enrichment datum
    #  -     The run function should then return a networkx directed multi-graph including the nodes and edges
    #  TODO: Interface plugin specifics:
    #  -     In the most efficient way possible, merge nodes and edges into the storage medium
    #  -     Merger of nodes should be done based on matching key & value.
    #  -     URI should remain static for a given node.
    #  -     Start time should be updated to the sending graph
    #  -     Edges should be added w/o attempts to merge with edges in the storage back end
    #  -     When adding nodes it is highly recommended to keep a node-to-storage-id mapping with a key of the node
    #  -       URI.  This will assist in bulk-adding the edges.
    def enrich(self, g):  # Networkx
        """

        :param g: networkx graph to be merged
        :return: Nonetype

        Note: Neo4j operates differently from the current titan import.  The neo4j import does not aggregate edges which
               means they must be handled at query time.  The current titan algorithm aggregates edges based on time on
               merge.
        """
        for uri, data in g.nodes(data=True):
        # For each node:
            # Get node by URI
            # (should we double check the the class/key/value match?)
            # If it exists in the receiving graph, going to need to merge properties (replacing with newer)
            if uri in self.context_graph.nodes():
                self.context_graph.node[uri].update(data)
            else:
                self.context_graph.add_node(uri, attr_dict=data)
        # For each edge:
        for edge in g.edges(data=True):
            # Add it
            self.context_graph.add_edge(edge[0], edge[1], attr_dict=data)


    def get_graph(self):
        return self.context_graph


    def write_graph(self, G=None, subgraph_file=None):
        if G is None:
            G = self.context_graph
        if subgraph_file is None:
            subgraph_file = self.context_graph_file
        logging.info("Writing graph.")
        # write the graph out
        file_format = subgraph_file.split(".")[-1]
        if file_format == "graphml":
            nx.write_graphml(G, subgraph_file)
        elif file_format == "gml":
            nx.write_gml(G, subgraph_file)
        elif file_format == "gexf":
            nx.write_gexf(G, subgraph_file)
        elif file_format == "net":
            nx.write_pajek(G, subgraph_file)
        elif file_format == "yaml":
            nx.write_yaml(G, subgraph_file)
        elif file_format == "gpickle":
            nx.write_gpickle(G, subgraph_file)
        else:
            print "File format not found, writing graphml."
            nx.write_graphml(G, subgraph_file)

    def read_graph(self, subgraph_file=None):
        if subgraph_file is None:
            subraph_file = self.context_graph_file
        logging.info("Writing graph.")
        # write the graph out
        file_format = subgraph_file.split(".")[-1]
        if file_format == "graphml":
            return nx.read_graphml(subgraph_file)
        elif file_format == "gml":
            return nx.read_gml(subgraph_file)
        elif file_format == "gexf":
            return nx.read_gexf(subgraph_file)
        elif file_format == "net":
            return nx.read_pajek(subgraph_file)
        elif file_format == "yaml":
            return nx.read_yaml(subgraph_file)
        elif file_format == "gpickle":
            return nx.read_gpickle(subgraph_file)
        else:
            logging.warning("File format not found, returning empty graph.")
        return nx.MultiDiGraph()