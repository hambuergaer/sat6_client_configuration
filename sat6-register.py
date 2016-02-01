#!/usr/bin/python
#
#####################################################################################
# Scriptname	: sat6-register.py
# Scriptauthor	: Frank Reimer
# Creation date	: 2016-01-05
# License	: GPL v. 3
#
# This script was inspired by https://github.com/sideangleside/sat6-bootstrap
#
#####################################################################################
#
# Description:
#
# This script will help you to register your RHEL clients to your Satellite 6 server.
# This script also creates "Host" entries and configures the Puppet agent if needed.
# Unfortunately the given values are not selectable at the moment so you need to
# copy/paste the values if for example you are asked to select the organization your
# client should be assigned to. If you want to run this script unattended then you
# need to add ALL options mentioned in the script usage before using the "-u" flag.
# If you do not pass all values the script will ask you for the remaining. If you
# also want to update your system you can pass by the option "-U". Please ignore the
# following message during the first Puppet run:
#
# Warning: Local environment: "production" doesn't match server specified node
# environment [...]
#
#####################################################################################

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

CURRENT_DATE = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

HOSTNAME  = platform.node().split(".")[0]
HEXMAC    = hex(getnode())
NOHEXMAC  = HEXMAC[2:]
MAC       = NOHEXMAC.zfill(13)[0:12]

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

def post_json(url, jdata):
    try:
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(url)
        base64string = base64.encodestring('%s:%s' % (LOGIN, PASSWORD)).strip()
        request.add_data(json.dumps(jdata))
        request.add_header("Authorization", "Basic %s" % base64string)
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json")
        #request.get_method = lambda: 'PUT'
        request.get_method = lambda: 'POST'
        url = opener.open(request)

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

def return_location_name():
        myurl = "https://" + SAT6_FQDN+ "/api/v2/locations/"
        locations = get_json(myurl)
        loc_name = []
        for loc in locations['results']:
                name = str(loc['name'])
                loc_name.append(name)
        return loc_name

def return_location_id(location):
	myurl = "https://" + SAT6_FQDN+ "/api/v2/locations/"
        locations = get_json(myurl)
        loc_id = ''
	for locid in locations['results']:
		if str(locid['name']) == location:
			loc_id = locid['id']
			return loc_id

def return_organization_label(orgname):
        myurl = 'https://' + SAT6_FQDN + '/katello/api/v2/organizations/' + str(orgname) + '/'
        orglabel = get_json(myurl)
        orglabel_name = str(orglabel['label'])
        return orglabel_name

def return_hostgroups():
	myurl = "https://" + SAT6_FQDN+ "/api/v2/hostgroups/"
	hostgroups = get_json(myurl)
	hg_name = []
	for hg in hostgroups['results']:
		name = str(hg['name']) + " \t\t(parent: " + str(hg['title'] + ")")
		hg_name.append(name)
	return hg_name

def return_hostgroup_id(hostgroup):
	myurl = "https://" + SAT6_FQDN+ "/api/v2/hostgroups/"
        hostgroups = get_json(myurl)
        hg_id = ''
	for hgid in hostgroups['results']:
                if str(hgid['name']) == hostgroup:
                        hg_id = hgid['id']
                        return hg_id

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
	cmd_check = '/usr/sbin/subscription-manager status'
	if subprocess.call(cmd_check, shell=True, stdout=subprocess.PIPE) == 0:
		return 0
	else:
		return 1

def install_needed_packages():
	cmd_yum = "/usr/bin/yum install -y katello-agent --nogpgcheck"
	print log.INFO + "INFO: Installing katello-agent." + log.END
        try:
                subprocess.call(cmd_yum, shell=True, stdout=subprocess.PIPE)
                print log.INFO + "INFO: katello-agent sucessfully installed." + log.END
	except:
                print log.ERROR + "ERROR: failed to install katello-agent. EXIT." + log.END
                sys.exit(1)

