#!/usr/bin/python
import csv
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import getpass
import sys
from optparse import OptionParser
try:
    import requests
except ImportError:
    print "Please install the python-requests module."
    sys.exit(-1)

def get_json(url):
    # Performs a GET using the passed URL location
  try:
    r = requests.get(url, auth=(options.username, options.password),timeout=options.timeout, verify=options.verify)
    r = r.json()
  except ValueError:
    print  r.text 
    sys.exit(-1)
  return r

def call_api(url):
  jsn = get_json(url)
  if jsn.get('error'):
      print "Error: " + jsn['error']['message']
  else:
      if jsn.get('results'):
          return jsn['results']
      elif 'results' not in jsn:
          return jsn
      else:
          print "No results found"
  return None


def url_list(url):
  url_list = []
  x = call_api(url + "vulnerability/v1/vulnerabilities/cves?data_format=json&show_all=false&page_size=200000")['data']
  for ids in x:
    y = url + "vulnerability/v1/cves/" + ids['id'] + "/affected_systems?page_size=200000&data_format=json"
    url_list.append(y)
  return url_list

def grab_inv_list(url):
  inv_list = []
  x = call_api(url + "vulnerability/v1/systems?page_size=300")['data']
  for inv in x:
    inv_dict = {'hostname': inv['attributes']['display_name'],'id':[]}
    inv_list.append(inv_dict)
  return inv_list

def cve_rhsa_to_host(url):
  # Add RHSA or CVE key
  x = get_json(url)['data']
  cve_rhsa = re.search('(?=CVE|RHSA)([^abc]+-\d\d\d\d-\d+)(?=\/a)', url)
  cve_rhsa_dict = {'id': cve_rhsa.group(1),'hostname':[]}
  for y in x:
    cve_rhsa_dict['hostname'].append(y['attributes']['display_name']) 
  cve_rhsa_list.append(cve_rhsa_dict)

def api_threader(url_list):
  threads = []
  with ThreadPoolExecutor(max_workers=2) as executor:
    for url in url_list:
      threads.append(executor.submit(cve_rhsa_to_host, url))

      
def gen_report(url):
  u_list = url_list(url)
  api_threader(u_list)
  map_id_to_hosts(url)

def map_id_to_hosts(url):
  inv = grab_inv_list(url)
  cvh = cve_rhsa_list 
  for a in cvh:
    ids = a['id']
    print ids
    for i in inv:
      print a['hostname']
      if i['hostname'] in a['hostname']:
        i['id'].append(ids)
  print inv
  return inv


if __name__ == '__main__':
  usage = "Usuage: %prog ./in.py -u user -c"
  parser = OptionParser(usage=usage)
  parser.add_option("-u", dest="username", help="Add username")
  parser.add_option("-p", dest="password", help="Add password")
  parser.add_option("-v", dest="verify", default="/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem", help="Ignore untrusted CA")
  parser.add_option("-t", dest="timeout", type="int", default=10, help="Set API timeoute")
  parser.add_option("-c", dest="cve", action='store_true', default=False, help="Create CVE Report")
  parser.add_option("-i", dest="hosts", action='store_true', default=False, help="Use a list of hosts, if your inventory is less than the total number of CVEs or RHSA")
  parser.add_option("-r", dest="rhsa", action='store_true', default=False, help="Create RHSA Report")
  parser.add_option("--url", dest="url", action="store_true", default="https://cloud.redhat.com/api/", help="URL for API Call")
  (options, args) = parser.parse_args()

  if not options.password:
    options.password = getpass.getpass("%s's password:" % options.login)

  if not (options.username and options.cve) or (options.username and options.rhsa): 
    print("You must add a user and to generate a cve report or a rhsa report") 
    sys.exit(1)

  cve_rhsa_list = []
  #grab_id(options.url)
  start = time.time()
  print start
  gen_report(options.url)
  print time.time()-start
