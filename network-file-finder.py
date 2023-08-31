# network-file-finder.py
##
## This script is designed to read all of filenames from column 'A' of a specified Google Sheets 'worksheet', and "glob" for matching files in a specified network storage directory tree.

import sys
import getopt
import re
import gspread as gs
import glob
import csv
import os.path

# import os
# import pathlib
# from datetime import datetime
# from queue import Empty
# from typing import Dict

# --- Function definitions

def extract_sheet_id_from_url(url):
  res = re.compile(r'#gid=([0-9]+)').search(url)
  if res:
    return res.group(1)
  raise Exception('No valid sheet ID found in the specified Google Sheet.')

def make_fuzzy_filename(pattern):
  f = pattern
  dot = f.rfind('.')
  if dot:
    f = pattern[:dot+1] + '*'
  return f
  
# --- Main

if __name__ == '__main__':

  # --- Arg handling
  # arg handling per https://www.tutorialspoint.com/python/python_command_line_arguments.htm
  
  print('\nNumber of arguments:', len(sys.argv[1:]))
  print('Argument List:', str(sys.argv[1:]), "\n")

  args = sys.argv[1:]
  show = False

  try:
    opts, args = getopt.getopt(args, 'hsw:t:', ["help", "worksheet=", "tree-path="])
  except getopt.GetoptError:
    print("python3 network-file-finder.py --help --worksheet <worksheet URL> --tree-path <network tree path> --show-matches\n")
    sys.exit(2)

  for opt, arg in opts:
    if opt in ("-h", "--help"):
      print("python3 network-file-finder.py --help --worksheet <worksheet URL> --tree-path <network tree path>\n")
      sys.exit( )
    elif opt in ("-w", "--worksheet"):
      sheet = arg
    elif opt in ("-t", "--tree-path"):
      path = arg
    elif opt in ("-s", "--show-matches"):
      show = True
    else:
      assert False, "Unhandled option"

  # Open the Google service account and sheet
  try:
    sa = gs.service_account()
  except Exception as e:
    print(e)
    
  try:
    sh = sa.open_by_url(sheet)
  except Exception as e:
    print(e)
  
  gid = int(extract_sheet_id_from_url(sheet))
  worksheets = sh.worksheets()
  worksheet = [w for w in sh.worksheets() if w.id == gid]

  # If -show-matches is true, open a .csv file to receive the matching filenames
  if show:
    csvfile = open('match-list.csv', 'w', newline='')
    listwriter = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)

  # Grab all filenames from column 'A' and begin glob loop
  counter = 0
  filenames = worksheet[0].col_values(1)  
  for x in range(len(filenames)):
    counter += 1
    pattern = path + "/**/" + filenames[x]
    print("\n{}. Finding a filename match for '{}'...".format(counter, pattern))
    found = glob.glob(pattern, recursive=True)
    if found:
      print("  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
      print("  Found! List of matching files: '{}'".format(found))
      if show:
        line = "Found exact match for: {}".format(found[0])
        listwriter.writerow([line])
    else:
      fuzzy = make_fuzzy_filename(pattern)
      print("  NONE FOUND! Starting 'fuzzy' search for: '{}'...".format(fuzzy) )
      found = glob.glob(fuzzy, recursive=True)
      if found:
        print("  Found! List of 'fuzzy' matching files: '{}'".format(found))
        if show:
          basename = os.path.basename(found[0])
          listwriter.writerow([basename])
      else:
        print("  ****************************************************************************************** \n    NOPE, could not even find a FUZZY match!" )
        if show:
          listwriter.writerow(["NO match found!"])






#   # Read all worksheets from the Google Sheet, and find the sheet named "Update"
#   sheets = sh.worksheets()
#   for ws in sheets:
#     title = ws.title
#     # Found the "Update" sheet
#     if (title == "Update"):

#       # Generate a temporary .csv of the worksheet 
#       # per https://community.esri.com/t5/python-questions/how-to-convert-a-google-spreadsheet-to-a-csv-file/td-p/452722
#       with open('temp.csv', 'w', newline='') as csvfile:
#         csvwriter = csv.writer(csvfile)
#         csvwriter.writerows(ws.get_all_values())

#       # Read the temporary .csv into a dict
#       with open('temp.csv', 'r') as data:
#         for record in csv.DictReader(data):

#           # worksheet record now in dict form, process it for updates
#           md_path = str(pathlib.Path.home()) + "/GitHub/rootstalk/content/" + record['Content Path'] + "/" + record['Filename'] + ".md"
#           if os.path.exists(md_path):
#             process_record(record, md_path)
#           else:
#             print(f"Warning: File '{md_path}' does not exist so it's record has been skipped.")

#   exit()



# def process_contributors(contributors, contributor_fields):
#   c_filtered = dict()
#   for f in contributor_fields:
#     if f in contributors[0].keys():
#       c_filtered[f] = contributors[0][f]
#     else: 
#       c_filtered[f] = ""
#   return len(contributors), c_filtered 

# def build_link(k, path):
#   base_urls = { "develop":"https://thankful-flower-0a2308810.1.azurestaticapps.net/", "main":"https://icy-tree-020380010.azurestaticapps.net/", "production":"https://rootstalk.grinnell.edu/" }
#   filename = path.name
#   parent = path.parent.name
#   grandma = path.parent.parent.name
#   if (filename == "_index.md"):
#     filename = ""
#   else:
#     filename = filename[:-3]    # remove .md  
#   if "past" in grandma:
#     url = f"{base_urls[k]}{grandma}/{parent}/{filename}"
#   else:
#     url = f"{base_urls[k]}{parent}/{filename}"
#   return f"{url} "   # blank at the end is necessary for links to work properly

# def parent_path(path):
#   parent = path.parent.name
#   grandma = path.parent.parent.name
#   if "past" in grandma:
#     return f"{grandma}/{parent}"
#   else:
#     return f"{parent}"

# # Lifted from https://stackoverflow.com/a/54231563
# #  csv_file - path to csv file to upload
# #  sheet - a gspread.Spreadsheet object
# #  cell - string giving starting cell, optionally including sheet/tab name
# #    example: 'A1', 'MySheet!C3', etc.
# def paste_csv(csv_file, sheet, cell):
#   if '!' in cell:
#     (tab_name, cell) = cell.split('!')
#     wks = sheet.worksheet(tab_name)
#   else:
#     wks = sheet.sheet1
#   (first_row, first_column) = gs.utils.a1_to_rowcol(cell)

#   with open(csv_file, 'r') as f:
#     csv_contents = f.read()
#   body = {
#     'requests': [{
#       'pasteData': {
#         "coordinate": {
#           "sheetId": wks.id,
#           "rowIndex": first_row-1,
#           "columnIndex": first_column-1,
#         },
#         "data": csv_contents,
#         "type": 'PASTE_NORMAL',
#         "delimiter": ',',
#       }
#     }]
#   }
#   return sheet.batch_update(body)
    
# # From an example at https://pypi.org/project/gspread-formatting/
# def format_google_sheet(sheet, tab_name):
#   bold = gsf.cellFormat(
#     backgroundColor=gsf.color(0.9, 0.9, 0.9),
#     textFormat=gsf.textFormat(bold=True, foregroundColor=gsf.color(0, 0, 0)),
#     )
#   wks = sheet.worksheet(tab_name)
#   batch = gsf.batch_updater(sheet)
#   batch.set_frozen(wks, rows=1)
#   batch.format_cell_ranges(wks, [('A1:Z1', bold)])
#   return batch.execute()

# # From a blog post at https://stackoverflow.com/questions/50938274/sort-a-spread-sheet-via-gspread
# def sort_google_sheet(sheet, tab_name):
#   wks = sheet.worksheet(tab_name)
#   wks.sort((9, 'asc'))   # sort first by articleIndex
#   wks.sort((1, 'asc'))   # now sort by Content Path
#   return

# # From an example at https://pypi.org/project/gspread-formatting/
# def highlight_todo_cells(sheet, tab_name):
#   wks = sheet.worksheet(tab_name)
#   rule = gsf.ConditionalFormatRule(
#     ranges=[gsf.GridRange.from_a1_range('H2:H2000', wks)],
#     booleanRule=gsf.BooleanRule(
#         condition=gsf.BooleanCondition('NOT_BLANK'),
#         format=gsf.cellFormat(textFormat=gsf.textFormat(bold=True), backgroundColor=gsf.Color(1,1,0))
#     )
#   )

#   rules = gsf.get_conditional_format_rules(wks)
#   rules.append(rule)
#   rules.save()


# ######################################################################

# # Main...
# if __name__ == '__main__':
#   csv_filename = "front-matter-status.csv"
  
#   # Open the .csv file for output
#   with open(csv_filename, "w") as csvfile:
#     writer = csv.DictWriter(csvfile, fieldnames=fields.values())
#     writer.writeheader()

#     # Specify the path to be processed...
#     filepath = str(pathlib.Path.home()) + "/GitHub/rootstalk/content/**/volume*/*.md"
  
#     # Iterate over the working directory tree + subdirectories for all {issue}/{article}.md files
#     # Using '*.md' pattern recursively
#     for file in glob.glob(filepath, recursive=True):
    
#       path = pathlib.PurePath(file)
#       article = frontmatter.load(file)
#       obsolete = []
#       filtered = dict()  # must be sure to initialize this to empty here!

#       # Loop on each top-level element of the article's front matter 
#       for key in article.metadata:

#         # Found a key that we didn't expect... warning
#         if key not in fields.keys():
#           assert key not in obsolete, "Error: Front matter key '{key}' does not exist in ANY list!"

#           print(f"Warning: Front matter key '{key}' is obselete. This article needs to be updated!")
#           obsolete.append(key)
        
#         # We have an expected top-level key and value
#         else:
#           value = article.metadata[key]

#           # If we have a list...
#           if type(value) is list:
#             if key == "contributors":
#               c = value[0]
#               for f in contributor_fields:
#                 if f in c.keys():
#                   filtered[fields[f]] = truncate(c[f])
#                 else:
#                   filtered[fields[f]] = ""
#               value = len(value)

#             # Just a list, nothing special  
#             else:  
#               value = ",".join(value)

#           # If we have a dict...
#           if type(value) is dict:
#             if key == "header_image":
#               for f in header_image_fields:
#                 if f in value.keys():
#                   filtered[fields[f]] = truncate(value[f])
#                 else:
#                   filtered[fields[f]] = ""
#               value = True
#             else:
#               print(f"Warning: Unexpected front matter dict {key} found!")

#           filtered[fields[key]] = truncate(value)
    
#       # Seed the .csv row with path and filename
#       filtered[fields['md-file']] = path.name[:-3]
#       filtered[fields['md-path']] = parent_path(path)

#       # Build one live link for each code branch and seed the .csv row with them
#       for key in branches:
#         key_name = f"{key}-link"
#         filtered[fields[key_name]] = build_link(key, path)

#       # Note any obsolete front matter
#       filtered[fields['obsolete']] = obsolete

#       writer.writerow(filtered)

#   # Ok, done writing the .csv, now copy it to a new tab/worksheet in our Google Sheet
#   # Open the Google service account and sheet
#   try:
#     sa = gs.service_account()
#   except Exception as e:
#     print(e)

#   try:  
#     sh = sa.open("Rootstalk Articles Front Matter")
#   except Exception as e:
#     print(e)  

#   # Make a datestamp to name the new worksheet
#   sheet_name = datetime.now().strftime("%Y-%b-%d-%I:%M%p")
  
#   # Create the new/empty worksheet
#   try:
#     worksheet = sh.add_worksheet(title=sheet_name, rows=1, cols=1)
#   except Exception as e:
#     print(e)  

#   # Call our function to write the new Google Sheet worksheet
#   try:
#     paste_csv(csv_filename, sh, sheet_name + "!A1")
#   except Exception as e:
#     print(e)

#   # Call our format function to set the overall format of the new sheet
#   try:
#     format_google_sheet(sh, sheet_name)
#   except Exception as e:
#     print(e)

#   # Call our function to sort the new sheet
#   try:
#     sort_google_sheet(sh, sheet_name)
#   except Exception as e:
#     print(e)

#   # Call our function to set conditional formatting rules
#   try:
#     highlight_todo_cells(sh, sheet_name)
#   except Exception as e:
#     print(e)
