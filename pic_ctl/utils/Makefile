all:
	gcc -o disk_reset disk_reset.c  ../libpic.a
ifneq ($(STRIP),)
	$(STRIP) disk_reset
endif

clean:
	rm -fr disk_reset *.o
