'''
Copyright (C) 2011 by
Nicola Bonzanni (n.bonzanni@vu.nl)
Distributed with BSD license.     
All rights reserved, see LICENSE for details.
'''

from random import choice
from itertools import repeat, ifilter, islice
from xml.etree.ElementTree import ElementTree

from networkx import DiGraph

__author__ = "Nicola Bonzanni (n.bonzanni@vu.nl)"
__copyright__ = "Copyright 2011, Nicola Bonzanni"

__license__ = "BSD"
__version__ = "0.1"
__maintainer__ = "Nicola Bonzanni"
__email__ = "n.bonzanni@vu.nl"

class EnableError(Exception): 
    pass

class PetriNet(DiGraph):
    '''
    classdocs
    '''
    def __init__(self, capacity=6, filename=None, fileformat=None):
        super(PetriNet, self).__init__(self)
        if capacity < 1: raise ValueError, "place capacity must be at least 1"
        self.capacity = capacity
        # Store the initial marking in the graph attributes,
        # it can be use later on to start the simulations
        if filename:
            # If a NDR file has been specified, load the Petri net from that file
            if fileformat is 'ndr': self.graph['marking'] = self.from_ndr(filename)
            # If a spstochpn file has been specified, load the Petri net from that file
            elif fileformat is 'spn': self.graph['marking'] = self.from_spstochpn(filename)
            else: raise ValueError, "invalid Petri net file format"
        
    def add_transition(self, n, attr_dict=None, **attr):
        super(PetriNet, self).add_node(n, attr_dict, transition=True, **attr)
        
    def add_place(self, n, attr_dict=None, **attr):
        super(PetriNet, self).add_node(n, attr_dict, place=True, **attr)
        
    def is_transition(self, n):
        try: return self.node[n]['transition'] == True
        except KeyError: return False
    
    def transitions_iter(self, data=False):
        if data: return ifilter(lambda n: self.is_transition(n[0]), self.node.iteritems())
        return ifilter(self.is_transition, iter(self.adj))
    
    def transitions(self, data=False):
        return list(self.transitions_iter(data=data))
    
    def is_place(self, n):
        try: return self.node[n]['place'] == True
        except KeyError: return False
    
    def places_iter(self, data=False):
        if data: return ifilter(lambda n: self.is_place(n[0]), self.node.iteritems())
        return ifilter(self.is_place, iter(self.adj))
    
    def places(self, data=False):
        return list(self.places_iter(data=data))
    
    def check_preconditions(self, n, marking):
        for place in self.predecessors_iter(n):
            if marking[place] < self.get_edge_data(place, n).get('weight', 1): return False
        return True
    
    def check_postconditions(self, n, marking):
        for place in self.successors_iter(n):
            if marking[place] >= self.capacity: return False
        return True 
    
    def is_enabled(self, n, marking):
        return self.check_preconditions(n, marking) and self.check_postconditions(n, marking)
    
    def enabled_iter(self, marking):
        return iter(ifilter(lambda n: self.is_enabled(n, marking), self.transitions_iter()))
    
    def enabled(self, marking):
        return list(self.enabled_iter(marking))

    def marking(self, default=0):
        return {k : default for k in self.places_iter()}

    def consume_tokens(self, n, marking):
        for place in self.predecessors_iter(n):
            marking[place] = marking[place] - self.get_edge_data(place, n).get('weight', 1)
        return marking
            
    def produce_tokens(self, n, marking):
        for place in self.successors_iter(n):
            marking[place] = marking[place] + self.get_edge_data(n, place).get('weight', 1)
        return marking

    def fire_transition(self, n, marking):
        current = marking.copy()
        self.consume_tokens(n, current)
        self.produce_tokens(n, current)
        return current
    
    def fire_step(self, marking):
        firing_sequence = []
        current = marking.copy()
        # Prepare copies of the current marking to use as delta markings
        consume_delta = marking.copy();
        produce_delta = marking.copy();
        # Get the list of enabled transitions in the current marking
        enabled = self.enabled(marking)
        # If no transitions are enabled return None
        if not enabled: return None, None
        # Add duplicate transitions to account for strength
        enabled = [x for e in enabled for x in repeat(e, self.node[e].get('strength', 1))]
        # Loop until all initially enabled transitions are no more enabled
        while(enabled):
            # Choose a random transition for the list
            n = choice(enabled)
            # Check if the preconditions and postconditions are met on the
            # respective delta markings
            if self.check_preconditions(n, consume_delta) and \
                self.check_postconditions(n, produce_delta):
                firing_sequence.append(n)
                # Consume and produce the tokens on the respective delta
                # markings
                self.consume_tokens(n, consume_delta)
                self.produce_tokens(n, produce_delta)
            else:
                # If the transitions is no more enabled remove it from the list
                enabled.remove(n)
        # Update the current marking using the delta markings
        for k, v in marking.iteritems():
            current[k] = v + (consume_delta[k] - v) + (produce_delta[k] - v)
        # Return also the firing sequence used to generate the current marking
        return current, firing_sequence
    
    def step_iter(self, marking):
        current = None
        # If the marking is the initial marking just return it with an empty firing sequence
        if not current:
            current = marking
            yield current, []
        while(True):
            current, sequence = self.fire_step(current)
            if not current:
                return
            yield current, sequence
    
    def simulate(self, stop, times=1, marking=None):
        '''
        Tables format:
        -- run number --->
        [      0,                                                     1,          ..., times-1]
               |                                                      |            |     |
           -----------------------------------------------------     ----- ...    ...   ...
           |                           |                       |     |
         placeX=[m0,m1,...,m_stop-1] placeY=[m0,...,m_stop-1] ...   placeX=[...]
                 -- step number --->
                 
        e.g. tables[5][placeK][10] = the marking of placeK at the 11th step of the 6th simulation run
        n.b. tables[n][plateK][0] contains always the initial marking of placeK, and it is always the
             same for all n runs.
                 
        Firings format:
        -- run number --->
        [       0,                                      1,    ..., times-1]
                |                                       |      |      |
                |  -- step number --->                  |      |      |
         [      0,   1,  ...,                stop-1], [...], [...], [...]
                |    |    |                    |
              [[], ..., ..., [transitionZ, transitionW, ...]]
        
        e.g. firings[0][1] = the firing that generated the marking at the second step in the first run
        n.b. the first firing sequence of each run is empty because the first marking is the initial
             marking and the firing sequence that generated the first marking is unknown
        '''
        tables = []
        firings = []
        if not marking: marking = self.graph['marking']
        # Performs 'times' simulations
        for _ in repeat(None, times):
            table = {k: [] for k,_ in marking.iteritems()}
            firing = []
            # Simulate the network for 'stop' number of steps
            for m,s in islice(self.step_iter(marking), stop):
                # Append the current marking of each place to their
                # list of values in the table
                for k in m: table[k].append(m[k])
                # Append the current firing sequence at the list
                # of firing sequences for this run
                firing.append(s)
            # Append this run results to the tables of runs
            firings.append(firing)
            tables.append(table)
        return tables, firings
    
    # TODO: must be done properly
    def from_ndr(self, filename):
        marking = {}
        with open(filename, 'r') as f:
            for line in f:
                cols = line.split()
                if not cols: continue
                if cols[0] == 'p':
                    self.add_place(cols[3], x=float(cols[1]), y=float(cols[2]))
                    marking[cols[3]] = int(cols[4])
                elif cols[0] == 't':
                    try:
                        strength = int(cols[5])
                    except ValueError:
                        strength = 1
                    if strength < 1: strength = 1
                    self.add_transition(cols[3], x=float(cols[1]), y=float(cols[2]), strength=strength)
                elif cols[0] == 'e':
                    self.add_edge(cols[1], cols[2], weight=int(cols[3]))
        return marking
    
    def from_spstochpn(self, filename):
        marking = {}
        xmlid_to_graphid = {}
        tree = ElementTree(file=filename)
        
        for node in tree.iterfind(".//nodeclass[@name='Place']/node"):
            # We use Name as id for our graph. This could be a problem
            # because names can be duplicate in spstochpn files
            place = node.find("attribute[@name='Name']").text.strip()
            xmlid_to_graphid[node.get('id')] = place
            self.add_place(place,
                           x = float(node.find("graphics/graphic").get('x').strip()),
                           y = float(node.find("graphics/graphic").get('y').strip()))
            marking[place] = int(node.find("attribute[@name='Marking']").text.strip())
            
        for node in tree.iterfind(".//nodeclass[@name='Transition']/node"):
            transition = node.find("attribute[@name='ID']").text.strip()
            xmlid_to_graphid[node.get('id')] = transition
            self.add_transition(transition,
                                strength = int(node.find("attribute[@name='FunctionList']"
                                                         "/colList/colList_body/colList_row"
                                                         "/colList_col[@nr='1']").text.strip()),
                                x = float(node.find("graphics/graphic").get('x').strip()),
                                y = float(node.find("graphics/graphic").get('y').strip()))
            
        for node in tree.iterfind(".//edgeclass[@name='Edge']/edge"):
            self.add_edge(xmlid_to_graphid[node.get('source')],
                          xmlid_to_graphid[node.get('target')], weight=
                          int(node.find("attribute[@name='Multiplicity']").text.strip()))
        return marking