def create_new_host(hostgroup,location,organization):
        orgid = return_organization_id(organization)
	locid = return_location_id(location)
	hgid = return_hostgroup_id(hostgroup)
	jsondata = json.loads('{"host": {"name": "%s","hostgroup_id": %s,"organization_id": %s,"location_id": %s,"mac":"%s"}}' % (HOSTNAME,hgid,orgid,locid,MAC))
	myurl = "https://" + SAT6_FQDN + "/api/v2/hosts/"
	print log.INFO + "INFO: Calling Satellite API to create a host entry assoicated with the group, org & location" + log.END
	post_json(myurl,jsondata)
	print log.INFO + "INFO: Successfully created host %s" % HOSTNAME + log.END

def remove_existing_puppet_agent():
	cmd_puppet_erase_01 = "/usr/bin/yum erase puppet -y"
	cmd_puppet_erase_02 = "/bin/rm -Rf /var/lib/puppet/"
	print log.INFO + "INFO: Removing existing Puppet agent and its configuration." + log.END
	try:
                subprocess.call(cmd_puppet_erase_01, shell=True, stdout=subprocess.PIPE)
                subprocess.call(cmd_puppet_erase_02, shell=True, stdout=subprocess.PIPE)
	except:
                print log.ERROR + "ERROR: failed to clean Puppet agent. EXIT." + log.END
                sys.exit(1)

def install_puppet_agent():
	cmd_yum = "/usr/bin/yum install -y puppet --nogpgcheck"
	print log.INFO + "INFO: Installing Puppet agent." + log.END
        try:
                subprocess.call(cmd_yum, shell=True, stdout=subprocess.PIPE)
                print log.INFO + "INFO: Puppet agent sucessfully installed." + log.END
	except:
                print log.ERROR + "ERROR: failed to install Puppet agent. EXIT." + log.END
                sys.exit(1)

def configure_puppet():
	cmd_puppet_01 = "/usr/bin/puppet config set --section agent report true"
	cmd_puppet_02 = "/usr/bin/puppet config set --section agent ignoreschedules true"
	cmd_puppet_03 = "/usr/bin/puppet config set --section agent daemon false"
	cmd_puppet_04 = "/usr/bin/puppet config set --section agent listen true"
	cmd_puppet_05 = "/usr/bin/puppet config set --section agent ca_server " + str(CAPSULE)
	cmd_puppet_06 = "/usr/bin/puppet config set --section agent server " + str(CAPSULE)
	try:
                subprocess.call(cmd_puppet_01, shell=True, stdout=subprocess.PIPE)
                subprocess.call(cmd_puppet_02, shell=True, stdout=subprocess.PIPE)
                subprocess.call(cmd_puppet_03, shell=True, stdout=subprocess.PIPE)
                subprocess.call(cmd_puppet_04, shell=True, stdout=subprocess.PIPE)
                subprocess.call(cmd_puppet_05, shell=True, stdout=subprocess.PIPE)
                subprocess.call(cmd_puppet_06, shell=True, stdout=subprocess.PIPE)
		print log.INFO + "INFO: Puppet client configuration successfully changed." + log.END
	except:
                print log.ERROR + "ERROR: failed to configure Puppet agent. EXIT." + log.END
                sys.exit(1)	

def initial_puppet_run():
	cmd = "/usr/bin/puppet agent -t -v --onetime --waitforcert 60"
	print log.WARN + "INFO: start initial Puppet run. Please visit your Satellite or Capsule server to sign the Puppet client cert request unless you configured Puppet autosign feature. Please ignore the following error message 'Warning: Local environment: production doesn't match server specified node environment [...]'"
	try:
		subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
		print log.INFO + "INFO: successfully performed initial Puppet run."
	except:
		print log.ERROR + "ERROR: failed to start initial Puppet agent run."

################################## OPTIONS PARSER AND VARIABLES ##################################

