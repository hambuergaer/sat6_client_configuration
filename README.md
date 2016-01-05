# sat6_client_configuration

#Description:
This script will help you to register your RHEL clients to your Satellite 6 server. This script also creates "Host" entries and configures the Puppet agent if needed. Unfortunately the given values are not selectable at the moment so you need to copy/paste the values if for example you are asked to select the organization your client should be assigned to. If you want to run this script unattended then you need to add ALL options mentioned in the script usage before using the "-u" flag. If you do not pass all values the script will ask you for the remaining. If you also want to update your system you can pass by the option "-U". This script also configures your Puppet agent and starts an initial Puppet run. Please ignore the following message during the first Puppet run:
```
Warning: Local environment: "production" doesn't match server specified node environment [...]
```
This script was inspired by https://github.com/sideangleside/sat6-bootstrap

#Prerequisites:
- Firewall ports from Client to Satellite 6, port 80 / 443 must be opened
- Make sure that you configured at least one hostgroup with lifecycle environment, content view, Puppet environment, Puppet classes (if available), Capsule settings, Operating System settings, Locations and Organizations. Otherwise the "Host" entry will not be created properly.
- Change number of entries per page to >= 100 in Satellite 6 Web-UI: 'Administer -> Settings -> General -> entries_per_page'. This number depends on for example how many hostgroups, activation keys etc. are configured in your Satellite environment.

#Usage:
You need at least the "-s", "-l" and "-p" option to run the script.
```
./sat6-register.py --help

Usage: sat6-register.py [options]

Options:
  -h, --help            show this help message and exit
  -s SAT6_FQDN, --server=SAT6_FQDN
                        FQDN of Satellite - omit https://
  -c CAPSULE, --capsule=CAPSULE
                        FQDN of Capsule - omit https://
  -l LOGIN, --login=LOGIN
                        Login user for API Calls
  -p PASSWORD, --password=PASSWORD
                        Password for specified user. Will prompt if omitted
  -a ACTIVATIONKEY, --activationkey=ACTIVATIONKEY
                        Activation Key to register the system
  -g HOSTGROUP, --hostgroup=HOSTGROUP
                        Label of the Hostgroup in Satellite that the host is
                        to be associated with
  -L LOCATION, --location=LOCATION
                        Label of the Location in Satellite that the host is to
                        be associated with
  -o ORGANIZATION, --organization=ORGANIZATION
                        Label of the Organization in Satellite that the host
                        is to be associated with
  -u, --unattended      Start unattended installation.
  -U, --update          Performs yum update -y.
  -v, --verbose         Verbose output

Example usage: ./sat6-register.py -l admin -p password -s satellite.example.com
```

