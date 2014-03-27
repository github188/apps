LDFLAGS += ./libled.a
OBJECTS := tools-test-led.o

all: led-ctl libled.a

led-ctl:$(OBJECTS) libled.a
	gcc -o led-ctl $(OBJECTS) $(LDFLAGS)
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
