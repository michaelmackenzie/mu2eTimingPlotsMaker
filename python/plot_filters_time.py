import time
import math
#import numpy as np
import matplotlib.pyplot as plt
import glob

from ROOT import TFile
from importlib import import_module

import os, sys
import argparse

from concurrent.futures import ThreadPoolExecutor

names  = { 
    'producers' : { "makeSD",
                    "CaloClusterFast",
                    #"CaloDigiMaker",
                    "CaloHitMakerFast",
                   # "FastCaloHitMaker",
                    "OfflineFragmentReader",
                    "TTCalHelixFinderDe",
                    "TTCalHelixMergerDe",
                    "TTCalSeedFitDe",
                   # "TTCalSeedFitDep",
                    "TTCalTimePeakFinder",
                    "TTflagPH",
                    "TThelixFinder",
                    "TTHelixMergerDe",
                    "TTKSFDe",
                    "TTTZClusterFinder",
                    "TTAprHelixFinder",
                    "TTAprHelixMerger",
                    "TTAprKSF",
                    "TTmakePH",
                    "TTmakeSH",
                    "TTmakeSTH",
                    "TTtimeClusterFinder"
                },
    'prescalers' : {"cprLowPSeedDeEventPrescale",
                    "cprSeedDeEventPrescale",
                    "tprHelixCalibIPADeEventPrescale",
                    "tprHelixIPADeEventPrescale",
                    "tprHelixCalibIPADePrescale",
                    "tprHelixIPADePrescale",
                    "tprLowPSeedDeEventPrescale",
                    "tprLowPSeedDePrescale",
                    "tprLowPSeedDePEventPrescale",
                    "tprSeedDeEventPrescale",
                    "tprSeedDePrescale",
                    "tprSeedDePEventPrescale",
                },
    
                    
    'filters_cpr0'   : {"cprLowPSeedDeHSFilter",
                        "cprLowPSeedDeSDCountFilter",
                        "cprLowPSeedDeTCFilter",
                        "cprLowPSeedDeTSFilter"},
    'filters_cor1'   :{ "cprSeedDeHSFilter",
                        "cprSeedDeSDCountFilter",
                        "cprSeedDeTCFilter",
                        "cprSeedDeTSFilter"},

    'filters_tpr0'   : {"tprHelixDeIpaPhiScaledHSFilter",
                        "tprHelixCalibIPADeSDCountFilter",
                        "tprHelixDeIpaPhiScaledTCFilter",
                        "tprHelixDeIpaHSFilter",
                        "tprHelixIPADeSDCountFilter",
                        "tprHelixDeIpaTCFilter"},

    'filters_tpr1'   : {"tprLowPSeedDeHSFilter",
                        "tprLowPSeedDeSDCountFilter",
                        "tprLowPSeedDeTCFilter",
                        "tprLowPSeedDeTSFilter"},

    'filters_tpr2'   : {"tprSeedDeHSFilter",
                        "tprSeedDeSDCountFilter",
                        "tprSeedDeTCFilter",
                        "tprSeedDeTSFilter"},

    'summary'    : {"tot_event_timing",
                    "tot_event_timing_noFilters",
                    "tot_timing_filters",
                    "tot_timing_prescale",
                    "tot_timing_SDFilter",
                    "tot_timing_TCFilter",
                    "tot_timing_HSFilter",
                    "tot_timing_TSFilter"}
}



def parseArgs(argv):
    parser = argparse.ArgumentParser(prog='./plot_filter_time.py')
    
    parser.add_argument("--filename", "-s", dest='filename', default="", type=str, help="input file")
    parser.add_argument("--out_dir", "-o", dest='out_dir', default="", type=str, help="input file")
    args = parser.parse_args(argv)
        
    return args

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


def plot_module_timing(args, tag, use_visits = False):
    
    labels, timing, timing_err, entries = extract_info(args.filename, tag)
    max_entries      = max(entries) if len(entries) > 0 else 0
    if not use_visits and max_entries > 0:
        timing     = [timing    [index] * entries[index] / max_entries for index in range(len(entries))]
        timing_err = [timing_err[index] * entries[index] / max_entries for index in range(len(entries))]
    plt.clf()
    plt.rcdefaults()
    plt.subplots_adjust(left=0.3,right=0.95, top=0.95, bottom=0.1)

    ax = plt.gca()
    # ax.set_ymargin(left=0.3,right=0)
    #y_pos = np.arange(len(labels))
    y_pos = [] #np.arange(len(labels))

    for i in range(len(labels)):
        y_pos.append(i)
    
    ax.barh(y_pos, timing, align='center', color='orange' if not use_visits else 'blue')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels,fontsize=7)
    ax.invert_yaxis()  # labels read top-to-bottom
    if 'summary' not in tag:
        if use_visits:
            ax.set_xlabel('timing/module_visit [ms]')
        else:
            ax.set_xlabel('timing/module_event [ms]')
    else:
        ax.set_xlabel('timing/event [ms]')
    ax.set_title('Modules {} timing chart'.format(tag))

    for i, v in enumerate(timing):
        ax.text(v + 0., i - 0., str("%2.2f"%v), color='orange' if not use_visits else 'blue', fontweight='bold')
    
    # top = len(y_pos)*1.1
    max_val = max(timing)
    plt.ylim(-0.5, len(timing)*1.08)
    plt.xlim(0., 1.1*max_val)

    plt.text(0.05,0.97,r'$\mathbf{{Mu2e}}$ Preliminary',ha="left",va="top",family='sans-serif',transform=ax.transAxes,fontsize=13)
    # plt.text(0.05,0.92,'ots',ha="left",va="top",family='sans-serif',transform=ax.transAxes,style='italic',fontsize=8)
    # plt.text(0.05,0.88,r'$\sqrt{s}=13\,\mathrm{TeV}$',ha="left",va="top",family='sans-serif',transform=ax.transAxes)

    # if flow_etau_VBF[0]>0:
    #     plt.xscale('log')

    print(f'Printing timing plot for tag {tag} with use visits = {use_visits}')
    plt.savefig("{}/plot_timing_modules_{}.pdf".format(args.out_dir,tag+'_visit' if use_visits else tag))
    plt.savefig("{}/plot_timing_modules_{}.png".format(args.out_dir,tag+'_visit' if use_visits else tag))
    
    return

def plot_filters_time(args):

    for key in sorted(names):
        plot_module_timing(args, key, False)
        plot_module_timing(args, key, True )
    
#--------------------------------------------------------------------------------
if __name__=="__main__":
    args = parseArgs(sys.argv[1:])
    modules = modules_list('/'.join(args.filename.split('/')[:-1]))
    names = organize_modules(modules)
    plot_filters_time(args)

