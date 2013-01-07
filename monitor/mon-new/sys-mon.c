#include <unistd.h>
#include <ev.h>
#include <json/json.h>
#include "sys-event.h"
#include "sys-action.h"

struct mon_io {
	ev_io io;
	int sockfd;
};

static void mon_io_cb(EV_P_ ev_io *w, int r);
static int mon_serv_create();
static struct mon_io mon_io;
static struct ev_loop *mon_loop = NULL;

void mon_release(int sig)
{
	if (mon_loop)
	{
		//ev_io_stop(mon_loop, &mon_io.io);
		//ev_loop_destroy(mon_loop);
	}

	log_release();
}


static void mon_io_cb(EV_P_ ev_io *w, int r)
{
	ssize_t n;
	sys_event_t ev;
	sys_event_conf_t *ec;
	char buff[1024];
	struct json_object *obj;

	struct mon_io *mi = (struct mon_io*)w;
	
	if ( (n=read(mi->sockfd, buff, sizeof(buff)-1)) <= 0 )
	{
	}
	buff[n] = '\0';

	sys_event_zero(&ev);
	obj = json_tokener_parse( buff );
	json_object_object_foreach(obj, key, val) {

		/*
		if ( json_object_get_type(val) == json_type_string )
			sys_event_fill(&ev, key, json_object_get_string(val));
		*/
		sys_event_fill(&ev, key, json_object_to_json_string(val));
	}
	
	if ( (ec=sys_module_event_get(ev.module, ev.event)) != NULL )
	{
		sys_module_event_update(ec);
		ev.level = ec->level;
		do_sys_action(ec->action, &ev);
		return;
	}

	// TODO:记录出错日志
}

int mon_serv_create()
{
	return 0;
}

int main()
{
	// set signal
	signal(SIGPIPE, SIG_IGN);
	signal(SIGTERM, mon_release);
	signal(SIGINT, mon_release);

	log_init();
	sys_mon_load_conf();

	dump_module_event();
	dump_action_alarm();

	while(1);

	mon_io.sockfd = mon_serv_create();

	// ev loop
	mon_loop = EV_DEFAULT;
	ev_io_init(&mon_io.io, mon_io_cb, mon_io.sockfd, EV_READ);
	ev_io_start(mon_loop, &mon_io.io);
	ev_run(mon_loop, 0);

	mon_release(-1);

	return 0;
}
