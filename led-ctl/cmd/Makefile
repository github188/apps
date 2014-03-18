CFLAGS += -Wstrict-aliasing=0
CFLAGS += -std=c99
ifdef debug
CFLAGS += -D_DEBUG -g -Wall
else
CFLAGS += -O2 -Wall
endif
LDFLAGS += -L./ -lled
OBJECTS := tools-test-led.o

all: tools-test-led libled.a

tools-test-led:$(OBJECTS) libled.a
	gcc -o tools-test-led $(OBJECTS) $(LDFLAGS)
ifneq ($(STRIP),)
	$(STRIP) tools-test-led
	$(STRIP) libled.a
endif

libled.a:sysled.o 
	ar x ../../pic_ctl/libpic.a
	gcc -c libled.c
	ar -rcs libled.a pic_ctl.o libled.o ../daemon/sysled.o
sysled.o:
	$(MAKE) -C ../daemon

clean:
	rm -rf *.o tools-test-led *.a
