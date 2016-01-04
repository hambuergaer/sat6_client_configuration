#!/usr/bin/python
#
import json
import getpass
import urllib2
import base64
import sys
import commands
import subprocess
import platform
import os.path
from datetime import datetime
from optparse import OptionParser
from uuid import getnode

#SAT6_FQDN = ""
#LOGIN = ""
#PASSWORD = ""

class log:
	HEADER	= '\033[0;36m'
	ERROR	= '\033[1;31m'
	INFO	= '\033[0;32m'
	WARN	= '\033[1;33m'
	SUMM	= '\033[1;35m'
	END	= '\033[0m'

def get_json(url):
        # Generic function to HTTP GET JSON from Satellite's API
    try:
        request = urllib2.Request(urllib2.quote(url,':/'))
        base64string = base64.encodestring('%s:%s' % (LOGIN, PASSWORD)).strip()
        request.add_header("Authorization", "Basic %s" % base64string)
        result = urllib2.urlopen(request)
        return json.load(result)
    except urllib2.URLError, e:
        print "Error: cannot connect to the API: %s" % (e)
        print "Check your URL & try to login using the same user/pass via the WebUI and check the error!"
        sys.exit(1)
    except:
        print "FATAL Error - %s" % (e)
        sys.exit(2)

def return_organization_name():
	myurl = "https://" + SAT6_FQDN+ "/api/v2/organizations/"
	organizations = get_json(myurl)
	org_name= []
	for org in organizations['results']:
		name = str(org['name'])
		org_name.append(name)
	return org_name

def return_organization_id(orgname):
        myurl = "https://" + SAT6_FQDN+ "/api/v2/organizations/"
        organizations = get_json(myurl)
	org_id=''
        for orgid in organizations['results']:
		if str(orgid['name']) == orgname:
                	org_id = orgid['id']
			return org_id

def return_organization_label(orgname):
        myurl = 'https://' + SAT6_FQDN + '/katello/api/v2/organizations/' + str(orgname) + '/'
        orglabel = get_json(myurl)
        orglabel_name = str(orglabel['label'])
        return orglabel_name

def return_hostgroups():
	myurl = "https://" + SAT6_FQDN+ "/api/v2/hostgroups/"
	hostgroups = get_json(myurl)
	for hg in hostgroups['results']:
        	hg_id = str(hg['id'])
		hg_name = str(hg['name'])
		hg_parent = str(hg['title'])
		print "Hostgroup name: " + hg_name + ", Hostgroup ID: " + hg_id + " Parent: " + hg_parent

def return_capsule_name():
	myurl = "https://" + SAT6_FQDN+ "/katello/api/capsules/"
        capsules = get_json(myurl)
	capsule_name = [] 
        for capsule in capsules['results']:
                name = str(capsule['name'])
		capsule_name.append(name)	
		#capsules.append(str(capsule_name))
	return capsule_name

def return_activation_key_name(orgid):
	myurl = 'https://' + SAT6_FQDN + '/katello/api/v2/organizations/' + str(orgid) + '/activation_keys/'
	print myurl
	activationkeys = get_json(myurl)
	activationkey_name = []
	for activationkey in activationkeys['results']:
		act_name = str(activationkey['name'])
		activationkey_name.append(act_name)
	return activationkey_name

def register_system(destination,activationkey,organization):
	cmd_yum = "/usr/bin/yum -y localinstall http://" + destination + "/pub/katello-ca-consumer-latest.noarch.rpm --nogpgcheck"
	cmd_sub = "/usr/sbin/subscription-manager register --org " + organization + " --activationkey " + activationkey
	print log.INFO + "INFO: Calling subscription-manager to register your system" + log.END
	try:
		subprocess.call(cmd_yum, shell=True, stdout=subprocess.PIPE)
		subprocess.call(cmd_sub, shell=True, stdout=subprocess.PIPE)
		print log.INFO + "INFO: your system was successfully registered." + log.END
		
	except:
		print log.ERROR + "ERROR: failed to run Subscription Manager. EXIT." + log.END
		sys.exit(1)

def update_system():
	cmd_update = "/usr/bin/yum update -y"
	try:
		subprocess.call(cmd_update, shell=True, stdout=subprocess.PIPE)
		print log.INFO + "INFO: your system was successfully updated." + log.END
	except:
		print log.ERROR + "ERROR: failed to update your system Please check /var/log/messages for more informations." + log.END

def check_subscription_manager_status():
	cmd_check = '/usr/sbin/subscription-manager list | grep -e Subskribiert -e Subscribed'
	if subprocess.call(cmd_check, shell=True, stdout=subprocess.PIPE) == 0:
		return 0
	else:
		return 1


################################## OPTIONS PARSER AND VARIABLES ##################################

parser = OptionParser()
parser.add_option("-s", "--server", dest="sat6_fqdn", help="FQDN of Satellite - omit https://", metavar="SAT6_FQDN")
parser.add_option("-l", "--login", dest="login", default='admin', help="Login user for API Calls", metavar="LOGIN")
parser.add_option("-p", "--password", dest="password", help="Password for specified user. Will prompt if omitted", metavar="PASSWORD")
parser.add_option("-a", "--activationkey", dest="activationkey", help="Activation Key to register the system", metavar="ACTIVATIONKEY")
parser.add_option("-g", "--hostgroup", dest="hostgroup", help="Label of the Hostgroup in Satellite that the host is to be associated with", metavar="HOSTGROUP")
parser.add_option("-L", "--location", dest="location", default='Default_Location', help="Label of the Location in Satellite that the host is to be associated with", metavar="HOSTGROUP")
parser.add_option("-o", "--organization", dest="organization", default='Default_Organization', help="Label of the Organization in Satellite that the host is to be associated with", metavar="ORGANIZATION")
parser.add_option("-v", "--verbose", dest="verbose", action="store_true", help="Verbose output")
(options, args) = parser.parse_args()

