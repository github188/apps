d=$(shell date "+%Y-%m-%d %H:%M:%S")

all:
	echo "Build Date: "$d > .build-date
	gcc -o pic-version pic-version.c ../pic_ctl/libpic.a

clean:
	rm -f ./.build-date pic-version
