#! /usr/bin/env python
#
# Name:    rdf2nt
#
# Author:  enridaga - Enrico Daga
#          http://www.enridaga.net
#
# Version: 0.1
# Last changed: 08/04/2011
#
# 
import sys
import os
import glob
import re
import logging

sys.tracebacklimit = 10000000

# Get the content of a folder
def get_folder_items(current_folder):
    listing = []
    for item in glob.glob( os.path.join(current_folder, '*') ):
        listing.append(item)
    return listing

# Check if the file is bibtex (ends with .bib)
def is_bibtex(file):
    return re.match(".*?\.bib$", file)

# Lookup directories for *.bib files
def start_recursive(path):
    for item in get_folder_items( path ):
        item = os.path.abspath(item)
        if os.path.isdir(item):
            logging.debug("Item is directory: "+item)
            if not str( item ) == '.':
               start_recursive(item)
        else:
            logging.debug("Item is file: "+item)
            if is_bibtex(item):
               logging.debug("Item is bibtex file: "+item)
               transform(item)
            else:
                logging.debug("Item ignored: "+item)
    return 1

# Start reengineer a file
def transform(file_name):
    logging.debug("Reengineering file "+file_name)
    file = open(file_name)
    for line in file.readlines():
      parse_bib_line(line.strip())

# Flush the reengineered triples in the output file
# and initialize the triple memory-store
def flush_triples():
    global triples
    global out_file
    
    for triple in triples:
       n3triple = ""
       for t in triple:
         n3triple += t
         n3triple += " "
       n3triple += ".\n"
       out_file.write(n3triple)
    init()
    return 1

# Adds the triple to the list of triples to bewrite in the output file in the next flush()
def triple(s, p, o):
    triples.append(  (s,p,o) )

# Prepare an IRI value
def iri(string):
    return "<" + str(string) + ">"

# This prepare a Literal value
# TODO - Define XML datatypes for known literals (boring, which is the added value?)
def literal(string):
    # We try to normalize {} stuff
    # we decide to split the first adn last { one or two
    string = re.sub("^[{]{1,2}","",string)
    string = re.sub("[}]{1,2}$","",string)
    # Now we fix the string for the turtle syntax
    if re.search("^.*?[^\\\\][\\\\][^\\\\].*$",string) != None:
      logging.debug("Escaping the \\ symbol: "+string)
      string = re.sub('\\\\','\\\\\\\\',string)
    if re.search("^.*?[\"\n\r].*$",string) != None:
      string = re.sub('"','\"',string)
      string = "\"\"\"" + string + "\"\"\""
      logging.debug("Escaping the  \": in " + string)
      return string
    else:
      return '"' + string + '"'

# Initialize the task
def init():
    global triples
    global subject
    global vocabulary_namespace
    # TODO
    # Let setup the base vocabulary namespace
    #
    vocabulary_namespace = "http://bib/term/"
    triples = []
    subject = ""
    
# Parse a single line of bibtex file
def parse_bib_line(line):
    global triples
    global subject
    global base_namespace
    global vocabulary_namespace
    
    # If matches the \@<something> init the parser and flush the triples
    if re.match("\@Comment.*",line):
        flush_triples()
    else:
        # If matches the \@ flush triples first
        matches = re.match("\@(?P<type>[^{]+)\{(?P<local_id>[^,$]+)",line )
        if matches != None:
          flush_triples()
          subject = iri(base_namespace + uni( matches.group('local_id') ) )
          property = iri("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
          object =  iri(vocabulary_namespace + uni( matches.group('type') ) )
          triple(subject, property, object)
          return 1
        # If it is a property
        matches = re.match("(?P<property>[^=]+)\=?(?P<value>.+)",line )
        if matches != None:
          property = iri( vocabulary_namespace + uni( matches.group('property').strip() ) )
          # remove ending comma
          vstring = matches.group('value').strip()
          #logging.debug("Value catched is : " + vstring )
          vstring = re.sub("[,]$", "", vstring)
          value = literal( uni( vstring ) )
          triple(subject, property, value)

# To be sure of unicode output (not sure this is needed)
def uni(string):
   u = unicode(string, 'utf-8')
   return u.encode('utf-8')

if __name__ == "__main__":
  if len(sys.argv)==5:
    path = str( sys.argv[1] )
    log_file_name = str( sys.argv[2] )
    global out_file
    out_file_name = str( sys.argv[3] )
    out_file = open(out_file_name,'a')

    global base_namespace
    base_namespace = str( sys.argv[4] )

    if not os.path.exists(log_file_name):
        log_file = open(log_file_name,'a')
        log_file.close()
    
    logging.basicConfig(filename=log_file_name,level=logging.DEBUG)
    
    init()
    
    start_recursive ( path )
    out_file.close()
  else:
    print "usage: ./"+sys.argv[0]+" <path> <log file> <output file name> <base namespace>\n\n* First argument is the starting FS branch to look for bib files\n* Second argument is the log file name\n* Third argument is output file name\n* Fourth argument is the base namespace for individuals"
