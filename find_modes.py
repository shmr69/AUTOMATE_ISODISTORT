import selenium # type: ignore
print(f'Using Selenium version {selenium.__version__}')
import sys
print(f'Using Python version {sys.version}')
from selenium import webdriver # type: ignore
#from webdriver_manager.chrome import ChromeDriverManager
#from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore
from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoSuchWindowException # type: ignore
from selenium.webdriver.common.by import By # type: ignore
#from pymatgen.io.vasp.inputs import Poscar
#from pymatgen.core import Structure
#from pymatgen.core.periodic_table import Species
import numpy as np # type: ignore
print(f'Using numpy version {np.__version__}')
import pprint
import warnings
import os
from pathlib import Path
import yaml # type: ignore
import argparse
import time
import glob


#parent_structure_file : str = '/Users/shmr69/Documents/Brownmillerites/Ca2FeAlO5/switching/Ca2FeAlO5_Imma.cif'
#child_structure_file : str = '/Users/shmr69/Documents/Brownmillerites/Ca2FeAlO5/switching/CONTCAR_Ima2_unstrained_sym.cif'
## TODO find matrix automatically using pymatgen
#basis_transformation : np.ndarray = np.array(
#    [[1, 0, 0],
#    [0, 0, -1],
#    [0, 1, 0]]
#)
#MAIN_PAGE = "https://stokes.byu.edu/iso/isodistort.php"

text_tags : list = [
    # infofile text tags (i.e. initialise)
    'PARENT_FILE', 'DISTORTED_FILE', 'BASIS_TRANSFORM'
]
option_tags_bool : dict = {
    # infofile optional boolean tags and default values
    'READ_MODE' : True, 
    'WRITE_FILE' : False,
    'DEBUG' : False,
    'WEBDRV_WINDOW' : False,
    'SCALEMODES' : False,
}
option_tags_other : dict = {
    # infofile optional tags (non-boolean) and default values
    'ORIGIN_SHIFT' : None,
    'SCALEMODES_LABELS' : None,
    'SCALEMODES_MIN' : 0,
    'SCALEMODES_MAX' : 1,
    'SCALEMODES_STEPS' : 5,
    'DOWNLOAD_DIR' : '~/Downloads/'
}


"""
Functions for file handling
"""

def file_check(filepath) -> str:
    '''check if file is existent and if path is absolute, return full path if provided path is relative'''
    if not os.path.isfile(filepath): # check if files exists
        raise FileNotFoundError(f"The file {filepath.split('/')[-1]} could not be found.")
    elif Path(filepath).is_absolute():
        path = filepath
    else:
        path = os.path.abspath(filepath)
    return path

def save_to_file(result : dict, filename : str = 'modeamplitudes') -> None:
    '''save mode amplitude dict to YAML file without overwriting existing files'''
    if os.path.isfile(f'{filename}.yaml'): # check if file exists
        filename = filename + '_1'
    else:
        i = 1
        while os.path.isfile(f'{filename}_{i}.yaml'): # append filename
            i += 1
            filename = filename + f'_{i}'

    with open(f'{filename}.yaml', 'w+') as ff:
        yaml.dump(result, ff)
    print(f'Saved results to file {filename}.yaml')
    return None
    
def read_from_file(name : str) -> dict | None:
    '''reading mode amplitude dict from YAML file'''
    if not os.path.isfile(f'{name}'): # check if file exists
        raise FileNotFoundError(f'File {name} could not be found')
    else:   
        conf = yaml.safe_load(Path(name).read_text())
        print(f'Reading data from file {name}')
        return conf

