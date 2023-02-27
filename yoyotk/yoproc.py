import os
import glob

import numpy as np
import nibabel as nib

import yaml



def midway_copyer(input_path, file_list = None, template = None, folder_list = None, FILETYPE = None):
  '''
  Running this method remove the current content of input_path!
  Copy file from folder to the midway input path.
  Also changes the name of the file in the  input folder, adding an index number at the end of the filename
  for midway processing.
  When a template path is given, the copyer prepare folders for each patient, with the input file FILETYPE indicating the modality chosen, to
  run a patient to template midway mapping.'''

  #Cleaning the input datapath
  os.system(f"rm -rf {input_path}/*")
  if template == None:
    for index, file in enumerate(file_list):
        os.system(f"cp {file} {os.path.join(input_path, file.split('/')[-1][:-4])}_{index+1}.nii")
  else:
    print(f"Template analysis, using template at {template}")
    for folder in folder_list:
      os.system(f"mkdir {input_path}/{folder.split('/')[-1]}")
      os.system(f"cp {template} {input_path}/{folder.split('/')[-1]}/{template.split('/')[-1][:-4]}_1.nii")
      for file in glob.glob(os.path.join(folder, '*')):
        if FILETYPE in file:
          os.system(f"cp {file} {input_path}/{folder.split('/')[-1]}/{file.split('/')[-1][:-4]}_2.nii")


  return f'File succefully copied to {input_path}'

def update_config(yamlpath, time_to_compare):
  '''Update the config file for midway'''
  with open(yamlpath, 'r') as f:
    config = yaml.safe_load(f)
    if config is None:
      return 'Config is None!!!'
    config['MRI_cases']['Times_to_compare'] = [time + 1 for time in range(time_to_compare)]
  with open(yamlpath, 'w') as f:
    yaml.dump(config, f)
    # list(np.arange(1,time_to_compare +1))

  return 'config.yaml Updated.'

def run_midway(midway_path):
  '''Run midway from CLI from package root folder.'''
  current_dir = os.getcwd()
  os.chdir(midway_path)
  os.system('run_midway')
  os.chdir(current_dir)
  return 'Midway mapping done.'

def to_brats_format(midwaypath, outputpath, template_path = None):
  '''/!\ Currently only works with template folder
  Take the midway_output folder, or any folder containting folder each containing images in a specific modality,
  and create a Brats like format path, usable as input for brats based model.
  for data organization like MONAI 2018, having subdirectories, a template folder can be given as an argument to fill the subdirectories
  midwaypath: path of the midway folder
  outputpath: path for the output brats like folder
  template: path of a template folder. To correctly fill subdirectories, it should contains the same file as in midwaypath'''
  if os.path.exists(outputpath) == True:
    os.system(f'rm -rf {outputpath}')
  os.system(f'mkdir {outputpath}')

  if template_path != None:
    template_files = glob.glob(os.path.join(template_path, '*', '*', '*'), recursive = True)
    subdirs = glob.glob(os.path.join(template_path, '*'), recursive = True)
    for dirs in subdirs:
      if '.' in dirs:
        os.system(f"cp {dirs} {outputpath}/{dirs.split('/')[-1]}")
      else:
        os.system(f"mkdir {outputpath}/{dirs.split('/')[-1]}")


  midway_files = glob.glob(os.path.join(midwaypath, '*', '*'), recursive=True)
  if template_path != None:
    for template_file in template_files:
      for midway_file in midway_files:
        if template_file.split('/')[-1][:-7] in midway_file:
          subdir = template_file.split('/')[-3]
          file_folder = template_file.split('/')[-2]
          if os.path.exists(os.path.join(outputpath, subdir, file_folder)) == False:
            os.system(f"mkdir {outputpath}/{subdir}/{file_folder}")
            for file in glob.glob(os.path.join(template_path, subdir, file_folder, '*')):
              if 'seg' in file:
                os.system(f"cp {file} {outputpath}/{subdir}/{file_folder}/{file.split('/')[-1]}")

          os.system(f"cp {midway_file} {outputpath}/{subdir}/{file_folder}/{midway_file.split('/')[-1]}")

    return f'Brats formated folder created at {outputpath}'
