#./radius_transport.py -port 1812 -conf xxx.conf -ln AUTH_TANS001 -t AUTT -d -p
#./radius_transport -port 1812 -conf xxx.conf -ln AUTH_TANS001 -t AUTT -p -logpath /radius/log
#python -m cProfile -o tsp.pyprof ../modules/radius_transport.py -port 1812 -conf xxx.conf -ln AUTH_TANS001 -t AUTT -p -logpath /radius/log
radius_transport -addr 192.168.237.131 -port 1812 -conf xxx.conf -ln AUTH_TANS001 -t AUTT -p -logpath /radius/log  $*
