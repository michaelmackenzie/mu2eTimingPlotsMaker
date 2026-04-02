#!/usr/bin/env python3
import os, sys
import argparse

import ROOT
from ROOT import TFile, TCanvas, TH1, TH1F, gStyle, TLatex

# The list of modules run keyed by module type
names = dict()

#--------------------------------------------------------------------------------
def parseArgs(argv):
    parser = argparse.ArgumentParser(prog='./plot_filter_time_root.py')
    parser.add_argument("--filename", "-s", dest='filename', default="", type=str, help="input ROOT file")
    parser.add_argument("--out_dir", "-o", dest='out_dir', default="", type=str, help="output directory")
    return parser.parse_args(argv)

#--------------------------------------------------------------------------------
def extract_info(filename, tag):
    f = TFile.Open(filename)
    if not f or f.IsZombie():
        raise RuntimeError(f"Could not open ROOT file: {filename}")

    labels = []
    timing = []
    timing_err = []
    entries = []

    for n in sorted(names.get(tag, [])):
        h = f.Get(f"hm0_{n}")
        if not h:
            continue
        labels.append(n)
        timing.append(float(h.GetMean()))
        # NOTE: your original script used GetMean() for the "error" too; keep identical behavior.
        timing_err.append(float(h.GetMean()))
        entries.append(float(h.GetEntries()))

    f.Close()
    return labels, timing, timing_err, entries

#-------------------------------------------------------------------------------
# Get the list of modules by checking for csv files
def modules_list(input_dir):
    dir_content = os.listdir(input_dir)
    modules = []
    for f in dir_content:
        if '.csv' not in f:
            continue
        module = f.split('/')[-1].replace('.csv', '')
        if 'Prefetch' in module or 'subsystem' in module or 'OfflineFragmentReader' in module:
            continue
        modules.append(module)
    return modules

#-------------------------------------------------------------------------------
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
        else:
            mod_cat['producers'].append(module)
    return mod_cat

#-------------------------------------------------------------------------------
def _ensure_out_dir(out_dir):
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

#-------------------------------------------------------------------------------
# ROOT version of the horizontal bar chart
def plot_module_timing(filename, out_dir, tag, use_visits=False):

    labels, timing, timing_err, entries = extract_info(filename, tag)
    if len(labels) == 0:
        print(f"[WARN] No histograms found for tag '{tag}'")
        return

    max_entries = max(entries) if len(entries) > 0 else 0.0

    # Match original behavior: if not per-visit, scale by N(visits)/N(events)
    if (not use_visits) and max_entries > 0:
        timing     = [timing[i]     * entries[i] / max_entries for i in range(len(entries))]
        timing_err = [timing_err[i] * entries[i] / max_entries for i in range(len(entries))]

    # Determine axis max like matplotlib version
    max_val = max(timing) if len(timing) else 1.0
    x_max = 1.1 * max_val if max_val > 0 else 1.0

    # Styling
    gStyle.SetOptStat(0)
    gStyle.SetTitleFont(42, "XYZ")
    gStyle.SetLabelFont(42, "XYZ")
    gStyle.SetTextFont(42)
    gStyle.SetPadLeftMargin(0.30)
    gStyle.SetPadRightMargin(0.05)
    gStyle.SetPadTopMargin(0.05)
    gStyle.SetPadBottomMargin(0.10)

    # Make a "bar" histogram: each bin is one module, content = timing
    nb = len(labels)
    hbar = TH1F(f"hbar_{tag}_{'visit' if use_visits else 'event'}", "", nb, 0.5, nb + 0.5)
    hbar.SetDirectory(0)

    # Fill bins (top-to-bottom like matplotlib's invert_yaxis)
    # We'll reverse labels so the first module appears at the top once we set labels.
    labels_plot = list(labels)[::-1]
    timing_plot = list(timing)[::-1]

    for i in range(nb):
        bin_idx = i + 1
        hbar.SetBinContent(bin_idx, timing_plot[i])
        hbar.GetXaxis().SetBinLabel(bin_idx, labels_plot[i])

    # Colors to match original: orange for per-event, blue for per-visit
    if use_visits:
        fill = ROOT.kAzure - 3
        line = ROOT.kAzure + 2
    else:
        fill = ROOT.kOrange - 3
        line = ROOT.kOrange + 7

    hbar.SetFillColor(fill)
    hbar.SetLineColor(line)
    hbar.SetLineWidth(1)

    # Axis config
    hbar.GetYaxis().SetRangeUser(0.0, x_max)
    hbar.GetXaxis().SetLabelSize(0.03)   # ~ fontsize=7 feeling
    hbar.GetYaxis().SetTitleSize(0.045)
    hbar.GetYaxis().SetTitleOffset(0.9)

    if 'summary' not in tag:
        ytitle = 'timing/module_visit [ms]' if use_visits else 'timing/module_event [ms]'
    else:
        ytitle = 'timing/event [ms]'
    hbar.GetYaxis().SetTitle(ytitle)

    # Canvas
    c = TCanvas(f"c_{tag}_{'visit' if use_visits else 'event'}", "", 1100, 700)
    c.SetGridx(False)
    c.SetGridy(False)

    # Draw horizontal bars
    hbar.Draw("HBAR")

    # Title (as a top text, closer to matplotlib look)
    title = f"Modules {tag} timing chart"
    t_title = TLatex()
    t_title.SetNDC(True)
    t_title.SetTextFont(42)
    t_title.SetTextSize(0.04)
    t_title.DrawLatex(0.30, 0.965, title)

    # Mu2e Preliminary (NDC, like the matplotlib text)
    t = TLatex()
    t.SetNDC(True)
    t.SetTextFont(42)
    t.SetTextSize(0.045)
    # ROOT doesn't do TeX like matplotlib; approximate the styling:
    t.DrawLatex(0.05, 0.97, "Mu2e Preliminary")

    # Add value labels at end of each bar
    t_val = TLatex()
    t_val.SetTextFont(42)
    t_val.SetTextSize(0.028)
    t_val.SetTextColor(line)

    for i in range(nb):
        # Bin i+1 corresponds to labels_plot[i], timing_plot[i]
        x = timing_plot[i]
        y = i + 1
        # place slightly to the right of bar end
        t_val.DrawLatex(x + 0.005 * x_max, y, f"{x:2.2f}")

    _ensure_out_dir(out_dir)
    out_tag = f"{tag+'_visit' if use_visits else tag}"
    pdf_path = os.path.join(out_dir, f"plot_timing_modules_{out_tag}.pdf")
    png_path = os.path.join(out_dir, f"plot_timing_modules_{out_tag}.png")

    print(f"Printing timing plot for tag {tag} with use visits = {use_visits}")
    c.Print(pdf_path)
    c.Print(png_path)

    # Cleanup (avoid ROOT keeping lots of objects around)
    c.Close()
    del c
    del hbar

#--------------------------------------------------------------------------------
def plot_filters_time(filename, out_dir):
    for key in sorted(names):
        plot_module_timing(filename, out_dir, key, False)
        plot_module_timing(filename, out_dir, key, True)

#--------------------------------------------------------------------------------
if __name__ == "__main__":
    args = parseArgs(sys.argv[1:])
    filename = args.filename
    out_dir = args.out_dir
    ROOT.gROOT.SetBatch(True)

    file_dir = '/'.join(filename.split('/')[:-1])
    modules = modules_list(file_dir)
    names = organize_modules(modules)

    plot_filters_time(filename, out_dir)

