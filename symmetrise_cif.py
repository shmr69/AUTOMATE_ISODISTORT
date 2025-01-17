from selenium import webdriver # type: ignore
from selenium.webdriver.support.ui import WebDriverWait # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException # type: ignore
from selenium.webdriver.common.by import By # type: ignore
import os
from pathlib import Path
import time
import glob
import warnings

def file_check(filepath) -> str:
    '''check if file is existent and if path is absolute, return full path if provided path is relative'''
    if not os.path.isfile(filepath): # check if files exists
        raise FileNotFoundError(f"The file {filepath.split('/')[-1]} could not be found.")
    elif Path(filepath).is_absolute():
        path = filepath
    else:
        path = os.path.abspath(filepath)
    return path

def move_downloaded_file(downloads_dir : str, destination: str, name : str, driver, wait_time : float = 5.0) -> None:
    # moving and renaming downloaded file
    time.sleep(wait_time) # wait until file has downloaded
    # look for the latest file in the Downloads directory
    if not os.path.isdir(os.path.expanduser(downloads_dir)):
        driver.quit()
        raise IOError(f"The Downloads directory could not be found at {os.path.expanduser(downloads_dir)}")
    list_of_files = glob.glob(os.path.expanduser(downloads_dir) + "*")
    latest_file = max(list_of_files, key = os.path.getctime)
    suffix = '_sym.cif'
    filepath = destination+name+suffix
    if os.path.isfile(filepath): # check if file exists
        warnings.warn(f'A file with the name {name+suffix} already exists in this directory.')
        while True:
            answer = input(f"\n Continue moving {latest_file} and overwrite existing file? (y/n) ")
            if answer.lower() in ["y","yes"]:
                os.rename(latest_file,filepath)
                break
            elif answer.lower() in ["n","no"]:
                driver.quit()
                raise FileExistsError(f'A file with the name {name+suffix} already exists.')
            else:
                print('invalid input')
                continue
    else: os.rename(latest_file,filepath)
    return None

def webdriver_setup(webdrv_win : bool, webdrv_path : str)  -> None:
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
    except TimeoutException:
        print("Timed out waiting for page to load")
        driver.quit()
    except NoSuchElementException:
        print("Could not loacate specified element")
        driver.quit()
    except WebDriverException:
        print('web driver error has occurred.')
        driver.quit()
    return None

def upload_struct(struct : str, driver) -> None:
    '''uploads parent structure file to main page'''
    filepath = file_check(struct)
    print('Uploading structure file...', end="")
    upload_struct_button = driver.find_element(By.XPATH, "/html/body/div[2]/div[1]/form/input[3]")
    upload_struct_button.send_keys(filepath) # upload parent file on first page
    wait_for_page_load('/html/body/div[2]/div[1]/form/input[2]', driver) # wait for 'OK' button to be clickable
    OK_button = driver.find_element(By.XPATH, "/html/body/div[2]/div[1]/form/input[2]")
    OK_button.click() #click OK on first page
    wait_for_page_load('/html/body/form[1]/input[3]', driver) # wait for 'download cif' button to be clickable
    print("Done!")
    return None

def symmetrise_using_findsym(structure_file_path : str, downloads_dir : str, driver, download_waiting_time : float = 2.0) -> None:
    '''wrapper function for automating the findsym workflow'''

    destination : str = '/'.join(structure_file_path.split('/')[:-1])+'/' # get full path of directory
    str_name : str = '.'.join(structure_file_path.split('/')[-1].split('.')[:-1]) # get file name without file extension

    # load findsym main page
    main_page = 'https://stokes.byu.edu/iso/findsym.php'
    print('Opening FINDSYM...', end="")
    driver.get(main_page)
    print('Done!')

    upload_struct(structure_file_path, driver)

    print('Downloading CIF...', end="")
    download_cif_button = driver.find_element(By.XPATH, "/html/body/form[1]/input[3]")
    download_cif_button.click()
    driver.implicitly_wait(download_waiting_time) # third tab will open when file downloads
    print('Done!')

    print('Moving symmetrised CIF to destination...', end="")
    move_downloaded_file(downloads_dir,destination,str_name,driver)
    print('Done!')

    driver.quit()

    return None


downloads : str = "/Users/shmr69/Downloads/"
webdriver_path : str = '/Users/shmr69/Documents/python_stuff/chromedriver-mac-x64'

# symmetrise single CIF:

# driver, wait = webdriver_setup(webdrv_win=False, webdrv_path=webdriver_path)
# struct_file : str = "/Users/shmr69/Documents/Brownmillerites/Ca2FeAlO5/QE/photorelax/Ima2/POSCAR_0.05e.cif"
# symmetrise_using_findsym(struct_file, downloads, driver)


# loop over multiple CIF's:

for i in range(1,9):

    driver, wait = webdriver_setup(webdrv_win=False, webdrv_path=webdriver_path)

    id : float = float(f"{i*0.05:.2f}")
    struct_file : str = f"/Users/shmr69/Documents/Brownmillerites/Ca2FeAlO5/QE/photorelax/Ima2/POSCAR_{str(id)}e.cif"

    print(f"symmetrising file no. {i}")
    symmetrise_using_findsym(struct_file, downloads, driver)