def move_downloaded_file(downloads_dir : str, destination: str, number : int, driver, wait_time : float = 5.0) -> None:
    # moving and renaming downloaded file
    time.sleep(wait_time) # wait until file has downloaded
    # look for the latest file in the Downloads directory
    if not os.path.isdir(os.path.expanduser(downloads_dir)):
        driver.quit()
        raise IOError(f"The Dwonloads directory could not be found at {os.path.expanduser(downloads_dir)}")
    list_of_files = glob.glob(os.path.expanduser(downloads_dir) + "*")
    latest_file = max(list_of_files, key = os.path.getctime)
    prefix = 'structure'
    suffix = f'_s{number}.cif'
    filename = destination+'/'+prefix+suffix
    if os.path.isfile(filename): # check if file exists
        warnings.warn(f'A file with the name {prefix+suffix} already exists in this directory.')
        while True:
            answer = input(f"Continue moving {latest_file} and overwrite existing file? (y/n) ")
            if answer.lower() in ["y","yes"]:
                os.rename(latest_file,filename)
                break
            elif answer.lower() in ["n","no"]:
                driver.quit()
                raise FileExistsError(f'A file with the name {filename} already exists.')
            else:
                print('invalid input')
                continue
    else: os.rename(latest_file,filename)
    return None

"""
Functions for parsing the user file
"""

def get_usr_options():
    '''reads filename of infofile and parses it'''
    parser = argparse.ArgumentParser(
        prog='find_modes',
        usage='%(prog)s infofile',
        description='Automatically operate ISODISTORT method 4: mode decomposition',
    )
    parser.add_argument(
        'infofile',
        type=str,
        help='input file',
        nargs='?'
    )
    # TODO Add dryrun
    args = parser.parse_args()

    # Sanity check arguments
    infofile = args.infofile
    if Path(infofile).is_file() is False:
        raise FileNotFoundError(f'Your infofile {infofile} does not exist')

    return infofile

def field_code(lines, myfield, optional : bool = False):
    '''loops through lines of input file and returns the user value for a given input tag. Returns None or KeyError is tag is not found'''
    # TODO Have this ignore the field delimiters automatically, e.g. colons and equal signs etc.
    for line in lines:
        split_line = line.split()

        # Check if not a blank line - if so skip
        if line == '\n':
            continue
        # Turn all the field names to UPPER case
        if split_line[0].upper() == myfield.upper():
            # HACK Assuming colon is the second element in string after the field name ignoring space
            # HACK so grab the third.
            code = ' '.join(split_line[2:])
            return code

    # Made it through entire file without finding our item
    if not optional:
        raise KeyError(f'Unable to find the required tag {myfield} from infofile')

    return None

def read_bool_tag(usr_input : str) -> bool|None:
    '''helper function to convert user text into boolean value (or None)'''
    try:
        if usr_input.upper() in ['TRUE', 'T']:
            return True
        elif usr_input.upper() in ['FALSE', 'F']:
            return False
        else:
            return None
    except AttributeError:
        return None  

def read_usr_info(filename : str,  tags_text : list[str] = text_tags, tags_bool : dict = option_tags_bool, tags_other : dict = option_tags_other):
    '''reads lines from input file and assigns use values to relevant variables'''
    # Read the input file
    with open(filename, 'r', encoding='ASCII') as file:
        lines = file.readlines()

    # Initialise the user data with garbage values
    walker_text = dict.fromkeys(tags_text, -1)

    # Get the main page link
    webdrv_path = field_code(lines, 'WEBDRIVER_PATH')

    # Get the path to the google form
    main_page = field_code(lines, 'MAIN_PAGE')

    # Now get the required info.
    for tag in tags_text:
        usr_text = field_code(lines, tag)
        if tag == 'BASIS_TRANSFORM': # this will be a string of 9 numbers
            basis_list = list(map(int,usr_text.split()))
            if len(basis_list) != 9:
                raise KeyError(f"{usr_text} is not a valid basis transformation matrix ")
            usr_text = np.reshape(basis_list, (-1,3))
        walker_text[tag] = usr_text

    
    # Get optional info
    for opt_tag_b in tags_bool.keys():
        usr_value = field_code(lines,opt_tag_b, optional=True)
        value = read_bool_tag(usr_value)
        if value == None:
            warnings.warn(f"invalid input value for {opt_tag_b}: {usr_value}. Falling back to default value ({tags_bool[opt_tag_b]}).")
            continue
        else:
            tags_bool.update({
                opt_tag_b : value
            })

    for opt_tag_o in tags_other.keys():
        usr_value_o = field_code(lines,opt_tag_o, optional=True)
        if usr_value_o == None:
            warnings.warn(f"invalid input value for {opt_tag_o}: {usr_value_o}. Falling back to default value ({tags_other[opt_tag_o]}).")
            continue
        else:
            if opt_tag_o == 'ORIGIN_SHIFT':
                origin_arr = np.array(list(map(float, usr_value_o.split()))) # generate 1x3 numpy array from input
                if origin_arr is not None and len(origin_arr) != 3:
                    raise KeyError(f"{usr_value_o} is not a valid origin shift")
                usr_value_o = origin_arr
            tags_other.update({
                opt_tag_o : usr_value_o
                })
    return webdrv_path, main_page, walker_text, tags_bool, tags_other

