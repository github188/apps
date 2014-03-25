all:
	gcc -o tools-test-led led-test.c ../led-ctl/cmd/libled.a -L../pic_ctl -lpic
ifneq ($(STRIP),)
	$(STRIP) tools-test-led
endif

clean:
	rm -fr a.out tools-test-led *.o core*
