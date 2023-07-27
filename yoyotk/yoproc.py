import os
import glob
import re

import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt

import yaml
import matplotlib



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
        if 'midway_mapped' in template_file:
          template_file = re.split('_(\d*)_midway_mapped', template_file)[0] + 'placeho'
          print(template_file)
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
    if (".nii" or ".nii.gz") in glob.glob(os.path.join(datapath, '*', '*'), recursive = True)[0]:
      folder_list = glob.glob(os.path.join(datapath, '*', '*'), recursive = True)
    elif (".nii" or ".nii.gz") in glob.glob(os.path.join(datapath, '*', '*', '*'), recursive = True)[0]:
      folder_list = glob.glob(os.path.join(datapath, '*', '*', '*'), recursive = True)
    elif (".nii" or ".nii.gz") in glob.glob(os.path.join(datapath, '*', '*', '*', '*'), recursive = True)[0]:
      folder_list = glob.glob(os.path.join(datapath, '*', '*', '*', '*'), recursive = True)
    elif (".nii" or ".nii.gz") in glob.glob(os.path.join(datapath, '*', '*', '*', '*', '*'), recursive = True)[0]:
      folder_list = glob.glob(os.path.join(datapath, '*', '*', '*', '*', '*'), recursive = True)


  if acqlist != []:
    for files in folder_list:
      for keys in list(dico.keys()):
        if keys in files and (files.endswith('.nii') or files.endswith('.nii.gz')):
            dico[keys] = dict_filler(files, dico[keys])
  else:
    for files in folder_list:
      dico['acq'] = dict_filler(files, dico['acq'])

  return dico

def dict_filler(file, dico):
    '''Used with database contanining image from different modality for each patient.
    Class the image in the correct modality list
    file: the image file to be classed
    dico: A dictionnary containing the different modality type as keys, and lists as values.'''

    if 't1ce' in file:
        dico['t1ce'].append(file)
    elif 't1' in file:
        dico['t1'].append(file)
    elif 't2' in file:
        dico['t2'].append(file)
    elif 'flair' in file:
        dico['flair'].append(file)
    elif 'seg' in file:
        dico['seg'].append(file)
    for keys in list(dico.keys()):
      dico[keys] = sorted(dico[keys])
    return dico

