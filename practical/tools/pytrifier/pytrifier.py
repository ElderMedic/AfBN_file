#!/usr/bin/env python
'''
Copyright (C) 2011 by
Nicola Bonzanni (n.bonzanni@vu.nl)
Distributed with BSD license.     
All rights reserved, see LICENSE for details.
'''
from datetime import datetime
from itertools import cycle
from cPickle import dump, load as load_pickle
from json import dumps
from xml.etree.ElementTree import ElementTree

from petrinet import PetriNet
from smoothy import smooth

from numpy import matrix, asarray, savetxt

__copyright__ = "Copyright 2011, Nicola Bonzanni"

__license__ = "BSD"
__version__ = "0.1"
__maintainer__ = "Nicola Bonzanni"
__email__ = "n.bonzanni@vu.nl"

def main(argv):
    P = None
    ndr = None
    spn = None
    capacity = 6
    window = 51
    last_values = 20
    loadname = None
    data = None
    firings = None
    runs = 1
    steps = 100
    over_value = None
    knock_out = []
    over_express = []
    le = None
    ge = None
    raw = False
    saveseries = False
    saveraw = False
    plot = False
    pprint = False
    grade = False
    saveanimation = False
    histogram = False
    
    try:
        opts, args = getopt(argv[1:], 'hn:tpgSsl:r:m:L:G:Rw:v:c:k:o:e:N:aT', 
                               ['help', 'ndr=', 'plot', 'print', 'grade', 
                                'save-timeseries', 'save', 'load=', 'runs=',
                                'steps=', 'le=', 'ge=', 'raw', 'window=',
                                'last-nvalues=', 'capacity=', 'knock-out=',
                                'over-express=', 'over-express-val=', 'spn=',
                                'reanimate', 'histogram'])
    except GetoptError:
        usage()
        sys.exit(2)
        
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-w', '--window'):
            window = int(arg)
        elif opt in ('-n', '--ndr'):
            ndr = arg
        elif opt in ('-s', '--save'):
            saveraw = True
        elif opt in ('-S', '--save-timeseries'):
            saveseries = True
        elif opt in ('-l', '--load'):
            loadname = arg
        elif opt in ('-t', '--plot'):
            plot = True
        elif opt in ('-p', '--print'):
            pprint = True
        elif opt in ('-g', '--grade'):
            grade = True
        elif opt in ('-r', '--runs'):
            runs = int(arg)
        elif opt in ('-m', '--steps'):
            steps = int(arg)
        elif opt in ('-L', '--le'):
            le = float(arg)
        elif opt in ('-G', '--ge'):
            ge = float(arg)
        elif opt in ('-R', '--raw'):
            raw = True
        elif opt in ('-v', '--last-nvalues'):
            last_values = int(arg)
        elif opt in ('-c', '--capacity'):
            capacity = int(arg)
        elif opt in ('-k', '--knock-out'):
            knock_out = arg.split(',')
        elif opt in ('-o', '--over-express'):
            over_express = arg.split(',')
        elif opt in ('-e', '--over-express-val'):
            over_value = int(arg)
        elif opt in ('-N', '--spn'):
            spn = arg
        elif opt in ('-a', '--reanimate'):
            saveanimation = True
        elif opt in ('-T', '--histogram'):
            histogram = True
    
    if not (loadname or ndr or spn):
        fatal_error('You must load either a Petri net or data.')
        
    if spn and ndr:
        fatal_error('You can load only one network at a time.')
    
    if loadname and (ndr or spn):
        fatal_error('You can\'t load both data and Petri net.')
    
    if not loadname and runs < 1:
        fatal_error('You must run at least 1 simulation.')
        
    if not loadname and steps < 1:
        fatal_error('You must run at least for 1 step.')
        
    # TODO: Check steps with lastvalues and window lenght
        
    if not loadname and capacity < 1:
        fatal_error('The capacity must be at least 1.')
        
    if window < 5 or window % 2 == 0:
        fatal_error('Your windows must be an odd integer greater than 4.')
        
    if grade and not (le or ge):
        fatal_error('You must specify at least one reference value for the grading.')
    
    if (plot or pprint or grade or histogram or saveseries) and len(args) < 1:
        fatal_error('You must specify a list of places.')
        
    if not (plot or pprint or grade or histogram or saveseries or saveraw or saveanimation):
        fatal_error('Yaaaawn... busy day hum?!')
        
    if not over_value:
        over_value = capacity - 1
    
    if loadname:
        loadnames = loadname.split(',')
        data = []
        firings = []
        for filename in loadnames:
            try:
                # Load data from a file
                markings, sequences = load(filename)
                # Check for if the markings contain the same set of places
                if data and set(markings[0]) != set(data[0]):
                    print "You are trying to merge incompatible data files."
                    print "Skipping {0}...".format(filename)
                    continue
                # TODO: Check for same simulation lengths
                # TODO: Check for same initial conditions
                # Merge the current data file with the newly loaded file
                firings.extend(sequences)
                data.extend(markings)
            except ValueError:
                print "Data format error: {0} contains incompatible data".format(filename)
                print "Skipping {0}...".format(filename)
            except IOError as (errno, strerror):
                print "I/O error({0}): {1} - {2}".format(errno, filename, strerror)
                print "Skipping {0}...".format(filename)
        if not data:
            fatal_error('Unable to load any data.')
    else:
        try:
            if ndr: P = PetriNet(filename=ndr, fileformat='ndr', capacity=capacity)
            elif spn: P = PetriNet(filename=spn, fileformat='spn', capacity=capacity)
        except IOError as (errno, strerror):
            print "I/O error({0}): {1} - {2}".format(errno, ndr, strerror)
            fatal_error('Unable to load the Petri net from {0}.'.format(ndr))
        for name in knock_out:
            if name in P.graph['marking']: P.graph['marking'][name] = 0
            else: print "Unable to knock out {0}. Gene not found, skipping.".format(name)
        for name in over_express:
            if name in P.graph['marking']: P.graph['marking'][name] = over_value
            else: print "Unable to over express {0}. Gene not found, skipping.".format(name)
        data, firings = P.simulate(steps, runs)
        
    if saveanimation:
        filename = 'reanimation-{0}.html'.format(datetime.now().strftime('%Y%m%d%H%M%S'))
        try:
            save_reanimation(filename, P, data, firings)
        except IOError as (errno, strerror):
            print "I/O error({0}): {1} - {2}".format(errno, filename, strerror)
            print "Unable to save the reanimation data to {0}.".format(filename)
        
    if saveraw:
        filename = 'data-{0}.pyt'.format(datetime.now().strftime('%Y%m%d%H%M%S'))
        try:
            save(filename, data, firings)
        except IOError as (errno, strerror):
            print "I/O error({0}): {1} - {2}".format(errno, filename, strerror)
            print "Unable to save the simulation data to {0}.".format(filename)   
    
    if saveseries:
        save_timeseries(data, args, window, raw)
    if pprint:
        print_lastvalues(data, args, last_values)
    if grade:
        grade_lastvalues(data, args, last_values, le, ge)
    if plot:
        plot_timeseries(data, args, window, raw)
    if histogram:
        plot_histogram(data, args, last_values)

