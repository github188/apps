CFLAGS=${CFLAG} -Wall #-g

all:
	./version-info.sh
	gcc -o sys-manager sys-manager.c cmd-log.c udv.c exec-new-cmd.c common.c version.c ../udv/libudv.a -lparted ../common/liblog.a -lsqlite3 $(CFLAGS) 
	./version-info.sh clean

clean:
	rm -fr sys-manager
