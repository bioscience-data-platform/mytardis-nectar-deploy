##Assumptions

The commands in this tool are executed from a Chef workstation


##Installation

###Install packages
	sudo yum install -y git python-devel python-setuptools gcc virtualenv

	git clone https://github.com/iiman/mytarids-on-nectar.git


###Prepare your working environment
	cd mytardis-chef

	virtualenv .

	source bin/activate

	pip install -r requirements.txt

	cp settings_changeme settings

NB: Edit *settings* file as needed.

##Run options

Creating VM

	python mytardis.py -c

Deploying MyTardis to the VM using Chef

	python mytardis.py -m VM_IP_ADDRESS

Testing MyTardis deployment

	python mytardis.py -t VM_IP_ADDRESS

Destroying VM instance	

	python mytardis.py -d VM_IP_ADDRESS
