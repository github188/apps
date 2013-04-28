#include <signal.h>
#include "../common/log.h"
#include "sys-mon.h"
#include "sys-global.h"
#include "sys-interval-check.h"

struct list _g_capture;

static const char *MOD_NAME(const char *mod)
{
	int i;
	static char _not_found[2] = "";

	for (i=0;mod_cap_list[i];i++)
	{
		if (!strcmp(mod_cap_list[i], mod))
			return mod_ch_name[i];
	}

	return _not_found;
}


int _value_check_error(int value, sys_capture_t *cap, char *msg)
{
#ifdef _DEBUG
	printf(" value: %d, min: %d, max: %d\n", value, cap->min_thr, cap->max_thr);
#endif

	if ( value < cap->min_thr )
	{
		sprintf(msg, "当前取值 %d, 未达到最低值 %d", value, cap->min_thr);
		return VAL_ERROR;
	}
	else if ( value > cap->max_thr )
	{
		sprintf(msg, "当前取值 %d, 已超过最高值 %d", value, cap->max_thr);
		return VAL_ERROR;
	}

	return VAL_NORMAL;
}

void _capture(sys_capture_t *cap)
{
	char msg[128] = {0};
	char log_msg[256] = {0};
	int _cur_error = VAL_ERROR;

#ifndef _DEBUG
	if (!isExpried(cap))
		return;
	update(cap);
#else
	printf(" handler: %.8x", cap->_capture);
#endif/*_DEBUG*/

	if (!cap->_capture)
	{
		syslog(LOG_NOTICE, "the capture %s function is invalid, "
				"no more value can be captured.", cap->name);
		return;
	}

	if (cap->_preset)
	{
		_cur_error = _value_check_error(cap->_capture(NULL), cap, msg);
	}
	else
	{
		_cur_error = cap->_capture(msg);
	}

	/* 出错的值仅处理一次 */
	if (VAL_WARNING == _cur_error)
	{
		if (VAL_NORMAL == cap->_error)
		{
			cap->_error = VAL_WARNING;
			sprintf(log_msg, "监控模块%s告警: %s", MOD_NAME(cap->name), msg);
			LogInsert(NULL, "SysMon", "Auto", "Warning", log_msg);
		}
	}
	else if (VAL_ERROR == _cur_error)
	{
		if (cap->_error != VAL_ERROR)
		{
			cap->_error = VAL_ERROR;
			sysmon_event("self_run", "env_exception_raise", cap->name, msg);
			sprintf(log_msg, "监控模块%s告警: %s", MOD_NAME(cap->name), msg);
			LogInsert(NULL, "SysMon", "Auto", "Error", log_msg);
		}
	}
	else if (cap->_error != VAL_NORMAL)
	{
		if (VAL_ERROR == cap->_error)
			sysmon_event("self_run", "env_exception_backout", cap->name, "good");
		
		cap->_error = VAL_NORMAL;
		sprintf(log_msg, "监控模块%s告警解除", MOD_NAME(cap->name));
		LogInsert(NULL, "SysMon", "Auto", "Error", log_msg);
	}
}

void _check_interval()
{
	struct list *n, *nt;
	sys_capture_t *cap;

#ifdef _DEBUG
	printf("enter _check_interval()\n");
#endif

	list_iterate_safe(n, nt, &_g_capture)
	{
		cap = list_struct_base(n, sys_capture_t, list);
#ifdef _DEBUG
		printf("capture: %s", cap->name);
#endif
		_capture(cap);
	}
}

void do_interval_check(int sig)
{
	if (sig == SIGALRM)
	{
		signal(SIGALRM, SIG_IGN);
		_check_interval();
		signal(SIGALRM, do_interval_check);
		alarm(CHECK_INTVAL);
	}
}

void dump_self_run()
{
	struct list *n, *nt;
	sys_capture_t *cap;

	puts("------------------- dump capture -------------------");
	list_iterate_safe(n, nt, &_g_capture)
	{
		cap = list_struct_base(n, sys_capture_t, list);
		printf("capture: %.8x %s\n", cap, cap->name);
		printf("\tcheck interval: %d\n", cap->check_intval);
		printf("\tmin: %d\n", cap->min_thr);
		printf("\tmax: %d\n", cap->max_thr);
		printf("\t_error: %d\n", cap->_error);
		printf("\t_preset: %d\n", cap->_preset);
	}
}
