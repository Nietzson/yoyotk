#This module helps managing a framework using the brain segmentation model of MONAI, managing the dalalist.json creation
# and running the inference and training script
import os
import glob
import json

import numpy as np

import nibabel as nib

# from torchvision import transforms
from monai.losses.dice import DiceLoss
import torch
import monai
from sklearn.model_selection import train_test_split


def inference_datalist(datapath, jsonpath, training = False, keep_split = False, split_string = None, val = False):
  '''Create the dalalist.json file, using all file in datapath for inference'''
  folder_list = None
  json_dict = {}
  json_dict['training'] = []
  json_dict['validation'] = []
  json_dict['testing'] = []
  #Determine the where the data files are
  if ".nii" in glob.glob(os.path.join(datapath, '*', '*'), recursive = True)[0]:
    folder_list = glob.glob(os.path.join(datapath, '*'), recursive = True)
  elif ".nii" in glob.glob(os.path.join(datapath, '*', '*', '*'), recursive = True)[0]:
    folder_list = glob.glob(os.path.join(datapath, '*', '*'), recursive = True)
  elif ".nii" in glob.glob(os.path.join(datapath, '*', '*', '*'), recursive = True)[0]:
    folder_list = glob.glob(os.path.join(datapath, '*', '*'), recursive = True)

  if folder_list == None:
    raise ValueError (f'The data {datapath} folder has not been identified. Check the path given to the inference_datalist().')
  print(folder_list)

  for folder in folder_list:
    file_dict = {}
    file_list = glob.glob(f"{folder}/*")
    for file in file_list:
      if 'seg' in file:
        seg = file
      elif '_t1ce' in file:
        t1ce = file
      elif '_t1' in file:
        t1 = file
      elif '_t2' in file:
        t2 = file
      elif '_flair' in file:
        flair = file
    if val == False:
      file_dict['label'] = seg
    file_dict['image'] = [t1ce, t1, t2, flair]
    json_dict['testing'].append(file_dict)

  if training == True:
    monai.utils.set_determinism(seed=123)
    train_list, other_list = train_test_split(json_dict['testing'], train_size=200)
    val_list, test_list = train_test_split(other_list, train_size=0.5)
    json_dict = {"training": train_list, "validation": val_list, "testing": test_list}
  if keep_split == True:
    with open(jsonpath, 'r') as f:
      data = f.readlines()
      f.close()
    for i in range(len(data)):
      if '/' in data[i]:
          parts = data[i].split('/')
          parts[5] = split_string
          data[i] = '/'.join(parts)
    with open(jsonpath, 'w+') as f:
      f.writelines(data)
      f.close()

  with open(jsonpath, 'w+') as f:
    json.dump(json_dict, f, indent = 2)
    f.close()




  return f'datalist created at path {jsonpath}'

def set_model_for_inference(inferencepath, modelpath):
  ''' Set the  model to be used for inference in monai
  inferencepath: path to the infeence.json file
  modelpath: path to the .pt file '''
  inferencepath = inferencepath
  with open(inferencepath, 'r') as f:
      data = json.load(f)
      f.close()
  data['handlers'][0]['load_path'] = f"{modelpath}"
  with open(inferencepath, 'w+') as f:
      json.dump(data, f, indent = 2)
      f.close()
  return f"Model set to {modelpath}"

def run_inference(monaipath):
  '''Run the inference script for the brain segmentation model of MONAI zoo'''
  current_dir = os.getcwd()
  os.chdir(monaipath)
  print('Starting inference...')
  os.system('python -m monai.bundle run evaluating --meta_file configs/metadata.json --config_file configs/inference.json --logging_file configs/logging.conf')
  os.chdir(current_dir)

  return 'Inference done'

def compute_dice(inf_path, segpath, per_label = False):
  '''From the results of MONAI brain segmentation model, compute the average dice score between the the predictions and the labels
  Return a list with a dictionnary contaiting name of inference file as key and dice score as value at the first index,
  and the average dice score over all data at the second index'''
  #Creating dict to save Dice scores
  np.random.seed(123)
  torch.manual_seed(123)
  print("NEW VERSION")
  dice_dict = {}
  # dice = Dice(num_classes = 4, average = 'macro')
  dice =  DiceLoss(smooth_nr=0,
               smooth_dr=1e-05,
               squared_pred=True,
               to_onehot_y=False,
               sigmoid=True)
  #Iterate through files in  eval
  for folder in os.listdir(inf_path):
      inf_file_path = os.path.join(inf_path, folder, f"{folder}_seg.nii.gz")
      inf_data = nib.load(inf_file_path).get_fdata().astype('int')
      label_path = os.path.join(segpath, f"HGG/{folder.split('_t1ce')[0]}/{folder.split('_t1ce')[0]}_seg.nii")
      if os.path.exists(label_path) == False:
        label_path = os.path.join(segpath, f"LGG/{folder.split('_t1ce')[0]}/{folder.split('_t1ce')[0]}_seg.nii")
      if os.path.exists(label_path) == False:
        label_path = os.path.join(segpath, f"{folder.split('_t1ce')[0]}/{folder.split('_t1ce')[0]}_seg.nii")
      label_img = nib.load(label_path)
      label_data = label_img.get_fdata().astype('int')
      if per_label == True:
        oh_labels = np.zeros((len(np.unique(label_data))+1, *label_data.shape))
        oh_inf = np.zeros((len(np.unique(inf_data))+1, *inf_data.shape))
        for classes in np.unique(label_data):
          if classes == np.unique(label_data)[-1]:
            oh_labels[-1] = (label_data == np.unique(label_data)[-1])
            oh_inf[-1] = (inf_data == np.unique(label_data)[-1])
          else:
            oh_labels[classes] = (label_data == classes)
            oh_inf[classes] = (inf_data == classes)
        oh_label_tensor = torch.from_numpy(oh_labels).type(torch.int)
        oh_inf_tensor = torch.from_numpy(oh_inf).type(torch.int)
        bg = dice(oh_inf_tensor[0], oh_label_tensor[0])
        tc = dice(oh_inf_tensor[1], oh_label_tensor[1])
        wt = dice(oh_inf_tensor[2], oh_label_tensor[2])
        et = dice(oh_inf_tensor[3], oh_label_tensor[3])
        dice_dict[folder] = {"background": bg,
                             "TC": tc,
                             "WT": wt,
                             "ET": et}
      else:

        #Creating tensors from arrays
        label_tensor = torch.from_numpy(label_data).type(torch.int)
        inf_tensor = torch.from_numpy(inf_data).type(torch.int)
        dice_dict[folder] = dice(inf_tensor, label_tensor)

  if per_label == True:
    label_dict = {
            "mean_background": np.mean([value["background"] for value in dice_dict.values()]),
            "mean_TC": np.mean([value["TC"] for value in dice_dict.values()]),
            "mean_WT": np.mean([value["WT"] for value in dice_dict.values()]),
            "mean_ET": np.mean([value["ET"] for value in dice_dict.values()]),
    }

    return [dice_dict, label_dict]
  else:
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

