#include <unistd.h>
#include <signal.h>
#include <stdbool.h>
#include "sys-mon.h"

void mon_event(mon_conf_t *conf)
{
	char msg[256] = {0};
	int value;

	if (!conf)
	{
		// TODO: log
		printf("conf not invalid!\n");
		return;
	}

	value = conf->_capture();

	if ( isValid(conf->min_alr) && (value < conf->min_alr) )
		sprintf(msg, "%s模块告警：当前取值 %d 已经超过最低告警值 %d !",
				conf->name, value, conf->min_alr);
	else if ( isValid(conf->max_alr) && (value > conf->max_alr) )
		sprintf(msg, "%s模块告警：当前取值 %d 已经超过最高告警值 %d !",
				conf->name, value, conf->max_alr);
	else if ( isValid(conf->min_thr) && (value < conf->min_thr) )
		sprintf(msg, "%s模块告警：当前取值 %d 已经超过最低阀值 %d !",
				conf->name, value, conf->min_thr);
	else if ( isValid(conf->max_thr) && (value > conf->max_thr) )
		sprintf(msg, "%s模块告警：当前取值 %d 已经超过最高阀值 %d !",
				conf->name, value, conf->max_thr);
	if (msg[0] != '\0')
		raise_alarm(conf->name, msg);
}

void check_interval()
{
	struct list *n, *nt;

	list_iterate_safe(n, nt, &gconf)
	{
		mon_event(list_struct_base(n, mon_conf_t, list));
	}
}


void sig_alarm(int sig)
{
	if (sig==SIGALRM)
		check_interval();
	alarm(CHECK_INTVAL);
}

void mon_init()
{
	log_init();
	mon_conf_load();
}

void mon_fini()
{
	syslog(LOG_ERR, "监控进程出错退出!");
	mon_conf_release();
	log_release();
}

/* -------------------------------------------------------------------------- */
/*  test                                                                      */
/* -------------------------------------------------------------------------- */

#ifndef NDEBUG
void test()
{
#if 1
	printf("test load conf!\n");
	printf("load: %d\n", mon_conf_load());
	//dump_mon_conf();

	mon_conf_reload();
	//dump_mon_conf();
	mon_conf_release();
#else
	printf("load alarm: %d\n", mon_alarm_load());
	mon_alarm_reload();
	mon_alarm_release();
#endif
}
#endif

int main()
{
#ifdef NDEBUG
	daemon(0, 0);

	mon_init();
	signal(SIGALRM, sig_alarm);
	signal(SIGTERM, mon_fini);
	signal(SIGINT, mon_fini);
#else
	test();
#endif
	return 0;
}
