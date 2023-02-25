import os
import glob

from yoyotk.yoproc import to_brats_format
from yoyotk.monai_preproc import inference_datalist
from yoyotk.monai_preproc import run_inference
from yoyotk.monai_preproc import compute_dice
from yoyotk.monai_preproc import save_logs


def run_brats_monai_eval(datapath, jsonpath, monaipath, infpath, logpath, string_, midway = False, midway_path = None,  template_path = None):
  '''Pipeline function in the yoyotk packages to run inference using the monai brain segmentation model, calculating dice score, and saving the
  results in a given logfile. If midway = True, it will also create the Brats formated folder to be used as input for the pipeline.'''
  if midway == True:
    print(f'midway = {midway}, Starting creating of the input folder\n')
    to_brats_format(midway_path, datapath, template_path)
    print(f'Input folder created at {datapath}')
  print(f'''input data: {datapath}\n
        Creating datalist.json\n''')
  inference_datalist(datapath, jsonpath)
  print('Running inference...\n')
  run_inference(monaipath)
  print('Calculating Dice score...\n')
  results = compute_dice(infpath, datapath)
  print('Saving logs...\n')
  save_logs(logpath, string_, results[1])

  return f'Logs saved at {logpath}'
