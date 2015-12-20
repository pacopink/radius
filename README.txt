cp this directory to /radius
Add env:
export OCG_HOME=/radius
export LD_LIBRARY_PATH=$OCG_HOME/libs:$LD_LIBRARY_PATH
export PATH=$OCG_HOME/bin:$PATH
export PYTHONPATH=$OCG_HOME/config:$OCG_HOME/modules:$PYTHONPATH
