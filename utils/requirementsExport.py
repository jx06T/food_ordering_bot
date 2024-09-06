import subprocess

installed_packages = subprocess.check_output(['pip', 'freeze'])

with open('../requirements.txt', 'wb') as f:
    f.write(installed_packages)
