# sat6_client_configuration

#Description:
This script will help you to register your RHEL clients to your Satellite 6 server. This script also creates "Host" entries and configures the Puppet agent if needed. Unfortunately the given values are not selectable at the moment so you need to copy/paste the values if for example you are asked to select the organization your client should be assigned to.

#Prerequisites:
- Firewall ports from Client to Satellite 6, port 80 / 443 must be opened
- Make sure that you configured at least one hostgroup with lifecycle environment, content view, Puppet environment, Capsule settings, Operating System settings, Locations and Organizations. Otherwise the "Host" entry will not be created properly.

#Usage:
You need at least the "-s", "-l" and "-p" option to run the script.
```
./sat6-register.py --help


Usage: sat6-register.py [options]

Options:
  -h, --help            show this help message and exit
  -s SAT6_FQDN, --server=SAT6_FQDN
                        FQDN of Satellite - omit https://
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
  -v, --verbose         Verbose output
```

