import fitz
from pprint import pprint

doc = fitz.open("2N3904_BJT.pdf") # open document
page = doc[1] # get the 1st page of the document
tabs = page.find_tables(vertical_strategy='lines', horizontal_strategy='lines') # locate and extract any tables on page
print(f"{len(tabs.tables)} found on {page}") # display number of found tables
mt=0
if tabs.tables:  # at least one table found?
   data=tabs[0].extract()
   for d in data:
      for e in d:
        if e=='':
            mt+=1
   if mt/tabs[0].col_count/tabs[0].row_count<.5:     
   #if tabs[0].col_count>1 and tabs[0].row_count>1:
   pprint(tabs[0].extract())  # print content of first table