def fatal_error(msg):
    print msg
    print 'Try \'{0} --help\' for help.'.format(os.path.basename(sys.argv[0]))
    sys.exit(2)

def usage():
    print '''Pytrifier (c) 2011 - Nicola Bonzanni - VU University Amsterdam
Usage: {0} {{-l DATAFILE,... | -n PETRINET}} COMMAND... [OPTION]... [PLACE]...
Performs COMMANDS on the data obtained from DATAFILEs or simulating the PETRINET supplied in ndr file format.

    -l, --load=DATAFILE,...     load comma seprated DATAFILEs and join them
                                together
    -n, --ndr=PETRINET          load a PETRINET in ndr format in memory
    -N, --spn=PETRINET          load a PETRINET in spstochpn format in memory

    COMMAND:
    -a, --reanimate             save a reanimation html page from which is
                                possible to watch an animation of the first
                                simulation run
    -g, --grade                 for each PLACE print the percentage of runs
                                for which the average of the last NVALUES
                                time points is greater-or-equal GE and/or less
                                or-equal LE
    -p, --print                 print the mean and standard deviation of the
                                last NVALUES time points (previously averaged
                                over all simulation runs) for each given PLACE
    -T, --histogram             plot the histogram of the means and standard
                                deviations of the last NVALUES time points
                                (previously averaged over all simulation runs)
                                for each given PLACE
    -s, --save                  save the raw in memory data in binary format
    -S, --save-timeseries       save the smothed mean (over a window of size
                                WINDOW), the standard deviation, and the raw
                                mean of the time series of each PLACE
    -t, --plot                  plot the smoothed mean (over a window of size
                                WINDOW) and the standard deviation of the
                                selected PLACES. Plot also the raw mean if the
                                --raw option is selected
                                
    OPTION:
    -c, --capacity=CAP          a transition is not enabled if at least one
                                of the output places contains CAP or more
                                tokens. Default is 6
    -e, --over-express-val=OVAL see --over-express. Default is CAP - 1
    -G, --ge=GE                 see --grade
    -k, --knock-out=KGENE,...   specifies a comma separated list of KGENE for
                                which the initial marking is overwritten to 0
    -L, --le=LE                 see --grade
    -m, --steps=NSTEPS          if a simulation will be performed, it will run
                                for NSTEPS. Default is 100
    -o, --over-express=GENE,... specifies a comma separated list of GENE for
                                which the initial marking is overwritten to
                                OVAL
    -r, --runs=NRUNS            if PETRINET is provided, NRUNS simulations
                                will be performed. Default is 1
    -R, --raw                   see --plot and --save-timeseries
    -v, --last-nvalues=NVALUES  see --grade and --print. Default is 20
    -w, --window=WINDOW         see --plot and --save-timeseries. Default is 51
    '''.format(os.path.basename(sys.argv[0]))