"""
Functions for interfacing with ISODISTORT
"""

def webdriver_setup(webdrv_win : bool, webdrv_path : str):
    '''helper function for setting up the webdriver'''
    options = webdriver.ChromeOptions()
    if not webdrv_win:
        options.add_argument("--headless=new") # don't open window
    else:
        print('opening remote window')
        options.add_experimental_option("detach", True)  # Keep the window open
        options.add_argument("--start-maximized")
        options.add_argument("--remote-allow-origins=*")
    driver = webdriver.Chrome(
        #service=Service(ChromeDriverManager().install()), # optional: install Chrome driver if not present
        #service=Service(webdrv_path), # optional: look for Chrome driver at specific location (uncomment if driver cannot be found)
        options=options
        )
    # Set up webdriver waiting function
    wait = WebDriverWait(
        driver, 
        10 # default timeout
        )
    return driver, wait

def wait_for_page_load(element : str, driver, timeout : float = 10) -> None:
    '''set up built-in selenium waits until certain element can be found and is clickable'''
    try:
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.element_to_be_clickable((By.XPATH, element)))
        if DEBUG == True:
            print(f"page has loaded: {driver.current_url}")
    except TimeoutException:
        print("Timed out waiting for page to load")
        driver.quit()
    except NoSuchElementException:
        print("Could not loacate specified element")
        driver.quit()
    return None

def upload_parent_struct(parent_struct : str, driver) -> None:
    '''uploads parent structure file to main page'''
    filepath = file_check(parent_struct)
    print('Uploading parent structure file...', end="")
    upload_parent_button = driver.find_element(By.XPATH, "/html/body/div[2]/div[1]/ul/form/input[3]")
    upload_parent_button.send_keys(filepath) # upload parent file on first page
    wait_for_page_load('/html/body/div[2]/div[1]/ul/form/input[2]', driver) # wait for OK button to be clickable
    OK_button_1 = driver.find_element(By.XPATH, "/html/body/div[2]/div[1]/ul/form/input[2]")
    OK_button_1.click() #click OK on first page
    wait_for_page_load('/html/body/div[2]/div[5]/form/h3/input', driver) # wait for child upload OK button to be clickable
    print("Done!")
    return None

def upload_child_struct(child_struct : str, driver, wait) -> None:
    '''uploads child structure file to Method 4'''
    filepath = file_check(child_struct)
    print('Uploading child structure file...', end="")
    upload_child_button = driver.find_element(By.XPATH, '/html/body/div[2]/div[5]/form/p/input[67]')
    upload_child_button.send_keys(filepath) # upload child file on first page 
    OK_button_2 = driver.find_element(By.XPATH, "/html/body/div[2]/div[5]/form/h3/input") 
    OK_button_2.click() # click OK on second page
    wait.until(EC.number_of_windows_to_be(2)) # wait until second tab opens
    try: 
        driver.switch_to.window(driver.window_handles[1]) # switch to second tab
    except NoSuchWindowException:
        print("can't switch to second window - probably some error while uploading the child structure." )
        driver.quit()
        return None
    wait_for_page_load("/html/body/div[2]/form/p[1]/input", driver) # wait for OK button on basis transformation page to load
    print("Done!")
    return None

