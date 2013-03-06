d=$(shell date)

all:
	echo "Build Date: "$d > .build-date
	gcc -o pic-version pic-version.c -L../pic_ctl -lpic

clean:
	rm -f ./.build-date pic-version
