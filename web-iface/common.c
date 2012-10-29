#include <stdio.h>
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

void return_json_msg(const int type, const char *msg)
{
	if (MSG_OK == type)
	{
		fprintf(stdout, "{\"status\":true, \"msg\":\"%s\"}\n", msg);
		exit(0);
	}
	else
	{
		fprintf(stdout, "{\"status\":false, \"msg\":\"%s\"}\n", msg);
		exit(-1);
	}
}
