PYFLAGS=`python-config --includes`
CFLAGS=-g -Wall -lpthread -ldl -lutil -lm
CFLAGS+=${PYFLAGS}

all:
	./version-info.sh
	gcc -o sys-manager sys-manager.c cmd-log.c udv.c exec-new-cmd.c common.c version.c -L../udv -ludv -lparted -L../common -llog -lsqlite3 $(CFLAGS) 
	./version-info.sh clean

clean:
	rm -fr sys-manager
