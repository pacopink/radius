#!/bin/bash
time radclient -c 50 192.168.237.130:1812 auth abc123 < pap.txt &
time radclient -c 50 192.168.237.130:1812 auth abc123 < pap1.txt &
