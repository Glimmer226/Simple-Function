'''
print inforatmion
'''

import os
import sys
import inspect
import urllib2
import urllib
import json
from xml.etree import ElementTree
from robot.utils import ArgumentParser
from robot.errors import DataError, Information

project_build_dict ={
    "Indio Rhel":"7.1.2.21",
    "Indio Sles":"7.1.2.21",
    "Julian" : "7.3.0.233",
    "JulianSP1" : "7.3.1.125",
    "KensingtonSP1" : "7.4.1.58",
    "Kensington" : "7.4.0.242",
    "Laguna" : "7.5.0.183",
    "Harmony" : "7.2.1.32",
    "Rooster" : "7.5.1.84"
                     }
summarize_result = {}
def main(args):
    
    opts, paths = _process_args(args)
    #print paths
    for filename in paths:
        print filename
        _get_failed_test_name(filename)
        _get_suite_name(filename)
        #print project
        upload_test_result(_get_suite_name(filename))
def _get_failed_test_name(input_file):

    
    suit_result_list = []

    with open(input_file,'r') as f:
        tree = ElementTree.parse(f)
    for test in tree.getiterator('test'):
        #print test
        suit_result = {}
        if test.find('status').attrib.get('status') == 'PASS':
            
            suit_result['test_name']= test.attrib.get('name')
            suit_result['test_result'] = 'PASS'
            suit_result_list.append(suit_result)
  
        elif test.find('status').attrib.get('status') == 'FAIL':
            suit_result['test_name']= test.attrib.get('name')
            suit_result['test_result'] = 'FAIL'
            suit_result_list.append(suit_result)
    summarize_result['test_result']=suit_result_list
    
    #print summarize_result
    
def _get_suite_name(input_file):
    with open(input_file,'r') as f:
        tree = ElementTree.parse(f)
    for test in tree.getiterator('suite'):
        if len(test.attrib):
            print test.attrib.get('name')
            if test.attrib.get('name') == 'Juliansp1':
                return 'JulianSP1'
            elif test.attrib.get('name') == 'Kensingtonsp1':
                return 'KensingtonSP1'
            else:
                return test.attrib.get('name')
        
        
    
def upload_test_result(project):
    api="http://ciweb228-123.asl.lab.emc.com/web/app.php/ci/securityrollup/upload"
    passed_num=0
    failed_num=0
    #print summarize_result['test_result']
    
    for items in summarize_result['test_result']:
        print items    
        if items['test_result'] == 'PASS':
            passed_num += 1
        elif items['test_result'] == 'FAIL':
            failed_num += 1
    total_number = passed_num + failed_num
    

    upload_data = {}
    log_folder = ''
     
    upload_data['project'] = project
    upload_data['build_number'] = project_build_dict[project]
    upload_data['total_tc'] = 43
    upload_data['securityrollup_package_version'] = '2018-R1-v4'
    summary = {}
    summary['total_tc_ci'] = total_number
    summary['pass'] = passed_num
    summary['fail'] = failed_num
    if project == 'Kensington':
        log_folder = 'SecurityRollup_for_kensington'
    elif project == 'KensingtonSP1':
        log_folder = 'SecurityRollup_for_kensingtonsp1'
    elif project == 'Julian':
        log_folder = 'SecurityRollup_for_julian'
    elif project == 'JulianSP1':
        log_folder = 'SecurityRollup_for_juliansp1'
    elif project == 'Laguna':
        log_folder = 'SecurityRollup_for_laguna'
    elif project == 'Harmony':
        log_folder = 'SecurityRollup_for_harmony'
    elif project == 'Indio Rhel':
        log_folder = 'SecurityRollup_for_indiorhel'
    elif project == 'Indio Sles':
        log_folder = 'SecurityRollup_for_indiosles'
    elif project == 'Rooster':
        log_folder = 'SecurityRollup_for_rooster'
    else:
        log_folder = ""
    summary['detail_link'] = 'http://10.110.192.110/%s/log.html' %(log_folder)
    summary['type'] = 'AVE for VMWare'
    upload_data["summary"] = summary
    print upload_data
    encoder= json.JSONEncoder()
    upload_data=encoder.encode(upload_data)
     
    try:
        request = urllib2.Request(api)
        request.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(request,upload_data)
        code= response.code
        result= response.read()
        if code==200:
            result_json=json.loads(result)
            if result_json.has_key("Status") and result_json["Status"]=="Ok":
                return True
            else:
                print result
    except Exception,e:
        print e
    return False

def _process_args(cliargs):
    ap = ArgumentParser(__doc__, arg_limits=(0, ))
    try:
        return ap.parse_args(cliargs)
    except Information, msg:
        _exit(msg)
    except DataError, err:
        _exit(err, error=True)

def _exit(msg, error=False):
    print unicode(msg)
    if error:
        print u"\nPlease use '?' for more help information"
    sys.exit(int(error))


if __name__ == "__main__":
    
    main(sys.argv[1:])