parser = OptionParser()
parser.add_option("-s", "--server", dest="sat6_fqdn", help="FQDN of Satellite - omit https://", metavar="SAT6_FQDN")
parser.add_option("-c", "--capsule", dest="capsule", help="FQDN of Capsule - omit https://", metavar="CAPSULE")
parser.add_option("-l", "--login", dest="login", help="Login user for API Calls", metavar="LOGIN")
parser.add_option("-p", "--password", dest="password", help="Password for specified user. Will prompt if omitted", metavar="PASSWORD")
parser.add_option("-a", "--activationkey", dest="activationkey", help="Activation Key to register the system", metavar="ACTIVATIONKEY")
parser.add_option("-g", "--hostgroup", dest="hostgroup", help="Label of the Hostgroup in Satellite that the host is to be associated with", metavar="HOSTGROUP")
parser.add_option("-L", "--location", dest="location", help="Label of the Location in Satellite that the host is to be associated with", metavar="LOCATION")
parser.add_option("-o", "--organization", dest="organization", help="Label of the Organization in Satellite that the host is to be associated with", metavar="ORGANIZATION")
parser.add_option("-u", "--unattended", dest="unattended", action="store_true", help="Start unattended installation.")
parser.add_option("-P", "--puppet", dest="puppet", action="store_true", help="Configure Puppet agent and delete old Puppet configuration.")
parser.add_option("-U", "--update", dest="update", action="store_true", help="Performs yum update -y.")
parser.add_option("-v", "--verbose", dest="verbose", action="store_true", help="Verbose output")
(options, args) = parser.parse_args()

if not ( options.sat6_fqdn and options.login):
    print log.ERROR + "You must specify at least server and login parameter. See usage:\n" + log.END
    parser.print_help()
    print "\nExample usage: ./sat6-register.py -l admin -p password -s satellite.example.com"
    sys.exit(1)
else:
    SAT6_FQDN = options.sat6_fqdn
    CAPSULE   = options.capsule
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

if options.unattended:
    UNATTENDED=True
else:
    UNATTENDED=False

if options.update:
    UPDATE=True
else:
    UPDATE=False

if options.puppet:
    PUPPET=True
else:
    PUPPET=False

if not PASSWORD:
        PASSWORD = getpass.getpass("%s's password:" % LOGIN)

if VERBOSE:
    print "HOSTNAME - %s" % HOSTNAME
    print "MAC - %s" % MAC
    print "HEXMAC - %s" % HEXMAC
    print "NOHEXMAC - %s" % NOHEXMAC
    print "ORGANIZATION - %s" % ORGANIZATION
    print "CAPSULE - %s" % CAPSULE
    print "HOSTGROUP - %s" % HOSTGROUP
    print "LOCATION - %s" % LOCATION
    print "SAT6_FQDN - %s" % SAT6_FQDN
    print "ACTIVATIONKEY - %s" % ACTIVATIONKEY
    print "PUPPET - %s" % PUPPET
    print "UPDATE - %s" % UPDATE


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
if not ORGANIZATION:
	print log.INFO + "Available organizations:" + log.END
	for org in return_organization_name():
		print "-> " + org
	ORGANIZATION = raw_input(log.INFO + "Select an appropriate organization: " + log.END)
	while not ORGANIZATION:
		print log.WARN + "You must select an organization where your host will be assigned to." + log.END 
		ORGANIZATION = raw_input(log.INFO + "Select an appropriate organization:\n" + log.END) 

# Select location
if not LOCATION:
	print log.INFO + "Available locations:" + log.END
	for loc in return_location_name():
        	print "-> " + loc
	LOCATION = raw_input(log.INFO + "Select an appropriate location: " + log.END)
	while not LOCATION:
        	print log.WARN + "You must select an location where your host will be assigned to." + log.END
        	LOCATION = raw_input(log.INFO + "Select an appropriate location:\n" + log.END)

# Select hostgroup
if not HOSTGROUP:
	print log.INFO + "Available hostgroups:" + log.END
	for hg in return_hostgroups():
		print "-> " + hg
	HOSTGROUP = raw_input(log.INFO + "Select an appropriate hostgroup: " + log.END)
	while not HOSTGROUP:
        	print log.WARN + "You must select a hostgroup where your host will be assigned to." + log.END
        	HOSTGROUP = raw_input(log.INFO + "Select an appropriate hostgroup:\n" + log.END)

