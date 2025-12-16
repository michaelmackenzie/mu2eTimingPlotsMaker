import time
import math
import matplotlib.pyplot as plt

from ROOT import TFile
from importlib import import_module

import os, sys
import argparse

# The list of modules run keyed by module type
names  = dict()


#--------------------------------------------------------------------------------
def parseArgs(argv):
    parser = argparse.ArgumentParser(prog='./plot_filter_time.py')
    
    parser.add_argument("--filename", "-s", dest='filename', default="", type=str, help="input file")
    parser.add_argument("--out_dir", "-o", dest='out_dir', default="", type=str, help="input file")
    args = parser.parse_args(argv)
        
    return args

#--------------------------------------------------------------------------------
def extract_info(filename, tag):
    file = TFile.Open(filename)
    
    labels = []
    timing = []
    timing_err = []
    entries = []
    for n in sorted(names[tag]):
        h = file.Get("hm0_{}".format(n))
        if h == None: continue
        labels.append(n)
        timing.append(h.GetMean())
        timing_err.append(h.GetMean())
        entries.append(h.GetEntries())

    return labels, timing, timing_err, entries

#-------------------------------------------------------------------------------
# Get the list of modules by checking for csv files
def modules_list(input_dir):
    dir_content = os.listdir(input_dir)
    modules = []
    for f in dir_content:
        if '.csv' not in f: continue
        module = f.split('/')[-1].replace('.csv', '')
        if 'Prefetch' in module or 'subsystem' in module or 'OfflineFragmentReader' in module:
            continue
        modules.append(module)
    return modules

#-------------------------------------------------------------------------------
# Get the list of modules by checking for csv files
def organize_modules(modules):
    mod_cat = {
        'producers' : [],
        'prescalers' : [],
        'filters' : [],
        'summary' : []
        }
    for module in modules:
        if 'Filter' in module:
            mod_cat['filters'].append(module)
        elif 'tot' in module:
            mod_cat['summary'].append(module)
        elif module.endswith('PS'):
            mod_cat['prescalers'].append(module)
        else: # Assume a producer
            mod_cat['producers'].append(module)
    return mod_cat

#-------------------------------------------------------------------------------
# Make a bar plot of the timing by module
def plot_module_timing(filename, out_dir, tag, use_visits = False):

    # Get the data from the input file for each module
    labels, timing, timing_err, entries = extract_info(filename, tag)
    max_entries      = max(entries) if len(entries) > 0 else 0
    y_pos = range(len(labels))    

    # If doing per event, scale the module times by N(visits) / N(events)
    if not use_visits and max_entries > 0:
        timing     = [timing    [index] * entries[index] / max_entries for index in range(len(entries))]
        timing_err = [timing_err[index] * entries[index] / max_entries for index in range(len(entries))]

    # Configure the plot style
    plt.clf()
    plt.rcdefaults()
    plt.subplots_adjust(left=0.3,right=0.95, top=0.95, bottom=0.1)

    # Configure the axes
    ax = plt.gca()
    ax.barh(y_pos, timing, align='center', color='orange' if not use_visits else 'blue')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels,fontsize=7)
    ax.invert_yaxis()  # labels read top-to-bottom
    if 'summary' not in tag:
        if use_visits: ax.set_xlabel('timing/module_visit [ms]')
        else:          ax.set_xlabel('timing/module_event [ms]')
    else:              ax.set_xlabel('timing/event [ms]')
    ax.set_title('Modules {} timing chart'.format(tag))

    # Add the text timing values to the plot
    for i, v in enumerate(timing):
        ax.text(v + 0., i - 0., str("%2.2f"%v), color='orange' if not use_visits else 'blue', fontweight='bold')

    # Configure the axis ranges
    max_val = max(timing)
    plt.ylim(-0.5, len(timing)*1.08)
    plt.xlim(0., 1.1*max_val)


    # Print the plot in PDF and PNG
    plt.text(0.05,0.97,r'$\mathbf{{Mu2e}}$ $\it{Preliminary}$',ha="left",va="top",family='sans-serif',transform=ax.transAxes,fontsize=13)
    print(f'Printing timing plot for tag {tag} with use visits = {use_visits}')
    plt.savefig("{}/plot_timing_modules_{}.pdf".format(out_dir,tag+'_visit' if use_visits else tag))
    plt.savefig("{}/plot_timing_modules_{}.png".format(out_dir,tag+'_visit' if use_visits else tag))
    
    return

#--------------------------------------------------------------------------------
def plot_filters_time(filename, out_dir):

    # For each module list category, plot the timing per visit and per event
    for key in sorted(names):
        plot_module_timing(filename, out_dir, key, False)
        plot_module_timing(filename, out_dir, key, True )
    
#--------------------------------------------------------------------------------
if __name__=="__main__":
    # Parse the arguments and retrieve the parameters
    args = parseArgs(sys.argv[1:])
    filename = args.filename
    out_dir = args.out_dir

    # Get the list of modules and organize them by type
    file_dir = '/'.join(filename.split('/')[:-1])
    modules = modules_list(file_dir)
    names = organize_modules(modules)

    # Make the plots
    plot_filters_time(filename, out_dir)

