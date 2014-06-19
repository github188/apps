LIBLED += ./libled.a
OBJECTS := led-ctl.o libled.o
ifdef only-interface
	CFLAGS += -DONLY_INTERFACE
endif

all: led-ctl diskpower-ctl libled.a libled.so

led-ctl: $(OBJECTS) libled.a
	$(CC) $(CFLAGS) -o $@ $^
ifneq ($(STRIP),)
	$(STRIP) $@
endif

diskpower-ctl: diskpower-ctl.o libled.a
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

clean:
	rm -rf *.o led-ctl *.a *.so diskpower-ctl
