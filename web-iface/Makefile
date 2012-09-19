CFLAGS=-g -Wall -I/usr/include/python2.7 -I/usr/lib/python2.7/config -lpthread -ldl -lutil -lm -lpython2.7
all:
	gcc -o sys-manager sys-manager.c udv.c external.c ext-iscsi.c ../udv/list.c ../udv/libudv.c $(CFLAGS) -lparted

clean:
	rm -fr sys-manager
