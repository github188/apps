#include <unistd.h>
#include <signal.h>
#include <stdbool.h>
#include "sys-mon.h"

void mon_event(mon_conf_t *conf, int value)
{
	char msg[256] = {0};

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
	{
		// 写日志
		raise_alarm(conf->name, msg);
	}
}


void int_check(int sig)
{
	struct list *n, *nt;
	int value;
	mon_conf_t *item;

	if (sig!=SIGALRM)
		return;

	if (list_empty(&gconf))
		return;

	list_iterate_safe(n, nt, &gconf);
	log_release();
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
	printf("test load conf!\n");
	printf("load: %d\n", mon_conf_load());
	//dump_mon_conf();

	mon_conf_reload();
	//dump_mon_conf();

	mon_conf_release();
}
#endif

int main()
{
#ifdef NDEBUG
	daemon(0, 0);

	signal(SIGALRM, int_check);
	signal(SIGTERM, mon_fini);
	signal(SIGINT, mon_fini);
#else
	test();
#endif
	return 0;
}
