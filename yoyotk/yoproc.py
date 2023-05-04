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
    index = 1
    for file in file_list:
      if FILETYPE in file:
        os.system(f"cp {file} {os.path.join(input_path, file.split('/')[-1][:-4])}_{index+1}.nii")
        index += 1
  else:
    print(f"Template analysis, using template at {template}")
    for folder in folder_list:
      os.system(f"mkdir {input_path}/{folder.split('/')[-1]}")
      os.system(f"cp {template} {input_path}/{folder.split('/')[-1]}/{template.split('/')[-1][:-4]}_1.nii")
      for file in glob.glob(os.path.join(folder, '*')):
        if FILETYPE in file:
          os.system(f"cp {file} {input_path}/{folder.split('/')[-1]}/{file.split('/')[-1][:-4]}_2.nii")


  return f'File succefully copied to {input_path}'

def update_config(yamlpath, time_to_compare, patch_nber = 4):
  '''Update the config file for midway'''
  with open(yamlpath, 'r') as f:
    config = yaml.safe_load(f)
    if config is None:
      raise TypeError('Cannot read the yaml file. It is either empty or there was an issue loading it.')
    config['MRI_cases']['Times_to_compare'] = [time + 1 for time in range(time_to_compare)]
    if patch_nber != 4:
      config['Midway']['Patch_nber'] = patch_nber
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
        os.system(f"cp -R {dirs} {outputpath}/{dirs.split('/')[-1]}")
      else:
        os.system(f"mkdir {outputpath}/{dirs.split('/')[-1]}")


  midway_files = glob.glob(os.path.join(midwaypath, '*', '*'), recursive=True)
  if template_path != None:
    for template_file in template_files:
      for midway_file in midway_files:
        if '.' not in midway_file:
          for subfile in glob.glob(os.path.join(midway_file, '*')):
            if ('.txt' not in subfile) and ('template_centered' not in subfile):
              midway_file = subfile
        if template_file.split('/')[-1][:-7] in midway_file:
          subdir = template_file.split('/')[-3]
          file_folder = template_file.split('/')[-2]
          if os.path.exists(os.path.join(outputpath, subdir, file_folder)) == False:
            os.system(f"mkdir {outputpath}/{subdir}/{file_folder}")
            for file in glob.glob(os.path.join(template_path, subdir, file_folder, '*')):
              if 'seg' in file:
                os.system(f"cp -R {file} {outputpath}/{subdir}/{file_folder}/{file.split('/')[-1]}")

          os.system(f"cp -R {midway_file} {outputpath}/{subdir}/{file_folder}/{midway_file.split('/')[-1]}")

    return f'Brats formated folder created at {outputpath}'

def omat_to_template(inputpath, templatepath, outputpath = None, transpose = None, flip = None):
  '''Copy template transformation matrix to inputpath file. Be aware that this does not actually register the input file,
  only copy header information
  the output image can be fliped or transposed if needed, unsing np.flip or np.transpose arguement
  ---
  inputpath: path to input NIfTI to change the omat on
  templatepath: path to a template NIfTI providing the desired omat
  transpose: default = None. A tuple indicating the tranposition argument for numpy.transpose()
  flip: default = None. An integer indicating the axis to flip, argument of numpy.flip()'''

  if outputpath == None:
    outputpath = inputpath

  template = nib.load(templatepath)
  input_ = nib.load(inputpath)

  tmp_hdr = template.header
  input_hdr = input_.header

  tmp_aff = template.affine
  input_aff = input_.affine

  #Copy header information
  input_hdr['srow_x'] = tmp_hdr['srow_x']
  input_hdr['srow_y'] = tmp_hdr['srow_y']
  input_hdr['srow_z'] = tmp_hdr['srow_z']

  output_data  = input_.get_fdata()

  if transpose != None:
    output_data = np.transpose(input_.get_fdata(), transpose)

  if flip != None:
    output_data = np.flip(input_.get_fdata(), flip)

  #Save file at
  Nii_structure = nib.Nifti1Image(output_data, affine = tmp_aff, header = input_hdr)
  nib.loadsave.save(Nii_structure, outputpath)

  return f"omat changed, output at {outputpath}"


def dict_create(acqlist = [], fill = False, datapath = None):
  '''Create a directory with as many keys as there is values in acqlist. The values will alxays be a dictionnary with t1, t1 e, t2,
  and flair modalities and a segmentation key.
  If fill == True, the list will be filles with files from datapath, assuming the files and dictionnaries are correctly named.
  acqlist: The list of acquisition to add in the directory. Default: []'''
  if acqlist == []:
      dico = {
        'acq':{
          't1': [],
          't1ce': [],
          't2': [],
          'flair': [],
          'seg': []
      }
      }
  else:
    dico = {}
    for i in acqlist:
      dico[i] = {
        't1': [],
        't1ce':[],
        't2': [],
        'flair': [],
        'seg': []
    }


  if fill == True:
      #Determine the where the data files are
    if ".nii" in glob.glob(os.path.join(datapath, '*', '*'), recursive = True)[0]:
      folder_list = glob.glob(os.path.join(datapath, '*', '*'), recursive = True)
    elif ".nii" in glob.glob(os.path.join(datapath, '*', '*', '*'), recursive = True)[0]:
      folder_list = glob.glob(os.path.join(datapath, '*', '*', '*'), recursive = True)

  for files in folder_list:
    for keys in list(dico.keys()):
      if keys in files.split('/')[-1]:
          dico[keys] = dict_filler(files, dico[keys])

  return dico

def dict_filler(file, dico):
    '''Used with database contanining image from different modality for each patient.
    Class the image in the correct modality list
    file: the image file to be classed
    dico: A dictionnary containing the different modality type as keys, and lists as values.'''

    if 't1.' in file:
        dico['t1'].append(file)
    elif 't1ce.' in file:
        dico['t1ce'].append(file)
    elif 't2.' in file:
        dico['t2'].append(file)
    elif 'flair' in file:
        dico['flair'].append(file)
    elif 'seg.' in file:
        dico['seg'].append(file)
    return dico
