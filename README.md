##Assumptions

The commands in this tool are executed from a Chef workstation


##Installation

###Install packages
	sudo yum install -y git python-devel python-setuptools gcc

	sudo easy_install virtualenv	

	git clone https://github.com/iiman/mytardis-nectar-deploy.git

###Prepare your working environment
	cd mytardis-nectar-deploy

	virtualenv .

	source bin/activate

	pip install -r requirements.txt

	cp settings_changeme settings

NB: Edit *settings* file as needed.

##Run options

Creating VM

	python mytardis.py -c

Deploying MyTardis to the VM using Chef. Deploying MyTardis involves configuration of the chef client, and then deployment. The overall process takes on average 25 minutes: 5 minutes are spent on configuration while 20 minutes are spent on deployment.   

	python mytardis.py -m VM_IP_ADDRESS

Testing MyTardis deployment

	python mytardis.py -t VM_IP_ADDRESS

Destroying VM instance	

	python mytardis.py -d VM_IP_ADDRESS
