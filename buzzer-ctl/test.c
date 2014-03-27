#include <stdio.h>
#include <stdlib.h>
#include "./cmd/libbuzzer.h"

int main(int argc, char *argv[])
{
	int a;

	buzzer_get(&a);
	printf("buzzer: %d\n", a);
	return 0;
}
