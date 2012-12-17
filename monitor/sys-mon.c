#include <unistd.h>
#include <signal.h>
#include <stdbool.h>
#include "sys-mon.h"

void mon_event(mon_conf_t *conf)
{
	char msg[256] = {0};
	int value;


	if (!isExpried(conf))
		return;
	update(conf);

	if (!isExecutable(conf))
	{
		syslog(LOG_ERR, "mod: %s , the capture function is not executable!", conf->name);
		return;
	}

	if ( (value = conf->_capture()) < 0 )
	{
		syslog(LOG_INFO, "capture value invalid! (mod: %s val: %d)", conf->name, value);
		return;
	}

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
		char _tmp[128];
		sprintf(_tmp, "%d", value);
		write_alarm(conf->_alarm_file, _tmp);
		raise_alarm(conf->name, msg);
	}
	else
	{
		write_alarm(conf->_alarm_file, "good");
	}
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
	mon_alarm_load();
}

void mon_fini()
{
	syslog(LOG_ERR, "SIGINT or SIGTERM received!");
	mon_conf_release();
	mon_alarm_release();
	log_release();
	exit(0);
}

void mon_reload()
{
	syslog(LOG_INFO, "SIGHUP recieved!\n");
	mon_conf_reload();
	mon_alarm_reload();
}

/* -------------------------------------------------------------------------- */
/*  test                                                                      */
/* -------------------------------------------------------------------------- */

#ifndef NDEBUG
void test()
{
#if 1
	create_default_conf("/tmp/sys/abc/test.xml", MON_CONF_CONTENT);
	return;

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
	signal(SIGHUP, mon_reload);

	while(true)
	{
		check_interval();
		sleep(5);
	}
#else
	test();
#endif
	return 0;
}
