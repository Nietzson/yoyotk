import os
import glob

import numpy as np
import nibabel as nib


def file_lister(FILETYPE, folder_path):
    '''Browse the folder_path directory and create a file_list of file containing
    the FILETYPE string in their name'''
    file_list = []
    for index, file in enumerate(glob.glob(folder_path)):
        if FILETYPE in file:
            file_list.append(file)

    return file_list


def midway_copyer(file_list, input_path):
  '''Copy file from folder to the midway input path.
  Also changes the name of the file in the  input folder, adding an index number at the end of the filename
  for midway processing.'''
  for index, file in enumerate(file_list):
      os.system(f"cp {file} {os.path.join(input_path, file.split('/')[-1][:-4])}_{index+1}.nii")

  return f'File succefully copied to {input_path}'

def index_list_printer(file_list):
  '''Returns a list of index, that can be used to fill the midway config.yaml file'''
  array = np.arange(1, len(file_list)+1)
  return array

def run_midway(midway_path):
  '''Run midway from CLI from package root folder.'''
  current_dir = os.getcwd()
  os.chdir(midway_path)
  os.system('run_midway')
  os.chdir(current_dir)
  return 'Midway mapping done.'

