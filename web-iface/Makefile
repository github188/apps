all:
	gcc -g -o sys-manager sys-manager.c udv.c external.c ext-iscsi.c -L../udv -ludv -lparted -Wall -I/usr/include/python2.7 -I/usr/lib/python2.7/config -lpthread -ldl -lutil -lm -lpython2.7

clean:
	rm -fr sys-manager
