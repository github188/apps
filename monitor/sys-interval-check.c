#include <signal.h>
#include "sys-global.h"
#include "sys-interval-check.h"

struct list _g_capture;

void _value_check(int value, sys_capture_t *cap)
{
	char msg[128];

	if (isValid(value) && (value >= cap->min_thr) && (value <= cap->max_thr))
	{
		//write_alarm(conf->_alarm_file, "good");
		sysmon_event("self_run", "env_exception_backout", cap->name, "good");
		return;
	}

	if ( value < cap->min_thr )
		sprintf(msg, "%s模块告警：当前取值 %d 已经超过最低告警值 %d !",
				cap->name, value, cap->min_thr);
	else if ( value > cap->max_thr )
		sprintf(msg, "%s模块告警：当前取值 %d 已经超过最高告警值 %d !",
				cap->name, value, cap->max_thr);

	sysmon_event("self_run", "env_exception_raise", cap->name, msg);
}

void _capture(sys_capture_t *cap)
{
	if (!isExpried(cap))
		return;
	update(cap);

	if (cap->_capture)
		return _value_check(cap->_capture(), cap);

	syslog(LOG_NOTICE, "the capture %s function is invalid! no more value can be captured!", cap->name);
}

void _check_interval()
{
	struct list *n, *nt;

	list_iterate_safe(n, nt, &_g_capture)
	{
		_capture(list_struct_base(n, sys_capture_t, list));
	}
}

void do_interval_check(int sig)
{
	if (sig == SIGALRM)
	{
		signal(SIGALRM, SIG_IGN);
		_check_interval();
		alarm(CHECK_INTVAL);
	}
}
