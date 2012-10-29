#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>

#ifndef __WEB_IFACE_COMMON
#define __WEB_IFACE_COMMON

// 多语言支持宏
#define _T(...) (__VA_ARGS__)

#define ERROR(x, ...) error_out(_T(x), ## __VA_ARGS__)

void error_out(const char *fmt, ...);

enum {
	MSG_OK = 1,
	MSG_ERROR
};

void return_json_msg(const int type, const char *msg);

#endif/*__WEB_IFACE_COMMON*/