def snapshot(path, filename, batch, figsize  = (8, 115), direction = 'start'):
  '''Create a snapshot of Brats18 structured data.
  datapath: Path of the data to snapshot
  filename: name of the snapshot file
  batch: Number of files to take into the snapshot. The snapshot function will be repeated until there is all files have been snapshoted.
  figsize: Size of the final plot
  direction: {'start', 'end') Whether to take the first or the last <batch> files in the list
  /!\ Batching currently bugged probably because of matplotlib backend
  '''

  #Create patient list
  patient_list = []
  for name in glob.glob(os.path.join(path, '*', '*')):
      tag = name.split('/')[-1]
      patient_list.append(tag)
  patient_list.sort()
  patient_list

  #Create image arrays and plot
  BATCH = batch
  if direction == 'start':
    listfiles = patient_list[:BATCH]
    debut = 1
    fin = BATCH
  elif direction == 'end':
    listfiles = patient_list[BATCH:]
    debut = len(patient_list) - BATCH
    fin = len(patient_list)
  else:
    return f"Incorrect value for direction == {direction}"

  all_files = glob.glob(os.path.join(path, '*', '*', '*'))
  #List used to concatenate images afterward
  concall = np.zeros((50,50))
  print(f'=============== Batch = {BATCH} ===============')
  # #Initliating step counter for the while loop
  # iter = 0
  # current = []
  # while current != patient_list:
  #   if len(patient_list) <= BATCH:
  #     current = patient_list
  #     start = iter * BATCH
  #     end = start + len(current)
  #     print(f"===============Snapshoting files {start} to {end}...===============")
  #     patient_names = []
  #     for patient in current:
  #         patient_files = []
  #         for file in all_files:
  #             if patient in file and "_seg." not in file:
  #                 patient_files.append(file)
  #         patient_files.sort()
  #         name = patient_files[0].split('Brats18_')[-1].split(f"_flair")[0]
  #         patient_names.append(name)
  #         #Load images
  #         base_list = []
  #         for file in patient_files:
  #             img = nib.load(file)
  #             data = img.get_fdata()
  #             base_list.append(np.transpose(data[:,:,int(data.shape[-1] / 2)]))
  #         conc = np.concatenate(np.array(base_list), axis = 1)
  #         if np.array_equal(concall, np.zeros((50,50))):
  #             concall = conc
  #         else:
  #             concall = np.concatenate([concall, conc], axis = 0)
  #     iter += 1
  #     #Creating filename
  #     batch_filename = f"{filename.split('.')[0]}_{start}-{end}.{filename.split('.')[1]}"
  #     print("=============== Done ===============")
  #   else:
  #     current = patient_list[:BATCH]
  #     start = iter * BATCH
  #     end = start + BATCH
  #     print(f"===============Snapshoting files {start} to {end}...===============")
  #     patient_names = []
  #     for patient in current:
  #         patient_files = []
  #         for file in all_files:
  #             if patient in file and "_seg." not in file:
  #                 patient_files.append(file)
  #         patient_files.sort()
  #         name = patient_files[0].split('Brats18_')[-1].split(f"_flair")[0]
  #         patient_names.append(name)
  #         #Load images
  #         base_list = []
  #         for file in patient_files:
  #             img = nib.load(file)
  #             data = img.get_fdata()
  #             base_list.append(np.transpose(data[:,:,int(data.shape[-1] / 2)]))
  #         conc = np.concatenate(np.array(base_list), axis = 1)
  #         if np.array_equal(concall, np.zeros((50,50))):
  #             concall = conc
  #         else:
  #             concall = np.concatenate([concall, conc], axis = 0)
  #     iter += 1
  #     #Updating patient_list to remove files already snapshot
  #     patient_list = patient_list[BATCH:]
  #     #Creating filename
  #     batch_filename = f"{filename.split('.')[0]}_{start}-{end}.{filename.split('.')[1]}"
  #     print("=============== Done ===============")

  #   print('Creating figure')
  #   plt.figure(figsize = (8, 115))
  #   plt.axis('off')
  #   for i, name in enumerate(patient_names):
  #       y = concall.shape[0] / int(len(patient_names) * 2) + (concall.shape[0] / len(patient_names)) * i
  #       x = -250
  #       plt.text(x, y, name, fontsize=12, ha='center', va='bottom')
  #   for i, cond in enumerate(['FLAIR', 'T1', 'T1CE','T2']):
  #       x = concall.shape[1] / 8 + (concall.shape[1] / 4) * i
  #       y = -50
  #       plt.text(x, y, cond, fontsize = 12, ha = 'center', va = 'top')
  #   plt.imshow(concall, cmap = 'gray', interpolation = 'none')
  #   plt.savefig(batch_filename, dpi = 300)
  #   plt.close()
  #   print("=============== Done ===============")

  patient_names = []
  print('Creating concatenated array...')
  for patient in listfiles:
      patient_files = []
      for file in all_files:
          if patient in file and "_seg." not in file:
              patient_files.append(file)
      patient_files.sort()
      name = patient_files[0].split('Brats18_')[-1].split(f"_flair")[0]
      patient_names.append(name)
      #Load images
      base_list = []
      for file in patient_files:
          img = nib.load(file)
          data = img.get_fdata()
          base_list.append(np.transpose(data[:,:,int(data.shape[-1] / 2)]))
      conc = np.concatenate(np.array(base_list), axis = 1)
      if np.array_equal(concall, np.zeros((50,50))):
          concall = conc
      else:
          concall = np.concatenate([concall, conc], axis = 0)
  print('Creating figure')
  plt.figure(figsize = (8, 115))
  plt.axis('off')
  for i, name in enumerate(patient_names):
      y = concall.shape[0] / int(len(patient_names) * 2) + (concall.shape[0] / len(patient_names)) * i
      x = -250
      plt.text(x, y, name, fontsize=12, ha='center', va='bottom')
  for i, cond in enumerate(['FLAIR', 'T1', 'T1CE','T2']):
      x = concall.shape[1] / 8 + (concall.shape[1] / 4) * i
      y = -50
      plt.text(x, y, cond, fontsize = 12, ha = 'center', va = 'top')
  plt.imshow(concall, cmap = 'gray', interpolation = 'none')
  plt.savefig(f"{filename.split('.')[0]}_{debut}-{fin}.{filename.split('.')[1]}", dpi = 300)
  print("=============== Done ===============")

