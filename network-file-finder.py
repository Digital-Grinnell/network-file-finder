# network-file-finder.py
##
## This script is designed to read all of filenames from a specified --column of a specified
## --worksheet Google Sheet and fuzzy match with files found in a specified --tree-path 
## network storage directory tree.

import sys
import getopt
import re
import gspread as gs
import csv
import os.path
from fuzzywuzzy import fuzz, process

# Local packages
import my_colorama

# --- Function definitions


def extract_sheet_id_from_url(url):
  res = re.compile(r'#gid=([0-9]+)').search(url)
  if res:
    return res.group(1)
  raise Exception('No valid sheet ID found in the specified Google Sheet.')


def check_significant(regex, filename):
  import re

  if '(' in regex:             # regex already has a (group), do not add one
    pattern = regex
  else: 
    pattern = f"({regex})"     # regex is raw, add a (group) pair of parenthesis

  try:
    match = re.search(pattern, filename) 
    if match:
      return match.group( )
    else:
      return False
  except Exception as e:
    assert False, f"Exception: {e}"  


def build_lists_and_dict(significant, target, files_list, paths_list):
  significant_file_list = []
  significant_path_list = [] 
  significant_match = False
  is_significant = "*"

  # If a --regex (significant) was specified see if our target has a matching component...
  if significant:
    significant_match = check_significant(significant, target)
    if significant_match:   # ...it does, pare the significant_*_list down to only significant matches
      for i, f in enumerate(files_list): 
        is_significant = check_significant(significant_match, f)
        if is_significant:
          significant_file_list.append(f)
          significant_path_list.append(paths_list[i])
  
  # If there's no significant_match... make the output lists match the input lists
  if not significant_match:
    significant_file_list = files_list
    significant_path_list = paths_list 

  # Now, per https://github.com/seatgeek/fuzzywuzzy/issues/165 build an indexed dict of significant files
  file_dict = {idx: el for idx, el in enumerate(significant_file_list)}

  # Return a tuple of significant match and the three significant lists
  return (significant_match, significant_file_list, significant_path_list, file_dict)    


# --- Main