## Select a Capsule server where the client should be registered.
if not CAPSULE:
	print log.INFO + "Capsule servers:" + log.END
	for cap in return_capsule_name():
		print "-> " + cap
	CAPSULE = raw_input(log.INFO + "Select a Capsule where you want to register your client: " + log.END)
	while not CAPSULE:
		print log.WARN + "You must select a Capsules server." + log.END
		CAPSULE = raw_input(log.INFO + "Select a Capsule where you want to register your client: " + log.END)

## Select Activationkey for given organization
if not ACTIVATIONKEY:
	print log.INFO + "Will now check for available Activation Keys. This could take some time..." + log.END
	ORGID = return_organization_id(ORGANIZATION)
	ACTKEYS = return_activation_key_name(ORGID)
	for key in ACTKEYS:
		print "-> " + key
	ACTIVATIONKEY = raw_input(log.INFO + "Select appropriate Activationkey: " + log.END)

## Print summary and start tasks
print log.SUMM + "\n" + 30*"#" + log.END
print log.SUMM + "#" + log.END
print log.SUMM + "# SUMMARY"
print log.SUMM + "#" + log.END
print log.SUMM + 30*"#" + log.END

print log.INFO + "Please verify the your choices:"
print log.WARN + "Organization:\t" + log.END + ORGANIZATION
print log.WARN + "Location:\t" + log.END + LOCATION
print log.WARN + "Capsule:\t" + log.END + CAPSULE 
print log.WARN + "Activationkey:\t" + log.END + ACTIVATIONKEY
print log.WARN + "Hostgroup:\t" + log.END + HOSTGROUP

if UNATTENDED and SAT6_FQDN and CAPSULE and ORGANIZATION and LOCATION and ACTIVATIONKEY and HOSTGROUP:
	# Registering system at give destination
        print log.INFO + "INFO: Registering client at your destination " + CAPSULE
        ORGLABEL=return_organization_label(ORGANIZATION)
        register_system(CAPSULE,ACTIVATIONKEY,ORGLABEL)

        # Create new host entry
        print log.INFO + "INFO: creating new host entry on Satellite server." + log.END
        create_new_host(HOSTGROUP,LOCATION,ORGANIZATION)

	# Install needed packages
	install_needed_packages()
	
        # Configure Puppet agent
        if PUPPET:
		remove_existing_puppet_agent()
		install_puppet_agent()
		configure_puppet()
		initial_puppet_run()
	
	# Start update of the whole server if Option "-U" was given.
	if UPDATE:
		print log.INFO + "INFO: Will now try to update your system. This can take some time..." + log.END
                update_system()
	
	print log.INFO + "FINISHED: registration and configuration of your Satellite 6 client successfullly finished." + log.END
	sys.exit(0)

SUMMARY = raw_input(log.INFO + "Are your settings correct (y/n)? : " + log.END)
while not SUMMARY:
	print log.WARN + "You must either type y/Y or n/N." + log.END
if SUMMARY == "y" or SUMMARY == "Y":
	print "\n"

	# Registering system at give destination
	print log.INFO + "INFO: Registering client at your destination " + CAPSULE
	ORGLABEL=return_organization_label(ORGANIZATION)
	register_system(CAPSULE,ACTIVATIONKEY,ORGLABEL)
	
	# Create new host entry
	print log.INFO + "INFO: creating new host entry on Satellite server." + log.END
	create_new_host(HOSTGROUP,LOCATION,ORGANIZATION)
	
	# Install needed packages
	install_needed_packages()
	
        # Configure Puppet agent
        if PUPPET:
		remove_existing_puppet_agent()
		install_puppet_agent()
		configure_puppet()
		initial_puppet_run()
	
	# Start update of the whole server if Option "-U" was given.
	if UPDATE:
		print log.INFO + "INFO: Will now try to update your system. This can take some time..." + log.END
                update_system()
	else:
		print log.INFO + "INFO: it is recommended to update your system to the latest package versions. Please perform a 'yum update -y' after this script is finished."
	
	print log.INFO + "FINISHED: registration and configuration of your Satellite 6 client successfullly finished." + log.END
	sys.exit(0)

if SUMMARY == "n" or SUMMARY == "N":
	print log.WARN + "INFO: Will exit now. Pelase re-run this script." + log.END
	sys.exit(0)
else:
	sys.exit(1)