if not ( options.sat6_fqdn and options.login):
    print log.ERROR + "You must specify at least server and login parameter. See usage:\n" + log.END
    parser.print_help()
    print "\nExample usage: ./bootstrap.py -l admin -s satellite.example.com -o Default_Organization -L Default_Location -g My_Hostgroup -a My_Activation_Key"
    sys.exit(1)
else:
    SAT6_FQDN = options.sat6_fqdn
    LOGIN     = options.login
    PASSWORD  = options.password
    HOSTGROUP = options.hostgroup
    LOCATION  = options.location
    ORGANIZATION  = options.organization
    ACTIVATIONKEY = options.activationkey

if options.verbose:
    VERBOSE=True
else:
    VERBOSE=False

if not PASSWORD:
        PASSWORD = getpass.getpass("%s's password:" % LOGIN)

if VERBOSE:
    print "HOSTNAME - %s" % HOSTNAME
    print "MAC - %s" % MAC
    print "SAT6_FQDN - %s" % SAT6_FQDN
    print "LOGIN - %s" % LOGIN
    print "PASSWORD - %s" % PASSWORD
    print "HOSTGROUP - %s" % HOSTGROUP
    print "LOCATION - %s" % LOCATION
    print "ORG - %s" % ORG
    print "ACTIVATIONKEY - %s" % ACTIVATIONKEY


################################## MAIN ##################################

## Print header text
print log.HEADER + 85*"#" + log.END
print log.HEADER + "#" + log.END
print log.HEADER + "#" + '\033[1m' + " WELCOME TO SATELLITE 6 BOOTSTRAP SCRIPT." + log.END
print log.HEADER + "#" + log.END
print log.HEADER + "#" + log.END
print log.HEADER + "# This script will help you to automatically register your Red Hat Enteprise Linux" + log.END
print log.HEADER + "# client system to your Red Hat Satellite 6 server and configure your Puppet " + log.END
print log.HEADER + "# environment as needed. " + log.END
print log.HEADER + "#" + log.END
print log.HEADER + 85*"#" + log.END

## First check if the system is already registered somewhere
if check_subscription_manager_status() == 0:
	print log.WARN + "WARN: Your system is already registered. Please check 'subscription-manager list'." + log.END
	sys.exit(0)
else:
	print log.INFO + "INFO: Your system in not registerd to any Satellite yet. Will do it now." + log.END

## Select an organization
print log.INFO + "Available organizations:" + log.END
for org in return_organization_name():
	print "-> " + org
ORGANIZATION = raw_input(log.INFO + "Select an appropriate organization: " + log.END)
while not ORGANIZATION:
	print log.WARN + "You must select an organization where your host will be assigned to." + log.END 
	ORGANIZATION = raw_input(log.INFO + "Select an appropriate organization:\n" + log.END) 

## Select a Capsule server where the client should be registered.
print log.INFO + "Capsule servers:" + log.END
for cap in return_capsule_name():
	print "-> " + cap
CAPSULE = raw_input(log.INFO + "Select a Capsule where you want to register your client: " + log.END)
while not CAPSULE:
	print log.WARN + "You must select a Capsules server." + log.END
	CAPSULE = raw_input(log.INFO + "Select a Capsule where you want to register your client: " + log.END)

## Select Activationkey for given organization
print log.INFO + "Will now check for available Activation Keys. This could take some time..." + log.END
ORGID = return_organization_id(ORGANIZATION)
ACTKEYS = return_activation_key_name(ORGID)
for key in ACTKEYS:
	print "-> " + key
SELECT_ACKTKEY = raw_input(log.INFO + "Select appropriate Activationkey: " + log.END)
#while not SELECT_ACKTKEY:
#	print log.WARN + "You must select an Activationkey." + log.END
#	SELECT_ACKTKEY = raw_input(log.INFO + "Select appropriate Activationkey: " + log.END)

## Print summary and start tasks
print log.SUMM + "\n\n" + 30*"#" + log.END
print log.SUMM + "#" + log.END
print log.SUMM + "# SUMMARY"
print log.SUMM + "#" + log.END
print log.SUMM + 30*"#" + log.END

print log.INFO + "Please verify the your choices:"
print log.WARN + "Organization:\t" + log.END + ORGANIZATION
print log.WARN + "Capsule:\t" + log.END + CAPSULE 
print log.WARN + "Activationkey:\t" + log.END + SELECT_ACKTKEY
SUMMARY = raw_input(log.INFO + "Are your settings correct (y/n)? : " + log.END)
while not SUMMARY:
	print log.WARN + "You must either type y/Y or n/N." + log.END
if SUMMARY == "y" or SUMMARY == "Y":
	print "\n"
	# Registering system at give destination
	print log.INFO + "INFO: Registering client at your destination " + CAPSULE
	ORGLABEL=return_organization_label(ORGANIZATION)
	register_system(CAPSULE,SELECT_ACKTKEY,ORGLABEL)
	
	# Updating the box?
	UPDATE = raw_input(log.INFO + "Do you want to Update your system (y/n)? : " + log.END)
	if UPDATE == "y" or UPDATE == "Y":
		print log.INFO + "INFO: Will now try to update your system..." + log.END
		update_system()
	if UPDATE == "n" or UPDATE == "N":
		print log.INFO + "INFO: You can update your system later." + log.END		
	
if SUMMARY == "n" or SUMMARY == "N":
	print log.WARN + "INFO: Will exit now. Pelase re-run this script." + log.END
	sys.exit(0)
else:
	sys.exit(1)

#return_hostgroups()