def transform_basis(transformation_matrix : np.ndarray, origin_shift : None|np.ndarray, driver) -> None:
    '''fills in the basis transformation matrix explicitly'''
    matrix = np.asarray(transformation_matrix.flatten(), dtype=str) # convert transformation matrix to 1D array of strings
    print('Transforming basis...', end="")
    specify_basis_button = driver.find_element(By.XPATH, "/html/body/div[2]/form/input[71]")
    specify_basis_button.click() # click 'specify basis as' on third page
    OK_button_3 = driver.find_element(By.XPATH, "/html/body/div[2]/form/p[1]/input")

    # fill basis transformation matrix
    for i,el in enumerate(range(72,81)):
        basis_element = driver.find_element(By.XPATH, f"/html/body/div[2]/form/input[{el}]") # textbox for matrix element in basis transformation matrix
        basis_element.clear()
        basis_element.send_keys(matrix[i])

    # fill origin shift if requested    
    if origin_shift is not None:
        print("Done!")
        print('Shifting origin...', end="")
        specify_origin_button = driver.find_element(By.XPATH, "/html/body/div[2]/form/input[82]")
        specify_origin_button.click()
        for i,x in enumerate(range(83,86)):
            origin_element = driver.find_element(By.XPATH, f"/html/body/div[2]/form/input[{x}]")
            origin_element.clear()
            origin_element.send_keys(str(origin_shift[i]))

    OK_button_3.click() # click OK on third page
    # TODO handle case when basis is incorrect
    wait_for_page_load('/html/body/div[2]/form/input[91]', driver)
    print("Done!")
    return None

def read_mode_amplitudes(driver) -> tuple[dict,dict]:
    '''reads info from distortion results page, outputs info on each distortion mode and A_p mode amplitudes with labels'''
    print('Reading mode amplitudes...', end="")
    text_boxes = driver.find_elements(By.CLASS_NAME, 'span1')
    mode_amplitudes : list[float] = []
    mode_names : list[str] = []
    for ap in range(len(text_boxes)):
        mode_name = text_boxes[ap].get_attribute("name") # internal mode label, not corresponding to label next to text boxes <--- boxlabel
        ap_value = text_boxes[ap].get_attribute("value")
        if (("mode" in mode_name) or ("strain" in mode_name)) and (mode_name not in ['modeamplitude', 'strainamplitude']):
            mode_amplitudes.append(float(ap_value))
            mode_names.append(str(mode_name))
    

    paragraphs = driver.find_elements(By.TAG_NAME, 'p')
    mode_info_paragraphs : list = []
    results : dict = {}
    labels : dict = {}
    form_start = False
    for i,p in enumerate(paragraphs):
        textblock = p.text
        if textblock.startswith("Space Group:"):
            msg = "this is info on input structures" # first paragraph contains info on parent and child structures
            input_info = textblock.split("\n") 
        elif textblock.startswith("Subgroup:"): # second paragraph contains info on subgroup transformation
            msg = "this is the subgroup info"
            subgroup_info = textblock.split("\n") 
        elif textblock.startswith("Enter mode and strain amplitudes:"): # third paragraph signals the start of the form
            msg = "form starts here"
            form_start = True
        elif textblock.startswith("Parameters:"): # this paragraph follows the one that contains the last mode
            msg = "mode info stops here"
            form_start = False

        if DEBUG == True:
            if i == 0:
                print("")
            print(f"paragraph {i}: ({msg})") # print statement for debugging

        if form_start==True:
            mode_info_paragraphs.append(textblock.split("\n"))
    
    if not mode_info_paragraphs: # check if any modes were found
        warnings.warn("No modes found!")
        return None
    else:
        mode_info_paragraphs.pop(0) # remove the paragraph before mode info starts
        num_modes = len(mode_info_paragraphs)
        mode_info_paragraphs[-1].pop(-1) # remove last line in final mode paragraph ('Zero all mode and ...')
        mode_info_paragraphs = [list(filter(None,  l)) for l in mode_info_paragraphs] # remove any empty lines
        num_components = - num_modes 
        for i,m in enumerate(mode_info_paragraphs):
            num_components += len(m)
        if num_components != len(mode_amplitudes):
            warnings.warn("Number of A_p values read from text boxes does not match number of irrep component labels!")
            return None

    last_component : int = 0
    for mode in mode_info_paragraphs: # extract info on distortion modes
        info_line = mode[0] # paragraphs include line info for each irrep
        mode_components = mode[1:] # these are the labels displayed next to the textboxes
        last_component += len(mode_components)
        # first read irrep info from info_line
        parent_SG = info_line.split("[")[0]
        irrep_label = info_line.split()[0].split("]")[-1]
        child_SG = info_line.split()[3].replace(',','')
        child_SG_num = info_line.split()[2]
        opd = info_line.split()[1]
        info_out : dict = { # dict containing info for each irrep
                    'parent': parent_SG,
                     'child': child_SG+f" ({str(child_SG_num)})",
                     'OPD': opd
                    }
        # now extract the actual values
        components_out : dict = {}
        labels_out : dict = {}
        for i,j in enumerate(range(last_component-len(mode_components),last_component)): # map component labels to Ap values 
            components_out.update({
                mode_components[i] : mode_amplitudes[j]
                })
            labels_out.update({
                mode_components[i] : mode_names[j]
            })
        results.update({
            irrep_label : 
                {'info' : info_out,
                 'components' : components_out
                 }
                 })
        labels.update({
            irrep_label : labels_out
        })

    print("Done!")
    print(f"Found {num_modes} irreps ({', '.join(results.keys())}) and {num_components} components.")
    if DEBUG == True:
        pprint.pprint(results)
        pprint.pprint(labels)

    return (results, labels)

