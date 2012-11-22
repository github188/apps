CFLAGS=-g -Wall -I/usr/include/python2.7 -I/usr/lib/python2.7/config -lpthread -ldl -lutil -lm -lpython2.7
all:
	./version-info.sh
	gcc -o sys-manager sys-manager.c cmd-log.c udv.c external.c ext-python-cmd.c ../udv/list.c ../udv/libudv.c common.c version.c $(CFLAGS) -lparted -L../common -llog -lsqlite3
	./version-info.sh clean

clean:
	rm -fr sys-manager
