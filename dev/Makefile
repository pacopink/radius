FREERADIUS_PATH=/ocg/freeradius-server-3.0.8
CC = gcc

DEBUG = -g -fPIC -Wall -pthread 
CFLAGS = $(DEBUG) -I. -I./inc -I$(FREERADIUS_PATH)/src -I$(PYTHON_PATH)
FREERADIUS_LIBS = -L./lib -leap -L./libs -lfreeradius-server -lfreeradius-eap -lfreeradius-server -lradiusbase
LIBS=-lpthread -ldl -lc -lm -lrt -lnsl 

PYTHON_PATH=/usr/include/python2.6/

OBJS_PY= eap_util.o 

eap_util.so: $(OBJS_PY)
	    @echo Linking $(TARGET)
		$(CC) -fPIC -Xlinker -export-dynamic -shared -o $@ $(OBJS_PY)  $(FREERADIUS_LIBS) $(LIBS)

all:test

clean:
	rm -rf *.o test



test:test_eap_sim.o
	$(CC) $(CFLAGS) -o $@ $^ $(FREERADIUS_LIBS) $(LIBS)


.cpp.o:
	@echo "Compiling $<"
	$(CC) $(CFLAGS) -c $< -o $@
	@echo "Done"
	@echo

.c.o:
	@echo "Compiling $<"
	$(CC) $(CFLAGS) -c $< -o $@
	@echo "Done"
	@echo
