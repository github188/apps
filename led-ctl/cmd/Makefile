LIBLED += ./libled.a
OBJECTS := led-ctl.o libled.o
ifdef only-interface
	CFLAGS += -DONLY_INTERFACE
endif

all: led-ctl libled.a

led-ctl: $(OBJECTS) libled.a
	$(CC) -o led-ctl led-ctl.c $(CFLAGS) $(LIBLED)
ifneq ($(STRIP),)
	$(STRIP) led-ctl
endif

libled.a: libled.o 
	ar x ../../pic_ctl/libpic.a
	ar -rcs libled.a pic_ctl.o libled.o ../daemon/sysled.o

clean:
	rm -rf *.o led-ctl *.a
