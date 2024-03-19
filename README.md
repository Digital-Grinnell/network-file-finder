# Network File Finder

A Python script designed to recursively "find" a list of files in network storage.  The list of files will be a range of cells from the specified column of a specified Google Sheet.  If an exact match can't be found, a "fuzzy" search is initiated to look for any matching filenames, but with a wildcard in place of the original extension.  The effect can be seen in the sample output from a "fuzzy" result shown below.  

```
Finding a filename match for '/Volumes/DGIngest/Reunion/**/grinnell-26849.jpg'...
  NONE FOUND! Starting 'fuzzy' search for: '/Volumes/DGIngest/Reunion/**/grinnell-26849.*'...
  ****************************************************************************************** 
    NOPE, could not even find a FUZZY match! 
```

---

## Python

See [Proper Python](https://blog.summittdweller.com/posts/2022/09/proper-python/) for applicable guidance when enabling Python parts of this workflow.    

### Quick Start

```bash
╭─mcfatem@MAC02FK0XXQ05Q ~/GitHub/network-file-finder ‹main› 
╰─$ git pull
Already up to date.
╭─mcfatem@MAC02FK0XXQ05Q ~/GitHub/network-file-finder ‹main› 
╰─$ python3 -m venv .venv
╭─mcfatem@MAC02FK0XXQ05Q ~/GitHub/network-file-finder ‹main●› 
╰─$ source .venv/bin/activate
(.venv) ╭─mcfatem@MAC02FK0XXQ05Q ~/GitHub/network-file-finder ‹main●› 
╰─$ pip3 install -r python-requirements.txt
```

Then...  

```zsh
(.venv) ╭─mcfatem@MAC02FK0XXQ05Q ~/GitHub/network-file-finder ‹main●› 
╰─$ python3 network-file-finder.py --column A --worksheet https://docs.google.com/spreadsheets/d/17uNXLP5aTSCfYZ8FXBqTvDd-z0F19FJeAOK5TsCr-PI/edit\#gid\=750240076 --tree-path /Volumes/exports/ --output-csv
```

---

## Use

Runing `python3 network-file-finder.py --help` in the project directory generates this "help" guidance:  

```zsh
Number of arguments: 1
Argument List:' ['--help']

python3 network-file-finder.py --help --output-csv --keep-file-list --worksheet <worksheet URL> --column <filename column> --tree-path <network tree path> --regex <significant regex> --skip-rows <number of header rows to skip>
```

Note: Do NOT add a slash to the end of the `--tree-path`!

### --output-csv  

Specifying this optional argument sets `show = True` causing the script to open/create a `match-list.csv` output file which will include a shorthand summary of each filename match outcome. 

### -c or --column

Specifying this optional argument sets `column` equal to the specified value causing the script to read target filenames from the corresponding column of the Google Sheet.  `column` defaults to `G` (typically the `OBJ` column) if not specifed.  If specified, `-c` or `--column` must be a single uppercase letter A through Z.  

## Sample

```zsh
(.venv) ╭─mcfatem@MAC02FK0XXQ05Q ~/GitHub/network-file-finder ‹main●› 
╰─$ python3 network-file-finder.py --column A --worksheet https://docs.google.com/spreadsheets/d/17uNXLP5aTSCfYZ8FXBqTvDd-z0F19FJeAOK5TsCr-PI/edit\#gid\=750240076 --tree-path /Volumes/exports/ --output-csv
/Users/mcfatem/GitHub/network-file-finder/.venv/lib/python3.10/site-packages/fuzzywuzzy/fuzz.py:11: UserWarning: Using slow pure-python SequenceMatcher. Install python-Levenshtein to remove this warning
  warnings.warn('Using slow pure-python SequenceMatcher. Install python-Levenshtein to remove this warning')

Number of arguments: 7
Argument List:' ['--column', 'A', '--worksheet', 'https://docs.google.com/spreadsheets/d/17uNXLP5aTSCfYZ8FXBqTvDd-z0F19FJeAOK5TsCr-PI/edit#gid=750240076', '--tree-path', '/Volumes/exports/', '--output-csv']


No --regex specified, matching will consider ALL paths and files.
Skipping match for 'objectid' in worksheet row 0

1. Finding best fuzzy filename matches for 'grinnell_3601_OBJ'...
  No significant --regex limit specified.
!!! Found BEST matching file: ['1', 'grinnell_3601_OBJ', False, '95', 'grinnell_3601_OBJ.tiff', '/Volumes/exports/college-life/OBJ']

2. Finding best fuzzy filename matches for 'grinnell_3611_OBJ'...
  No significant --regex limit specified.
!!! Found BEST matching file: ['2', 'grinnell_3611_OBJ', False, '95', 'grinnell_3611_OBJ.tiff', '/Volumes/exports/college-life/OBJ']

3. Finding best fuzzy filename matches for 'grinnell_3610_OBJ'...
  No significant --regex limit specified.
!!! Found BEST matching file: ['3', 'grinnell_3610_OBJ', False, '95', 'grinnell_3610_OBJ.tiff', '/Volumes/exports/college-life/OBJ']
...
```  