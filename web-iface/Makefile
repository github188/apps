all:
	echo $(LD_LIBRARY_PATH)
	./version-info.sh
	gcc -o sys-manager sys-manager.c cmd-log.c udv.c exec-new-cmd.c common.c version.c ../udv/libudv.a -lparted ../common/liblog.a -lsqlite3 $(CFLAGS) 
	./version-info.sh clean
ifneq ($(STRIP),)
	$(STRIP) sys-manager
endif
clean:
	rm -fr sys-manager
