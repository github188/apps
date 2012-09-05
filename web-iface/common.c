#include "common.h"

void error_out(const char *fmt, ...)
{
	va_list arg_ptr;

	fprintf(stderr, "ERR:");
	va_start(arg_ptr, fmt);
	fprintf(stderr, fmt, arg_ptr);
	va_end(arg_ptr);
	fprintf(stderr, "\n");
	exit(-1);
}
