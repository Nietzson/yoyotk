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
