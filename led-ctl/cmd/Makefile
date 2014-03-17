OBJECTS := tools-test-led.o libled.o ../daemon/i2c_dev.o
LIBS := -L./ -lled

all: tools-test-led libled.a

tools-test-led:$(OBJECTS) libled.a
	gcc -o tools-test-led $(OBJECTS) $(LIBS)

libled.a:libpic.a i2c_dev.o
	cp ../../pic_ctl/libpic.a ./
	ar x libpic.a
	gcc -c libled.c
	ar -rcs libled.a pic_ctl.o libled.o ../daemon/i2c_dev.o
	rm -rf pic_ctl.o libpic.a
libpic.a:
	$(MAKE) -C ../../pic_ctl
i2c_dev.o:
	$(MAKE) -C ../daemon

clean:
	rm -rf *.o tools-test-led *.a
