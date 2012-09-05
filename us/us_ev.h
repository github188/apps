#ifndef US_EV_h
#define US_EV_H

#include <ev.h>

struct us_shell_cmd;

struct us_shell_cmd_ops {
	const char *cmd;

	void (*on_read)(struct ev_loop *ev, struct us_shell_cmd *cmd, int fd);
	void (*on_done)(struct ev_loop *ev,
	                struct us_shell_cmd *scmd, int status);
	int timeout;
};

struct us_shell_cmd {
	int		need_timer : 1;
	int		need_io : 1;

	ev_child	child;
	ev_io		pipe_io;
	ev_timer	timer;
	void		(*on_read)(struct ev_loop *l,
			           struct us_shell_cmd *scmd, int fd);
	void		(*on_done)(struct ev_loop *l,
			           struct us_shell_cmd *scmd, int status);
};


extern struct ev_loop *us_main_loop;
extern int us_ev_init(void);
extern void us_ev_release(void);

static inline void us_loop(void)
{
	ev_run(us_main_loop, 0);
}

#endif
