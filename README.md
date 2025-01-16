# AUTOMATE_ISODISTORT

This python code interfaces with [ISODISTORT](https://stokes.byu.edu/iso/isodistort.php) from the ISOTROPY sofware suite [[1]](#1), specifically the symmetry-mode decomposition of a distorted structure (Method 4). Given a pair of parent and child structure files in the CIF format this code can be used to extract mode amplitudes associated with the irreducible representations for further analysis, and to create multiple distorted structures with linearly scaled mode amplitudes.

Usage
----
All control parameters are handled using a separate input file, and the script can run by 
```
python find_modes.py <input-file>
```
The actual name of the input file does not matter. An example input file `inputs.info` is provided. \
\
Note that parend and distorted structure CIF's need to be symmetrised (e.g. using [FINDSYM](https://stokes.byu.edu/iso/findsym.php) from the ISOTROPY suite). This code has some limited built-in exception handling related to errors occuring in ISODISTORT, but it is safer to first do a 'manual' test e.g. to determine the correct basis transformation matrix (see below).\
\
The distortion mode amplitudes are internally stored as a Python dictionary and can (optionally) be written to a file in the `.yaml` format. This allows the values to be accessed easily using e.g. Python such as:
```python
import os
from pathlib import Path
import yaml

def read_from_file(name : str) -> dict:
    '''reading mode amplitude as dict from YAML file'''
    if not os.path.isfile(f'{name}'): # Check if file exists
        raise FileNotFoundError(f'file {name} could not be found')
    else:   
        data : dict = yaml.safe_load(Path(name).read_text())
        print(f'reading data from file {name}')
        return data

# Read in file as a dict
mode_amplitudes_dict = read_from_file('modeamplitudes.yaml')

# The actual mode amplitudes are stored as a dict under the key 'components'
GM1p_mode : dict = mode_amplitudes_dict['components']

# This also contains some extra information on each irrep such as OPD, parent and child space groups
GM1p_info : dict = mode_amplitudes_dict['info']

# Individual components can be accessed using the ISODISTORT mode labels as key
GM1p_Al_A1 : float = GMp_mode['[Ca1:i:dsp]A''_1(a)']
```
System Requirements
-------
In addition to [Python 3](https://www.python.org/) (tested with v3.10.8) the following packages need to be installed:

* [Selenium](https://selenium-python.readthedocs.io/) version 4.15.2
* [Numpy](https://numpy.org/) version 1.25.2

Other versions might still work but have not been tested.

Input tags
-----------
All input tags should be provided in the input file file separated by colons: 
```
<TAG-NAME> : <VALUE>
```
 All tag names are case-insensitive. Tags which require a boolean value accept either `True`, `true`, `T`, `t` etc. or `False`, `F` etc. \
 Each tag has to be specified on a new line and the order of tags in the input file does not matter.
\
\
`WEBDRIVER_PATH` (**required**): \
Path to directory where the webdriver is located. \
\
`MAIN_PAGE` (**required**, *should not need to be changed*): \
URL to ISODISTORT main page. \
\
`PARENT_FILE` (**required**): \
Path to parent structure CIF (obviously including filename). Can be absolute path or relative path. \
\
`DISTORTED_FILE` (**required**): \
Path to distorted (child) structure CIF (obviously including filename). Can be absolute path or relative path. \
\
`BASIS_TRANSFORM` (**required**): \
Basis transformation matrix **P** that relates the child basis vectors to the parent ones via $(a',b',c')^T=\textbf{P}(a,b,c)^T$. The matrix elements should be provided separated by spaces, e.g.: 
``` 
BASIS_TRANSFORM : 1 0 0 0 1 0 0 0 -1
```
 where the elements should be specified in order $P_{11}$ $P_{12}$ $P_{13}$ $P_{21}$  $P_{22}$  $P_{23}$  $P_{31}$ $P_{32}$ $P_{33}$ and separated by spaces. \
\
`WRITE_FILE` (**optional**, *boolean*, default: False): \
Write distortion mode output to a `.yaml` file. Existing files will not be overwritten, instead the new filename will be appended with a number. \
\
`READ_MODE` (**optional**, *boolean*, default: True): \
Whether to read distortion mode amplitudes from a previously written `.yaml` file. By default the file with the name `modeamplitudes.yaml` will be read. \
\
`DEBUG` (**optional**, *boolean*, default: False): \
Write additional outputs to terminal for debugging purposes. \
\
`WEBDRV_WINDOW` (**optional**, *boolean*, default: False): \
Whether to open the browser window when reading data from ISODISTORT (for debugging purposes mainly). \
\
`SCALEMODES` (**optional**, *boolean*, default: False): \
Turn on the method for creating a range of structures with scaled mode amplitudes. This will also create a `.yaml` file\
\
`SCALEMODES_LABELS` (**required if** `SCALEMODES==True`): \
Mode labels of modes to be scaled as they appear on ISODISTORT, e.g. GM2- will scale all components of the $\Gamma_2^-$ irrep except for the strain mode amplitudes, unless explicitely specified (see below). Scaling multiple irreps simultaneously is allowed, the labels should be separated by space. \
\
`SCALEMODES_MIN` (**optional**, default: 0): \
Minimum multiplicative factor for scaling the mode amplitudes, in terms of the value in the original child structure. Negative values and non-integers are allowed.\
\
`SCALEMODES_MAX` (**optional**, default: 1): \
Maximum multiplicative factor for scaling the mode amplitudes, in terms of the value in the original child structure. \
\
`SCALEMODES_STEPS` (**optional**, default: 5): \
Integer number of distorted structures to create. Mode amplitudes will be scaled linearly between `SCALEMODES_MIN` and `SCALEMODES_MAX`. \
\
`DOWNLOAD_DIR` (**optional**, default: `~/Downloads/`): \
Full (absolute) path to the system downloads directory. Structure files created by and downloaded from ISODISTORT will be moved from this directory to the same directory where the child structure file is located.\
\
`SCALE_STRAINS`: Not yet implemented


## References
<a id="1">[1]</a>
H. T. Stokes, D. M. Hatch, and B. J. Campbell, ISOTROPY Software Suite, iso.byu.edu. (https://stokes.byu.edu/iso/isotropy.php)
