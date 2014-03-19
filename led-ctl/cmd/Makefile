LDFLAGS += ./libled.a
OBJECTS := tools-test-led.o

all: tools-test-led libled.a

tools-test-led:$(OBJECTS) libled.a
	gcc -o tools-test-led $(OBJECTS) $(LDFLAGS)
ifneq ($(STRIP),)
	$(STRIP) tools-test-led
endif

libled.a:sysled.o 
	ar x ../../pic_ctl/libpic.a
	gcc -c libled.c
	ar -rcs libled.a pic_ctl.o libled.o ../daemon/sysled.o
sysled.o:
	$(MAKE) -C ../daemon

clean:
	rm -rf *.o tools-test-led *.a