if __name__ == '__main__':

  # --- Arg handling
  # arg handling per https://www.tutorialspoint.com/python/python_command_line_arguments.htm
  
  my_colorama.blue(f"\nNumber of arguments: {len(sys.argv[1:])}")
  my_colorama.blue(f"Argument List:' {str(sys.argv[1:])}\n")

  args = sys.argv[1:]
  output_to_csv = False

  try:
    opts, args = getopt.getopt(args, 'hokw:c:t:r:s:', ["help", "output-csv", "kept-file-list", "worksheet=", "column=", "tree-path=", "regex=", "skip-rows="])
  except getopt.GetoptError:
    my_colorama.yellow("python3 network-file-finder.py --help --output-csv --kept-file-list --worksheet <worksheet URL> --column <worksheet filename column> --tree-path <network tree path> --regex <significant regex> \n")
    sys.exit(2)

  # Default column for filenames is 'G' = 7 and number of header rows to skip = 1
  column = 7
  levehstein_ratio = 90
  skip_rows = 1
  significant = False
  kept_file_list = False

  # Process the command line arguments
  for opt, arg in opts:
    if opt in ("-h", "--help"):
      my_colorama.yellow("python3 network-file-finder.py --help --output-csv --keep-file-list --worksheet <worksheet URL> --column <filename column> --tree-path <network tree path> --regex <significant regex> --skip-rows <number of header rows to skip>\n")
      sys.exit( )
    elif opt in ("-w", "--worksheet"):
      sheet = arg
    # elif opt in ("-f", "--fuzzy-score"):
    #   try:
    #     val = int(arg)
    #     if val >= 0 and val <= 100:
    #       levehstein_ratio = val
    #       break
    #     else:
    #       assert False, "Unhandled option: Fuzzy score must be an integer between 0 and 100."
    #   except ValueError:
    #     assert False, "Unhandled option: Fuzzy score must be an integer between 0 and 100."
    elif opt in ("-c", "--column"):
      if arg.isalpha() and arg.isupper():
        column = str(ord(arg)-64)
      else:
        my_colorama.red("Unhandled option: Column must be a single uppercase character from A through Z.")
        exit( )
    elif opt in ("-t", "--tree-path"):
      path = arg
    elif opt in ("-r", "--regex"):
      significant = arg
    elif opt in ("-s", "--skip-rows"):
      try:
        val = int(arg)
        if val >= 0:
          skip_rows = val
        else:
          my_colorama.red("Unhandled option: Number of rows to skip must be an integer >= 0.")
          exit( )
      except ValueError:
        my_colorama.red("Unhandled option: Number of rows to skip must be an integer >= 0")
        exit( )
    elif opt in ("-o", "--output-csv"):
      output_to_csv = True
    elif opt in ("-k", "--kept-file-list"):
      kept_file_list = True
    else:
      my_colorama.red("Unhandled command line option")
      exit( )

  # Create an empty list of filenames    
  filenames = [ ]

  # Check the kept_file_list switch.  If it is True then attempt to open the file-list.tmp file 
  # saved from a previous run.  The intent is to cut-down on Google API calls.
  if kept_file_list:
    try:
      with open('file-list.tmp', 'r') as file_list:
        for filename in file_list:
          filenames.append(filename.strip( ))
    except Exception as e:
      kept_file_list = False
      pass  

  # If we don't have a kept file list... Open the Google service account and sheet
  if not kept_file_list:
    try:
      sa = gs.service_account()
    except Exception as e:
      my_colorama.red(e)
    
    try:
      sh = sa.open_by_url(sheet)
    except Exception as e:
      my_colorama.red(e)
  
    gid = int(extract_sheet_id_from_url(sheet))
    worksheets = sh.worksheets()
    worksheet = [w for w in sh.worksheets() if w.id == gid]
    
    # Grab all filenames from --column 
    filenames = worksheet[0].col_values(column)  
    try:
      with open('file-list.tmp', 'w') as file_list:
        for filename in filenames:
          file_list.write(f"{filename}\n")
    except Exception as e:
      my_colorama.red("Unable to open temporary file 'file-list.tmp' for writing.")
      exit( )

  # Grab all non-hidden filenames from the target directory tree so we only have to get the list once
  # Exclusion of dot files per https://stackoverflow.com/questions/13454164/os-walk-without-hidden-folders
  big_file_list = [ ]   # need a list of just filenames...
  big_path_list = [ ]   # ...and parallel list of just the paths
  significant_file_list = [ ]
  significant_path_list = [ ] 
  significant_dict = { }

  for root, dirs, files in os.walk(path):
    files = [f for f in files if not f[0] == '.']
    dirs[:] = [d for d in dirs if not d[0] == '.']
    for filename in files:
      big_path_list.append(root)
      big_file_list.append(filename)

  # Check for ZERO network files in the big_file_list
  if len(big_file_list) == 0:
    my_colorama.red(f"The specified --tree-path of '{path}' returned NO files!  Check your path specification and network connection!\n")
    exit( )

  # Report our --regex option...
  if significant:
    my_colorama.green(f"\nProcessing only files matching signifcant --regex of '{significant}'!")
  else:
    my_colorama.green(f"\nNo --regex specified, matching will consider ALL paths and files.")

  counter = 0
  csvlines = [ ]

  # Now the main matching loop...
  for x in range(len(filenames)):
    if x < skip_rows:  # skip this row if instructed to do so 
      my_colorama.yellow(f"Skipping match for '{filenames[x]}' in worksheet row {x}")
      continue         # move on and process the next row
    
    counter += 1
    target = filenames[x]
    my_colorama.green(f"\n{counter}. Finding best fuzzy filename matches for '{target}'...")
    csv_line = [ ]  
    significant_text = ''

    (significant_text, significant_file_list, significant_path_list, significant_dict) = build_lists_and_dict(significant, target, big_file_list, big_path_list)    
    if significant_text:
      my_colorama.blue(f"  Significant string is: '{significant_text}'.")
    else: 
      my_colorama.blue(f"  No significant --regex limit specified.")  

    matches = process.extract(filenames[x], significant_dict, limit=3)
    csv_line.append(f"{counter}")
    csv_line.append(target)
    csv_line.append(significant_text)

    # Report the top three matches
    if matches:
      for found, (match, score, index) in enumerate(matches):
        path = significant_path_list[index]
        csv_line.append(f"{score}")
        csv_line.append(match)
        csv_line.append(path)
        if found==0: 
          # txt = ' | '.join(csv_line)
          my_colorama.green("!!! Found BEST matching file: {}".format(csv_line))

    else:
      csv_line.append('0')
      csv_line.append('NO match')
      csv_line.append('NO match')
      my_colorama.red("*** Found NO match for: {}".format(' | '.join(csv_line)))

    if output_to_csv:
      csvlines.append(csv_line)

# If -output-csv is true, open a .csv file to receive the matching filenames and add a heading
if output_to_csv:
  with open('match-list.csv', 'w', newline='') as csvfile:
    listwriter = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)

    if significant:
      significant_header = f"'{significant}' Match"
    else:  
      significant_header = "Undefined"

    header = ['No.', 'Target', 'Significant --regex', 'Best Match Score', 'Best Match', 'Best Match Path', '2nd Match Score', '2nd Match', '2nd Match Path', '3rd Match Score', '3rd Match', '3rd Match Path']
    listwriter.writerow(header)

    for line in csvlines:
      listwriter.writerow(line)