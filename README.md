Installation:

sudo yum install -y git python-devel python-setuptools gcc virtualenv

git clone https://github.com/iiman/mytarids-on-nectar.git

cd mytardis-chef

virtualenv .

source bin/activate

pip install -r requirements.txt

Assumptions:

The installation is done on a Chef workstation

Run options
# Creating VM
	python mytardis.py -c 

# Deploying MyTardis to the VM using Chef
	python mytardis.py -m VM_IP_ADDRESS 

# Testing MyTardis deployment
	python mytardis.py -t VM_IP_ADDRESS

# Destroying VM instance	
python mytardis.py -d VM_IP_ADDRESS
