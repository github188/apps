all:
	gcc -o tools-test-led led-test.c ../monitor/util-gpio.c -L../pic_ctl -lpic
ifneq ($(STRIP),)
	$(STRIP) tools-test-led
endif

clean:
	rm -fr a.out tools-test-led *.o core*
