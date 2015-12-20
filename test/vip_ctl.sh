#!/bin/bash
if [ "$1" = "start" ]
then
ifconfig eth0:1 192.168.237.131 broadcast 192.168.237.255 netmask 255.255.255.0
ifconfig
elif [ "$1" = "stop" ]
then
ifconfig eth0:1 down
ifconfig
else
ifconfig
fi
