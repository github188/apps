objects=libudv.o list.o

libudv.a : $(objects)
	$(AR) -rcs libudv.a $(objects)

%.o:%.c
	$(CC) $(CFLAGS) -c $< -o $@

all: libudv.a

clean:
	rm -fr libudv.a $(objects)
