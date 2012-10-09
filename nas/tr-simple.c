#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#define BUF_SIZE 10000
#define true 1
#define false 0

char buf[BUF_SIZE];

int main(int argc, char *argv[])
{
	int n;
	int n1;
	char* ptr;
	char* ptr1;
	while(1){
		n = read(0, buf, BUF_SIZE);
		if(n<=0)
			return 0;

		ptr = buf;
		n1 = n;
		while(1){
			ptr1 = (char*)memchr(ptr, '\b', n1);
			if(ptr1 == NULL)
				break;
			*ptr1 = '\n';
			ptr = ptr1+1;
			n1 = buf+n - ptr;
			if(n1 <= 0)
				break;
		}

		write(1, buf, n);
		fflush(stdout);
	}
	return 0;
}

