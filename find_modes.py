from selenium import webdriver
#from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import os
import glob
from pymatgen.io.vasp.inputs import Poscar
from pymatgen.core import Structure
from pymatgen.core.periodic_table import Species
import numpy as np
import pprint

main_page = "https://stokes.byu.edu/iso/isodistort.php"
parent_structure_file = '/Users/shmr69/Documents/Brownmillerites/Ca2FeAlO5/switching/Ca2FeAlO5_Imma.cif'
child_structure_file = '/Users/shmr69/Documents/Brownmillerites/Ca2FeAlO5/switching/CONTCAR_Ima2_unstrained_sym.cif'
# TODO find matrix automatically using pymatgen
basis_transformation = np.array(
    [[1, 0, 0],
    [0, 0, -1],
    [0, 1, 0]]
)
DEBUG = True


def wait_for_page_load(element, driver, timeout = 10) -> None:
    #time.sleep(1)
    try:
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.element_to_be_clickable((By.XPATH, element)))
        #print(f"new page has loaded: {driver.current_url}")
    except TimeoutException:
        print("Timed out waiting for page to load")
        driver.quit()
    except NoSuchElementException:
        print("Could not loacate specified element")
        driver.quit()
    return None

def upload_parent_struct(parent_struct, driver) -> None:
    print('uploading parent structure file...', end="")
    upload_parent_button = driver.find_element(By.XPATH, "/html/body/div[2]/div[1]/ul/form/input[3]")
    upload_parent_button.send_keys(parent_struct) # upload parent file on first page
    wait_for_page_load('/html/body/div[2]/div[1]/ul/form/input[2]', driver) # wait for OK button to be clickable
    OK_button_1 = driver.find_element(By.XPATH, "/html/body/div[2]/div[1]/ul/form/input[2]")
    OK_button_1.click() #click OK on first page
    wait_for_page_load('/html/body/div[2]/div[5]/form/h3/input', driver) # wait for child upload OK button to be clickable
    print("Done!")
    return None

def upload_child_struct(child_struct, driver, wait) -> None:
    print('uploading child structure file...', end="")
    upload_child_button = driver.find_element(By.XPATH, '/html/body/div[2]/div[5]/form/p/input[67]')
    upload_child_button.send_keys(child_struct) # upload child file on first page 
    OK_button_2 = driver.find_element(By.XPATH, "/html/body/div[2]/div[5]/form/h3/input")
    OK_button_2.click() # click OK on second page
    wait.until(EC.number_of_windows_to_be(2)) # wait until second tab opens
    driver.switch_to.window(driver.window_handles[1]) # switch to second tab
    wait_for_page_load("/html/body/div[2]/form/p[1]/input", driver) # wait for OK button on basis transformation page to load
    print("Done!")

def transform_basis(transformation_matrix, driver) -> None:
    matrix = np.asarray(transformation_matrix.flatten(), dtype=str) # convert transformation matrix to 1D array of strings
    print('transforming basis...', end="")
    specify_basis_button = driver.find_element(By.XPATH, "/html/body/div[2]/form/input[71]")
    specify_basis_button.click() # click 'specify basis as' on third page
    OK_button_3 = driver.find_element(By.XPATH, "/html/body/div[2]/form/p[1]/input")

    # fill basis transformation matrix
    for i,el in enumerate(range(72,81)):
        basis_element = driver.find_element(By.XPATH, f"/html/body/div[2]/form/input[{el}]") # textbox for matrix element in basis transformation matrix
        basis_element.clear()
        basis_element.send_keys(matrix[i])

    OK_button_3.click() # click OK on third page
    wait_for_page_load('/html/body/div[2]/form/input[91]', driver)
    print("Done!")
    return None

def read_mode_amplitudes(driver) -> dict:
    print('reading mode amplitudes...', end="")
    text_boxes = driver.find_elements(By.CLASS_NAME, 'span1')
    mode_amplitudes_list = []
    for ap in range(len(text_boxes)):
        mode_name = text_boxes[ap].get_attribute("name")
        ap_value = text_boxes[ap].get_attribute("value")
        if (("mode" in mode_name) or ("strain" in mode_name)) and (mode_name not in ['modeamplitude', 'strainamplitude']):
            mode_amplitudes_list.append(float(ap_value))
    

    paragraphs = driver.find_elements(By.TAG_NAME, 'p')
    mode_info_paragraphs = []
    mode_info_dict = {}
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
            print(f"paragraph {i} ({msg})") # print statement for debugging

        if form_start==True:
            mode_info_paragraphs.append(textblock.split("\n"))
    
    if not mode_info_paragraphs: # check if any modes were found
        print("WARNING: No modes found!")
        return None
    else:
        mode_info_paragraphs.pop(0) # remove the paragraph before mode info starts
        num_modes = len(mode_info_paragraphs)
        mode_info_paragraphs[-1].pop(-1) # remove last line in final mode paragraph ('Zero all mode and ...')
        mode_info_paragraphs = [list(filter(None,  l)) for l in mode_info_paragraphs] # remove any empty lines
        num_components = - num_modes 
        for i,m in enumerate(mode_info_paragraphs):
            num_components += len(m)

    num_components = 0
    for mode in mode_info_paragraphs: # extract info on distortion modes
        info_line = mode[0] # paragraphs include line info for each irrep
        mode_components = mode[1:]
        num_components += len(mode_components)
        parent_SG = info_line.split("[")[0]
        irrep_label = info_line.split()[0].split("]")[-1]
        child_SG = info_line.split()[3].replace(',','')
        child_SG_num = info_line.split()[2]
        OPD = info_line.split()[1]
        info_dict = { # dict containing info for each irrep
                    'parent': parent_SG,
                     'child': child_SG+f" ({str(child_SG_num)})",
                     'OPD': OPD
                    }
        
        components_dict = {}
        for i,j in enumerate(range(num_components-len(mode_components),num_components)): # map component labels to Ap values 
            components_dict.update({
                mode_components[i] : mode_amplitudes_list[j]
                })
        mode_info_dict.update({
            irrep_label : 
                {'info:' : info_dict,
                 'components:' : components_dict
                 }
                 })

    print("Done!")
    print(f"found {num_modes} distortion modes and {num_components} components.")
    if DEBUG == True:
        pprint.pprint(mode_info_dict)
    return mode_info_dict


if __name__ == '__main__':
    # Set up webdriver and options
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless=new") # don't open window
    options.add_argument("--start-maximized")
    options.add_argument("--remote-allow-origins=*")
    options.add_experimental_option("detach", True)  # Keep the window open
    driver = webdriver.Chrome(
        #service=Service(ChromeDriverManager().install()), # optional: install Chrome driver if not present
        #service=Service(webdrv_path), # optional: look for Chrome driver at specific location
        options=options
        )
    # Set up webdriver waiting function
    wait = WebDriverWait(
        driver, 
        10 # default timeout
        )


    # load isodistort main page
    driver.get(main_page)

    # upload parent structure file
    upload_parent_struct(parent_structure_file, driver)

    # upload distorted structure file
    upload_child_struct(child_structure_file, driver, wait)

    # transform basis
    transform_basis(basis_transformation, driver)

    # read A_p values and interal element names
    mode_amplitudes = read_mode_amplitudes(driver)
    #print(mode_amplitudes)


    print('Press enter to close all when done')
    input()
    driver.quit()