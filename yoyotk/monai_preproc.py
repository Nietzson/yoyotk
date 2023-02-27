#This module helps managing a framework using the brain segmentation model of MONAI, managing the dalalist.json creation
# and running the inference and training script
import os
import glob
import json

import numpy as np

import nibabel as nib

# from torchvision import transforms
from torchmetrics import Dice
import torch

def inference_datalist(datapath, jsonpath):
  '''Create the dalalist.json file, using all file in datapath for inference'''
  json_dict = {}
  json_dict['training'] = []
  json_dict['validation'] = []
  json_dict['testing'] = []
  #Determine the where the data files are
  if ".nii" in glob.glob(os.path.join(datapath, '*', '*'), recursive = True)[0]:
    folder_list = glob.glob(os.path.join(datapath, '*'), recursive = True)
  elif ".nii" in glob.glob(os.path.join(datapath, '*', '*', '*'), recursive = True)[0]:
    folder_list = glob.glob(os.path.join(datapath, '*', '*'), recursive = True)
  print(folder_list)
  for folder in folder_list:
    file_dict = {}
    file_list = glob.glob(f"{folder}/*")
    for file in file_list:
      if 'seg' in file:
        seg = file
      elif '_t1ce' in file:
        t1ce = file
      elif 't1' in file:
        t1 = file
      elif 't2' in file:
        t2 = file
      elif 'flair' in file:
        flair = file
    file_dict['label'] = seg
    file_dict['image'] = [t1ce, t1, t2, flair]
    json_dict['testing'].append(file_dict)

  with open(jsonpath, 'w+') as f:
    json.dump(json_dict, f, indent = 2)
    f.close()

  return f'datalist created at path {jsonpath}'

def run_inference(monaipath):
  '''Run the inference script for the brain segmentation model of MONAI zoo'''
  current_dir = os.getcwd()
  os.chdir(monaipath)
  print('Starting inference...')
  os.system('python -m monai.bundle run evaluating --meta_file configs/metadata.json --config_file configs/inference.json --logging_file configs/logging.conf')
  os.chdir(current_dir)

  return 'Inference done'

def compute_dice(inf_path, segpath):
  '''From the results of MONAI brain segmentation model, compute the average dice score between the the predictions and the labels
  Return a list with a dictionnary contaiting name of inference file as key and dice score as value at the first index,
  and the average dice score over all data at the second index'''
  #Creating dict to save Dice scores
  dice_dict = {}
  dice = Dice()
  #Iterate through files in  eval
  for folder in os.listdir(inf_path):
      inf_file_path = os.path.join(inf_path, folder, f"{folder}_seg.nii.gz")
      inf_data = nib.load(inf_file_path).get_fdata()
      label_path = os.path.join(segpath, f"HGG/{folder.split('_t1ce')[0]}/{folder.split('_t1ce')[0]}_seg.nii")
      if os.path.exists(label_path) == False:
        label_path = os.path.join(segpath, f"LGG/{folder.split('_t1ce')[0]}/{folder.split('_t1ce')[0]}_seg.nii")
      if os.path.exists(label_path) == False:
        label_path = os.path.join(segpath, f"{folder.split('_t1ce')[0]}/{folder.split('_t1ce')[0]}_seg.nii")
      label_img = nib.load(label_path)
      label_data = label_img.get_fdata()
      #Creating tensors from arrays
      label_tensor = torch.from_numpy(label_data).type(torch.int)
      inf_tensor = torch.from_numpy(inf_data).type(torch.int)
      dice_dict[folder] = dice(inf_tensor, label_tensor)

  return [dice_dict, np.mean([value for value in dice_dict.values()])]

def save_logs(logpath, string, score):
  '''Save run logs at the specified path
  logpath: path of the logfile
  string: string to attach to the run logs
  score: evaluation score of the run'''
  with open(logpath, 'a') as log:
    log.write(f'{string}: {score}\n')
    log.close()

  return f'Logs saved at {logpath}'