def save(filename, data, firings):
    with open(filename, 'wb') as f:
        dump((data,firings), f, -1) # where -1 is interpred as HIGHEST_PROTOCOL
        
def load(filename):
    with open(filename, 'rb') as f:
        data, firings = load_pickle(f)
    return data, firings

def save_reanimation(filename, net, data, firings):
    tree = ElementTree(file='reanimation/index.html')
    script_element = tree.find(".//script[@id='pytrifier-data']")
    script_element.text = 'var network_data={0};'.format(
                    dumps({'nodes': [dict(d, id=x) for x,d in net.nodes(data=True)], 
                           'edges': [dict(d, id=s+t, source=s, target=t) for s,t,d in net.edges(data=True)]}))
    script_element.text += 'var markings_data={0};'.format(dumps(data[0]))
    script_element.text += 'var firings_data={0};'.format(dumps(firings[0]))
    script_element.text += 'var network_capacity={0};'.format(net.capacity)
    script_element.text += 'var marking_max={0};'.format(len(data[0].itervalues().next()))
    tree.write(filename, method="html")

def plot_histogram(data, names, window):
    import matplotlib.pyplot as plt
    # Define colors table
    colors = cycle(['b', 'r', 'g', 'c', 'm', 'y', 'k']) 
    # Init graph area
    fig = plt.figure()
    top = fig.add_subplot(111)
    # Label axes
    plt.ylabel('Tokens')
    plt.xlabel('Species')
    width = 0.15
    current_position = 0
    positions = []
    for name in names:
        color = colors.next()
        mx = matrix([d[name] for d in data])
        # Compute the mean over all simulation runs for each time point
        mean = asarray(mx.mean(0)).squeeze()
        top.bar(current_position, mean[-window:].mean(),width, color=color, yerr=mean[-window:].std(), ecolor='k')
        current_position += width
        positions.append(current_position - width/2.0)
        
    top.set_xticks(positions)
    top.set_xticklabels(names)
    plt.ylim(ymin=0)
    plt.show()

def plot_timeseries(data, names, window, raw=False):
    import matplotlib.pyplot as plt
    # Define colors table
    colors = cycle(['b', 'r', 'g', 'c', 'm', 'y', 'k'])
    # Init graph area
    fig = plt.figure()
    top = fig.add_subplot(111)
    # Label axes
    plt.ylabel('Tokens')
    plt.xlabel('Steps')
 
    # Loop over all the place names
    for name in names:
        color = colors.next()
        mx = matrix([d[name] for d in data])
        # Compute the mean over all simulation runs for each time point
        mean = asarray(mx.mean(0)).squeeze()
        std = asarray(mx.std(0)).squeeze()
        smooth_mean = smooth(mean, window)[:-window/2]
        std_plus = smooth_mean+std[:-window/2]
        std_minus = smooth_mean-std[:-window/2]
        x = range(0, len(smooth_mean))
        if raw:
            top.plot(x, mean[:-window/2], c=color, alpha=0.3, lw=1)
        top.plot(x, smooth_mean, c=color, label=name, lw=3)
        top.fill_between(x, std_plus, std_minus, where=std_plus>=std_minus,
                         alpha=0.5, facecolor=color, interpolate=True, lw=0.1)
        
    plt.ylim(ymin=0)
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=3, mode="expand", borderaxespad=0.)
    plt.show()

def save_timeseries(data, names, window=None, raw=False):
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    for name in names:
        filename = name + '_' + now
        mx = matrix([d[name] for d in data])
        # Compute the mean over all simulation runs for each time point
        mean = asarray(mx.mean(0)).squeeze()
        if raw:
            savetxt(filename + '_raw.txt', matrix)
        savetxt(filename + '_mean.txt', mean)
        savetxt(filename + '_std.txt', asarray(matrix.std(0)).squeeze())
        if window:
            savetxt(filename + '_smooth_mean.txt', smooth(mean, window)[:-window/2])
            
def print_lastvalues(data, names, window):
    output = '{0}: mean={1} std={2}'
    for name in names:
        mx = matrix([d[name] for d in data])
        # Compute the mean over all simulation runs for each time point
        mean = asarray(mx.mean(0)).squeeze()
        print output.format(name, str(mean[-window:].mean()),
                            str(mean[-window:].std()))
                            
def grade_lastvalues(data, names, window, le=None, ge=None, e=None):
    output = '{0}: {1}% of the simulations has an average {2} {3} in \
the last {4} steps, over {5} runs (mean={6})'
    for name in names:
        mx = matrix([d[name][-window:] for d in data])
        row_mean = mx.mean(1)
        mean = mx.mean()
        if le:
            print output.format(name, (row_mean <= le).sum() /
                                float(len(row_mean)), '<=', le, window,
                                str(len(row_mean)), mean)
        if ge:
            print output.format(name, (row_mean >= le).sum() /
                                float(len(row_mean)), '>=', le, window,
                                str(len(row_mean)), mean)

if __name__ == '__main__':
    import sys
    import os
    from getopt import getopt, GetoptError
    main(sys.argv)