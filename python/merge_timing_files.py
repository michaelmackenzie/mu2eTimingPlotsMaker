# Create total timing files by looping through all modules

import argparse
import time
import os, sys

my_dir=os.environ['PWD']
my_python_dir=my_dir+'/python'
sys.path.append(my_python_dir)

#-------------------------------------------------------------------------------
def parseArgs(argv):
    parser = argparse.ArgumentParser(prog='./merge_timing_files.py')
    
    parser.add_argument("--input-dir", "-i", dest='input_dir', default="", type=str, help="Input directory")
    parser.add_argument("--max-evts", "-max", dest='max_evts', default=1e7, type=int, help="max n events")

    try:
        args = parser.parse_args(argv)
        
        checkArgs(args)
        
    except:
        parser.print_help()
        raise

    return args

#-------------------------------------------------------------------------------
def checkArgs(args):
    if not os.path.exists(args.input_dir):
        os.makedirs(args.input_dir)
    elif not os.path.isdir(args.input_dir):
        raise Exception("Cannot access directory '{}'".format(args.output_dir))
        
    return

#--------------------------------------------------------------------------------
def readFile(fileName, events, timing, args):
    f      = open(fileName)
    lines  = f.readlines()
    counter = 0
    for x in lines:
        if counter >= args.max_evts:
            break
        events.append(x.split(',')[:-1])
        timing.append(float(x.split(',')[-1]))
        counter = counter + 1

#-------------------------------------------------------------------------------
# Get the list of modules by checking for csv files
def modules_list(input_dir):
    dir_content = os.listdir(input_dir)
    modules = []
    for f in dir_content:
        if '.csv' not in f: continue
        module = f.split('/')[-1].replace('.csv', '')
        if 'tot_' in module or 'Prefetch' in module or 'subsystem' in module or 'OfflineFragmentReader' in module:
            continue
        modules.append(module)
    return modules

#-------------------------------------------------------------------------------
def merge_timing_files(args):
    input_dir = args.input_dir

    events = []
    timing = []
    timing_prescale = []
    timing_filters  = []

    reference_module = 'CaloHitMakerFast' # Fixed module that runs every event
    readFile(input_dir+f'/{reference_module}.csv', events, timing, args)
    nevents = len(events)
    print("[merge_timing_files] nevents from {} = {}".format(reference_module, nevents))

    timing = []
    timing_noFilters = []
    timing_SDFilter = []
    timing_TCFilter = []
    timing_HSFilter = []
    timing_TSFilter = []

    # Initialize event timings to 0
    for index in range(nevents):
        timing.append(0)
        timing_noFilters.append(0)
        timing_prescale.append(0)
        timing_filters.append(0)
        timing_SDFilter.append(0)
        timing_TCFilter.append(0)
        timing_HSFilter.append(0)
        timing_TSFilter.append(0)

    # Loop through each module that was run
    modules = modules_list(input_dir)
    for mm in modules:
        tmp_events = []
        tmp_timing = []
        fname = input_dir+'/'+mm+'.csv'
        if not os.path.exists(fname): # Ensure the module file exists
            continue
        readFile(fname, tmp_events, tmp_timing, args)
        print("processing module {}...".format(mm))

        # For every event this module was run, add it to the time tracking
        j = 0
        for i, evt in enumerate(events):
            if j >= len(tmp_events): break
            new_evt = tmp_events[j]
            if evt != new_evt: continue # Continue until the next event is found
            timing[i] += + tmp_timing[j]
            if "Filter" not in mm and "PS" not in mm:
                timing_noFilters[i] += tmp_timing[j]
            if "Filter" in mm:
                timing_filters[i]   += tmp_timing[j]
            if mm.endswith('PS'):
                timing_prescale[i]  += tmp_timing[j]
            if "HSFilter" in mm:
                timing_HSFilter[i]  += tmp_timing[j]
            if "TCFilter" in mm:
                timing_TCFilter[i]  +=tmp_timing[j]
            if "TSFilter" in mm:
                timing_TSFilter[i]  += tmp_timing[j]
            j += 1 # Move to the next target event

    # Print out the resulting merged total timing files
    with open(input_dir+'/tot_event_timing.csv', 'w') as txt_file:
        for i in range(len(events)):
            print("{},{},{},{}".format(events[i][0], events[i][1], events[i][2], timing[i]), file=txt_file)

    with open(input_dir+'/tot_event_timing_noFilters.csv', 'w') as txt_file:
        for i in range(len(events)):
            print("{},{},{},{}".format(events[i][0], events[i][1], events[i][2], timing_noFilters[i]), file=txt_file)

    with open(input_dir+'/tot_timing_filters.csv', 'w') as txt_file:
        for i in range(len(events)):
            print("{},{},{},{}".format(events[i][0], events[i][1], events[i][2], timing_filters[i]), file=txt_file)

    with open(input_dir+'/tot_timing_prescale.csv', 'w') as txt_file:
        for i in range(len(events)):
            print("{},{},{},{}".format(events[i][0], events[i][1], events[i][2], timing_prescale[i]), file=txt_file)

    with open(input_dir+'/tot_timing_SDFilter.csv', 'w') as txt_file:
        for i in range(len(events)):
            print("{},{},{},{}".format(events[i][0], events[i][1], events[i][2], timing_SDFilter[i]), file=txt_file)

    with open(input_dir+'/tot_timing_TCFilter.csv', 'w') as txt_file:
        for i in range(len(events)):
            print("{},{},{},{}".format(events[i][0], events[i][1], events[i][2], timing_TCFilter[i]), file=txt_file)

    with open(input_dir+'/tot_timing_HSFilter.csv', 'w') as txt_file:
        for i in range(len(events)):
            print("{},{},{},{}".format(events[i][0], events[i][1], events[i][2], timing_HSFilter[i]), file=txt_file)

    with open(input_dir+'/tot_timing_TSFilter.csv', 'w') as txt_file:
        for i in range(len(events)):
            print("{},{},{},{}".format(events[i][0], events[i][1], events[i][2], timing_TSFilter[i]), file=txt_file)

#--------------------------------------------------------------------------------
if __name__=="__main__":
    args = parseArgs(sys.argv[1:])
    merge_timing_files(args)