def generate_scaled_structures(num_steps : int, factors : list, target_modes : list[str], mode_amplitudes : dict, downloads : str, destination : str, driver, wait) -> None:
    '''uses create cif functionality on ISODISTORT to generate a range of structure files with scaled mode amplitudes and moves them to destination directory'''
    write_cif_button = driver.find_element(By.XPATH, "/html/body/div[2]/form/input[81]")
    OK_button_4 = driver.find_element(By.XPATH, "/html/body/div[2]/form/input[91]")
    text_boxes = driver.find_elements(By.CLASS_NAME, 'span1')
    print(f'Generating {num_steps} structures with scaled mode amplitudes...')
    for i in range(num_steps):
        if DEBUG: print(f"structure {i+1} (scaling factor: {factors[i]})")
        # block for filling in mode amplitude text boxes
        for ap in range(len(text_boxes)):
            mode_name = text_boxes[ap].get_attribute("name") # internal mode label, not corresponding to label next to text boxes <--- boxlabel
            for mode in target_modes:
                components : dict = mode_amplitudes[mode]['components']
                for comp in components.keys():
                    if 'strain' not in comp:
                        boxlabel = components[comp]['boxlabel']
                        if mode_name == boxlabel:
                            value = components[comp]['values'][i]
                            if DEBUG: print(f"filling in mode amplitudes for {mode}: {comp} (boxlabel: {boxlabel}) with value {value}")
                            text_boxes[ap].clear()
                            text_boxes[ap].send_keys(str(value))

        write_cif_button.click()
        print(f"Creating cif no. {i+1}/{num_steps}.")
        OK_button_4.click()
        driver.implicitly_wait(1) # third tab will open when file downloads
        wait.until(EC.number_of_windows_to_be(2)) # wait until third tab closes

        move_downloaded_file(downloads, destination, i, driver)

        return None

