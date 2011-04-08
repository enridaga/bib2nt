#! /usr/bin/env python

import sys
import os
import glob
import re
import logging

sys.tracebacklimit = 10000000

def get_folder_items(current_folder):
    listing = []
    for item in glob.glob( os.path.join(current_folder, '*') ):
        listing.append(item)
    return listing

def is_bibtex(file):
    return re.match(".*?\.bib$", file)

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

def transform(file_name):
    logging.debug("Transforming file "+file_name)
    file = open(file_name)
    for line in file.readlines():
      parse_bib_line(line.strip())

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

def triple(s, p, o):
    triples.append(  (s,p,o) )

def iri(string):
    return "<" + str(string) + ">"

def literal(string):
    # We try to normalize {} stuff
    string = re.sub("^[{]+","",string)
    string = re.sub("[}]+$","",string)
    # Now we fix the string for the turtle syntax
    if re.search("^.*?[^\\\\][\\\\][^\\\\].*$",string) != None:
      logging.debug("Escaping the \\ symbol: "+string)
      #print string
      string = re.sub('\\\\','\\\\\\\\',string)
      #print string
    if re.search("^.*?[\"\n\r].*$",string) != None:
      string = re.sub('"','\"',string)
      string = "\"\"\"" + string + "\"\"\""
      logging.debug("Escaping the  \": in " + string)
      return string
    else:
      return '"' + string + '"'

def init():
    global triples
    global subject
    global vocabulary_namespace
    vocabulary_namespace = "http://bib/term/"
    triples = []
    subject = ""
    
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
        matches = re.match("(?P<property>[^=]+)\=?(?P<value>[^,$]+)",line )
        if matches != None:
          property = iri( vocabulary_namespace + uni( matches.group('property').strip() ) )
          value = literal( uni( matches.group('value').strip() ) )
          triple(subject, property, value)

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
