all:
	gcc -o led-test led-test.c ../monitor/util-gpio.c -L../pic_ctl -lpic
	gcc -o pic-version pic-version.c -L../pic_ctl -lpic

clean:
	rm -fr a.out led-test *.o core* pic-version