if __name__ == '__main__':
    print("")
    # read user input file
    infofile = get_usr_options()
    webdrv_path, main_page, walker_text, tags_bool, tags_other = read_usr_info(
        infofile,
        text_tags,
        option_tags_bool,
        option_tags_other
        )

    DEBUG = tags_bool['DEBUG']

    if DEBUG:
        # Read back input tags parsed from infofile
        print('INFO: debugging mode enabled.')
        print('required text tags:')
        pprint.pprint(walker_text)
        print('optional tags (boolean):')
        pprint.pprint(tags_bool)
        print('optional tags (other):')
        pprint.pprint(tags_other)


    if not tags_bool['READ_MODE']:
        # Set up webdriver and options
        driver, wait = webdriver_setup(tags_bool['WEBDRV_WINDOW'], webdrv_path)

        # load isodistort main page
        print('Opening ISODISTORT...', end="")
        driver.get(main_page)
        print('Done!')

        # upload parent structure file
        upload_parent_struct(walker_text['PARENT_FILE'], driver)

        # upload distorted structure file
        upload_child_struct(walker_text['DISTORTED_FILE'], driver, wait)

        # transform basis
        origin = tags_other['ORIGIN_SHIFT']
        if DEBUG and origin is not None: print(f'\norigin shifted by ({origin[0]})a + ({origin[1]})b + ({origin[2]})c')
        transform_basis(walker_text['BASIS_TRANSFORM'], origin, driver)

        # read A_p values and interal element names
        mode_amplitudes, box_labels = read_mode_amplitudes(driver)

        if tags_bool['WRITE_FILE']:
            save_to_file(mode_amplitudes)
            save_to_file(box_labels, filename='mode_labels')

        if tags_bool['WEBDRV_WINDOW']: # allow user to inspect window before closing
            print('Press enter to close all when done')
            input()

        driver.quit()

    elif tags_bool['READ_MODE']:
        # mode amplitudes are instead read from YAML file
        print('INFO: Read mode enabled.')
        mode_amplitudes = read_from_file('modeamplitudes.yaml')
        print('File read successfully.')

        if DEBUG: pprint.pprint(mode_amplitudes)
        box_labels = read_from_file('mode_labels.yaml')
        print('File read successfully.')
        if DEBUG: pprint.pprint(box_labels)

    if tags_bool['SCALEMODES']:
        # read input parameters
        factor_min : float = float(tags_other['SCALEMODES_MIN'])
        factor_max : float = float(tags_other['SCALEMODES_MAX'])
        num_steps : int = int(tags_other['SCALEMODES_STEPS'])
        downloads : str = tags_other['DOWNLOAD_DIR']
        destination : str = '/'.join(walker_text['DISTORTED_FILE'].split('/')[:-1]) # where to saved to structure files to

        # some sanity checks
        if factor_max < factor_min:
            raise AttributeError(f"Minimum scaling factor ({factor_min}) is larger than maximum scaling factor ({factor_max}).")
        
        if tags_other['SCALEMODES_LABELS'] is None:
            raise AttributeError("Scaling of modes was requested but no mode labels were provided!")
        else:
            target_modes : list[str] = tags_other['SCALEMODES_LABELS'].split()

        # create lists of scaled mode amplitudes
        factors = np.linspace(factor_min, factor_max, num_steps)
        scaled_modes : dict = {}
        for mode in target_modes:
            components : dict = mode_amplitudes[mode]['components']
            for key in components.keys():
                if 'strain' not in key: # NOT scaling strain mode amplitudes
                    value : float = components[key]
                    outputs : dict = {
                        'boxlabel' : box_labels[mode][key],
                        'values' : list(factors * value)
                    }
                    components[key] = outputs # create range of mode amplitudes
            # replace labels with internal text box labels
            scaled_modes.update({mode : {
                'components' : components,
                'info' : mode_amplitudes[mode]['info']}})

        if DEBUG: 
            print('scaled mode amplitudes:')
            pprint.pprint(scaled_modes)
        # TODO fix writing dict containing lists to file
        #save_to_file(scaled_modes,filename='scaled_modes')

        # Set up webdriver and options
        driver, wait = webdriver_setup(tags_bool['WEBDRV_WINDOW'], webdrv_path)

        # load isodistort main page
        print('Opening ISODISTORT...', end="")
        driver.get(main_page)
        print('Done!')

        # upload parent structure file
        upload_parent_struct(walker_text['PARENT_FILE'], driver)

        # upload distorted structure file
        upload_child_struct(walker_text['DISTORTED_FILE'], driver, wait)

        # transform basis
        transform_basis(walker_text['BASIS_TRANSFORM'], driver)

        # create CIF's with scaled mode amplitudes
        generate_scaled_structures(num_steps, factors, target_modes, mode_amplitudes, downloads, destination, driver, wait)

        if tags_bool['WEBDRV_WINDOW']: # allow user to inspect window before closing
            print('Press enter to close all when done')
            input()

        driver.quit()

    print('All Done!')

