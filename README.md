# AUTOMATE_ISODISTORT

All control parameters are handled using a separate input file, and the script can run by 
```
python find_modes.py <input-file>
```
The actual name of the input file does not matter. An example input file `inputs.info` is provided.

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
`SCALEMODES_LABELS` (**required if** `SCALEMODES==True`, default: None): \
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
`DOWNLOAD_DIR` (**required if** `SCALEMODES==True`, default: `~/Downloads/`): \
Full (absolute) path to the system downloads directory. \
\
`SCALE_STRAINS`: Not yet implemented



