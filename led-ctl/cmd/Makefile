LDFLAGS += ./libled.a
OBJECTS := led-ctl.o
ifdef only-interface
	CFLAGS += -DONLY_INTERFACE
endif
all: led-ctl libled.a

led-ctl: $(OBJECTS) libled.a
	gcc -o led-ctl $(OBJECTS) $(CFLAGS) $(LDFLAGS)
ifneq ($(STRIP),)
	$(STRIP) led-ctl
endif

libled.a:sysled.o 
	ar x ../../pic_ctl/libpic.a
	gcc -c libled.c
	ar -rcs libled.a pic_ctl.o libled.o ../daemon/sysled.o
sysled.o:
	$(MAKE) -C ../daemon

clean:
	rm -rf *.o led-ctl *.a
