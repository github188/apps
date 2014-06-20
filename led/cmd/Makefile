LIBLED += ./libled.a
OBJECTS := led-ctl.o libled.o
ifdef only-interface
	CFLAGS += -DONLY_INTERFACE
endif

all: led-ctl disk_reset libled.a libled.so libdiskpw.a libdiskpw.so

led-ctl: $(OBJECTS) libled.a
	$(CC) $(CFLAGS) -o $@ $^
ifneq ($(STRIP),)
	$(STRIP) $@
endif

disk_reset: disk_reset.o libdiskpw.a
	$(CC) $(CFLAGS) -o $@ $^
ifneq ($(STRIP),)
	$(STRIP) $@
endif


libled.so: libled.c ../daemon/sysled.c ../../pic_ctl/pic_ctl.c
	$(CC) $(CFLAGS) -fPIC -shared -o $@ $^
ifneq ($(STRIP),)
	$(STRIP) $@
endif

libled.a: libled.o ../daemon/sysled.o
	ar x ../../pic_ctl/libpic.a
	ar -rcs $@ $^ pic_ctl.o

libdiskpw.so: libdiskpw.c
	$(CC) $(CFLAGS) -fPIC -shared -o $@ $^
ifneq ($(STRIP),)
	$(STRIP) $@
endif

libdiskpw.a: libdiskpw.o ../../pic_ctl/pic_ctl.c
	ar -rcs $@ $^ pic_ctl.o

clean:
	rm -rf *.o led-ctl *.a *.so disk_reset
