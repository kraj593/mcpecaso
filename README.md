# mcPECASO
A two stage optimization framework that finds optimal operating points to maximize desired process variables (productivity/yield/titer/linear combination of these)

## Install
Download a [Python 3 installation](https://www.python.org/downloads/) for your platform, 
or you can use [Anaconda](https://www.continuum.io/downloads). 

### Fresh install
First, clone the repository. You will need your github username and password but if you are here presumably you are logged in.
    
    git clone http://github.com/kraj593/mcpecaso
    cd tsdyssco

Install the dependencies for the project using requirements.txt:
	
	pip install -r requirements.txt

Install the package

    python setup.py install

Optionally, developers may wish to use the develop flag to install the package from the current location, rather than installing in the default Python installation

	python setup.py develop

### Updating
To update to the latest version, run the following in the root folder:
    
    git pull
