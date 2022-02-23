# Contributing

How to contribute to easyeda project.

## Fork this repository

**Fork this repository before contributing**. It is a better practice, possibly even enforced, that only Pull Request from forks are accepted - consider a case where there are several main maintainers.

## Clone your fork

Next, clone your fork to your local machine, keep it up to date with the upstream, and update the online fork with those updates.

```bash
git clone https://github.com/YOUR-USERNAME/easyeda2kicad.py.git
cd easyeda2kicad.py
git remote add upstream https://github.com/uPesy/easyeda2kicad.py.git
git fetch upstream
git merge upstream/dev
git pull origin dev
```

**Note that PR should be done on the dev branch**

## Install for developers

Create a dedicated Python environment where to develop the project.


If you are using pip follow the official instructions on [Installing packages using pip and virtual environments](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment), most likely what you want is:

```bash
python -m venv env
source env/bin/activate
```

Where `env` is the name you wish to give to the environment dedicated to this project.

Install the package in develop mode.

```bash
python setup.py develop
```
