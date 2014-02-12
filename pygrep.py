import subprocess
from glob import glob

# -i   : case insensitive search
# -C 3 : with three lines of context on either side
base = "egrep -i -C 3 %s"
files = glob("*.log")

def do(query):
    command = base % query
    
    results = None
    
    try:
        results = subprocess.check_output(command.split() + files)
    except subprocess.CalledProcessError as e:
        print e.cmd, e.output
        
    return results
