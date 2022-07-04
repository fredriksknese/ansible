# Disclaimer
I created these modules while I studied. They are not bug free. They did how ever work for me.

They are made for Cisco devices only with version 15.*

You cant just git clone and excpect it to work out of the box. It will not.

# Usage
ansible-playbook -i inventory/vars -i inventory/okssh -M modules/ --vault-id .passwordfile cisco-image-upgrade.yaml

ansible-playbook -i inventory/vars -i inventory/dot1xswitches.ini -M modules/ --vault-id .passwordfile dot1x.yaml

ansible-playbook -i inventory/vars -i inventory/test.ini -M modules/ --vault-id .passwordfile cisco-image-upgrade.yaml

