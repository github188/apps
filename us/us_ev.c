#include <ev.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include "types.h"
#include "clog.h"
#include "us_ev.h"
#include "safe_popen.h"

struct ev_loop *us_main_loop;

int us_ev_init(void)
{
	us_main_loop = EV_DEFAULT;
	if (us_main_loop == NULL)
		return -1;

	return 0;
}

void us_ev_release(void)
{
	ev_loop_destroy(us_main_loop);
}

#define ev_io_to_usc(w) container_of(w, struct us_shell_cmd, pipe_io)
#define ev_timer_to_usc(w) container_of(w, struct us_shell_cmd, timer)
#define ev_child_to_usc(w) container_of(w, struct us_shell_cmd, child)

static void us_shell_done(struct ev_loop *loop, ev_child *w, int r)
{
	struct us_shell_cmd *usc = ev_child_to_usc(w);

	usc->on_done(loop, usc, w->rstatus);
}

static void us_shell_on_read(struct ev_loop *loop, ev_io *w, int r)
{
	struct us_shell_cmd *usc = ev_io_to_usc(w);

	usc->on_read(loop, usc, usc->pipe_io.fd);
}

static void us_shell_on_timeout(struct ev_loop *loop, ev_timer *w, int r)
{
	struct us_shell_cmd *usc = ev_timer_to_usc(w);

	usc->on_done(loop, usc, ETIMEDOUT);
}


int us_shell_cmd_init(struct us_shell_cmd *scmd,
                      struct us_shell_cmd_ops *ops)
{
	struct sp_child sc;
	int ret;
	struct ev_loop *loop = us_main_loop;

	if (ops->on_done == NULL)
		return -1;

	ret = safe_popen(&sc, ops->cmd);
	if (ret < 0)
		return ret;

	memset(scmd, 0, sizeof(*scmd));
	ev_child_init(&scmd->child, us_shell_done, sc.pid, 0);
	ev_child_start(loop, &scmd->child);

	if (ops->on_read) {
		ev_io_init(&scmd->pipe_io, us_shell_on_read, sc.fd, EV_READ);
		ev_io_start(loop, &scmd->pipe_io);
		scmd->need_io = 1;
	} else {
		close(sc.fd);
	}

	if (ops->timeout > 0) {
		ev_timer_init(&scmd->timer, us_shell_on_timeout, ops->timeout, 0.);
		ev_timer_start(loop, &scmd->timer);
		scmd->need_timer = 1;
	}
	scmd->on_read = ops->on_read;
	scmd->on_done = ops->on_done;

	return 0;
}

void us_shell_cmd_release(struct us_shell_cmd *scmd)
{
	struct ev_loop *loop = us_main_loop;

	ev_child_stop(loop, &scmd->child);
	if (scmd->need_io) {
		ev_io_stop(loop, &scmd->pipe_io);
		close(scmd->pipe_io.fd);
	}
	ev_timer_stop(loop, &scmd->timer);
}
