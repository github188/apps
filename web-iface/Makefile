CFLAGS=-g -Wall -I/usr/include/python2.7 -I/usr/lib/python2.7/config -lpthread -ldl -lutil -lm -lpython2.7
all:
	./version-info.sh
	gcc -o sys-manager sys-manager.c cmd-log.c udv.c external.c ext-python-cmd.c ../udv/list.c ../udv/libudv.c $(CFLAGS) -lparted ../common/log.c common.c version.c
	./version-info.sh clean

clean:
	rm -fr sys-manager
