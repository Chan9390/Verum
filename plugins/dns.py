#!/usr/bin/env python
"""
 AUTHOR: Gabriel Bassett
 DATE: 11-22-2014
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
pass

########### NOT USER EDITABLE ABOVE THIS POINT #################


# USER VARIABLES
DNS_CONFIG_FILE = "dns.yapsy-plugin"
NAME = "DNS Enrichment"


########### NOT USER EDITABLE BELOW THIS POINT #################

## IMPORTS
from yapsy.IPlugin import IPlugin
import networkx as nx
from datetime import datetime
import dateutil  # to parse variable time strings
import socket
import uuid
import ConfigParser
import logging
import inspect
try:
    import dns.resolver
    resolver_import = True
except:
    resolver_import = False

## SETUP
__author__ = "Gabriel Bassett"
loc = inspect.getfile(inspect.currentframe())
ind = loc.rfind("/")
loc = loc[:ind+1]
config = ConfigParser.SafeConfigParser()
config.readfp(open(loc + DNS_CONFIG_FILE))

if config.has_section('Core'):
    if 'name' in config.options('Core'):
        NAME = config.get('Core', 'name')

## EXECUTION
class PluginOne(IPlugin):
    def __init__(self):
        pass

    def configure(self):
        """

        :return: return list of [configure success (bool), name, description, list of acceptable inputs, resource cost (1-10, 1=low), speed (1-10, 1=fast)]
        """
        config_options = config.options("Configuration")

        if 'cost' in config_options:
            cost = config.get('Configuration', 'cost')
        else:
            cost = 9999
        if 'speed' in config_options:
            speed = config.get('Configuration', 'speed')
        else:
            speed = 9999

        if 'type' in config_options:
            plugin_type = config.get('Configuration', 'type')
        else:
            logging.error("'Type' not specified in config file.")
            return [None, False, NAME, "Takes an IP string and returns the DNS resolved IP address as networkx graph.", None, cost, speed]

        if 'inputs' in config_options:
            inputs = config.get('Configuration', 'Inputs')
            inputs = [l.strip().lower() for l in inputs.split(",")]
        else:
            logging.error("No input types specified in config file.")
            return [plugin_type, False, NAME, "Takes an IP string and returns the DNS resolved IP address as networkx graph.", None, cost, speed]

        return [plugin_type, True, NAME, "Takes an IP string and returns the DNS resolved IP address as networkx graph.", inputs, cost, speed]


    def run(self, domain, start_time=""):
        """ str, str -> networkx multiDiGraph

        :param domain: a string containing a domain to lookup up
        :param start_time: string in ISO 8601 combined date and time format (e.g. 2014-11-01T10:34Z) or datetime object.
        :return: a networkx graph representing the response.
        """

        # Parse the start_time
        if type(start_time) is str:
            try:
                time = dateutil.parser.parse(start_time).strftime("%Y-%m-%dT%H:%M:%SZ")
            except:
                time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        elif type(start_time) is datetime:
            time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        g = nx.MultiDiGraph()

        # Get or create Domain node
        domain_uri = "class=attribute&key={0}&value={1}".format("domain", domain)
        g.add_node(domain_uri, {
            'class': 'attribute',
            'key': "domain",
            "value": domain,
            "start_time": time,
            "uri": domain_uri
        })

        # Try the DNS lookup and just return the domain if the lookup fails
        try:
            ip = socket.gethostbyname(domain)
        except socket.gaierror:
            return g

        # Get or create Enrichment node
        dns_uri = "class=attribute&key={0}&value={1}".format("enrichment", "dns")
        g.add_node(dns_uri, {
            'class': 'attribute',
            'key': "enrichment",
            "value": "dns",
            "start_time": time,
            "uri": dns_uri
        })

        ip_uri = "class=attribute&key={0}&value={1}".format("ip", ip)
        g.add_node(ip_uri, {
            'class': 'attribute',
            'key': "ip",
            "value": ip,
            "start_time": time,
            "uri": ip_uri
        })

        # Create edge from domain to ip node
        edge_attr = {
            "relationship": "describedBy",
            "start_time": time,
            "origin": "dns"
        }
        source_hash = uuid.uuid3(uuid.NAMESPACE_URL, domain_uri)
        dest_hash = uuid.uuid3(uuid.NAMESPACE_URL, ip_uri)
        edge_uri = "source={0}&destionation={1}".format(str(source_hash), str(dest_hash))
        rel_chain = "relationship"
        while rel_chain in edge_attr:
            edge_uri = edge_uri + "&{0}={1}".format(rel_chain,edge_attr[rel_chain])
            rel_chain = edge_attr[rel_chain]
        if "origin" in edge_attr:
            edge_uri += "&{0}={1}".format("origin", edge_attr["origin"])
        edge_attr["uri"] = edge_uri
        g.add_edge(domain_uri, ip_uri, edge_uri, {"start_time": time})

        # Link domain to enrichment
        edge_attr = {
            "relationship": "describedBy",
            "start_time": time,
            "origin": "dns"
        }
        source_hash = uuid.uuid3(uuid.NAMESPACE_URL, domain_uri)
        dest_hash = uuid.uuid3(uuid.NAMESPACE_URL, dns_uri)
        edge_uri = "source={0}&destionation={1}".format(str(source_hash), str(dest_hash))
        rel_chain = "relationship"
        while rel_chain in edge_attr:
            edge_uri = edge_uri + "&{0}={1}".format(rel_chain,edge_attr[rel_chain])
            rel_chain = edge_attr[rel_chain]
        if "origin" in edge_attr:
            edge_uri += "&{0}={1}".format("origin", edge_attr["origin"])
        edge_attr["uri"] = edge_uri
        g.add_edge(domain_uri, dns_uri, edge_uri, edge_attr)


        if resolver_import:
            # Get nameservers.  (note, this can get cached ones, but the more complex answer at http://stackoverflow.com/questions/4066614/how-can-i-find-the-authoritative-dns-server-for-a-domain-using-dnspython didn't work.)
            # If resolution fails, simply return the graph as is
            try:
                answers = dns.resolver.query(domain, 'NS')
            except dns.resolver.NoAnswer:
                return g

            for ns in answers:
                ns = ns.to_text().rstrip(".")

                # Create the nameserver node
                ns_uri = "class=attribute&key={0}&value={1}".format("domain", ns)
                g.add_node(ns_uri, {
                    'class': 'attribute',
                    'key': "domain",
                    "value": ns,
                    "start_time": time,
                    "uri": ns_uri
                })

                # Link it to the domain
                edge_attr = {
                    "relationship": "describedBy",
                    "start_time": time,
                    "origin": "dns",
                    "describedBy": "nameserver" 
                }
                source_hash = uuid.uuid3(uuid.NAMESPACE_URL, domain_uri)
                dest_hash = uuid.uuid3(uuid.NAMESPACE_URL, ns_uri)
                edge_uri = "source={0}&destionation={1}".format(str(source_hash), str(dest_hash))
                rel_chain = "relationship"
                while rel_chain in edge_attr:
                    edge_uri = edge_uri + "&{0}={1}".format(rel_chain,edge_attr[rel_chain])
                    rel_chain = edge_attr[rel_chain]
                if "origin" in edge_attr:
                    edge_uri += "&{0}={1}".format("origin", edge_attr["origin"])
                edge_attr["uri"] = edge_uri
                g.add_edge(domain_uri, ns_uri, edge_uri, edge_attr)

        return g
