#include <ev.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <string.h>
#include <errno.h>

#include "types.h"
#include "clog.h"
#include "us_ev.h"

/* Each session can keep 10s */
#define TIMEOUT	(10.)
#define MAX_BUF (1023)
#define US_PORT (9000)

static ev_io us_server_io;

struct us_session {
	ev_io 		us_io;
	ev_timer	us_timer;
	char		buf[MAX_BUF];
	int		buf_len;
};

static inline int fd_nonblock(int fd)
{

	return fcntl(fd, F_SETFL, O_NONBLOCK);

}

static void us_sess_release(struct us_session *sess)
{
	ev_timer_stop(us_main_loop, &sess->us_timer);
	ev_io_stop(us_main_loop, &sess->us_io);
	shutdown(sess->us_io.fd, SHUT_RDWR);
	close(sess->us_io.fd);
	free(sess);
	return;
}

static int us_parse(struct us_session *sess)
{
	int i;
	int eol = 0;
	extern int us_do_cmd(int fd, char *buf);

	for (i = sess->buf_len; i--; ) {
		if (sess->buf[i] == '\n' || sess->buf[i] == '\r') {
			eol = 1;
			break;
		}
	}

	if (eol == 0) {
		if (sess->buf_len >= sizeof(sess->buf))
			return -1;
		else
			return 0;
	}
	while (i >= 0 && (sess->buf[i] == '\n' || sess->buf[i] == '\r'))
		i--;
	if (i < 0)
		return -1;

	sess->buf[i + 1] = '\0';
	us_do_cmd(sess->us_io.fd, sess->buf);
	return 1;
}

static void us_sess_on_io(EV_P_ ev_io *w, int r)
{
	struct us_session *sess = container_of(w,
	                                       struct us_session,
	                                       us_io);
	int ret;
	int l;
	char *buf = &sess->buf[sess->buf_len];

	l = sizeof(sess->buf) - sess->buf_len;
	ret = read(w->fd, buf, l);
	if (ret < 0)
		if (errno == EAGAIN || errno == EWOULDBLOCK)
			return;

	if (ret <= 0) {
		us_sess_release(sess);
		return;
	}

	sess->buf_len += l;
	if (us_parse(sess)) {
		us_sess_release(sess);
	}
}

static void us_sess_on_timeout(EV_P_ ev_timer *w, int r)
{
	struct us_session *sess = container_of(w,
	                                       struct us_session,
	                                       us_timer);

	clog(LOG_ERR, "%s: session timeout\n", __func__);
	us_sess_release(sess);
}

struct us_session * us_sess_new(int fd)
{
	struct us_session *sess = calloc(1, sizeof(*sess));

	if (sess) {
		ev_io_init(&sess->us_io, us_sess_on_io,
		           fd, EV_READ);
		ev_timer_init(&sess->us_timer, us_sess_on_timeout,
		              TIMEOUT, 0);
		ev_io_start(us_main_loop, &sess->us_io);
		ev_timer_start(us_main_loop, &sess->us_timer);
	}

	return sess;
}

static int new_server(int port)
{
	int fd;
	int opt = 1;
	struct sockaddr_in addr;


	fd = socket(AF_INET, SOCK_STREAM, 0);
	if (fd < 0)
		return -1;
	setsockopt(fd, SOL_SOCKET, SO_REUSEADDR,
	           &opt, sizeof(opt));
	memset(&addr, 0, sizeof(addr));
	addr.sin_family = AF_INET;
	addr.sin_family = AF_INET;

	addr.sin_port = htons(port);
	inet_pton(AF_INET, "127.0.0.1", &addr.sin_addr);
	if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
		clog(LOG_ERR, "Bind sock failed\n");
		close(fd);
		return -1;
	}

	if (listen(fd, 5) < 0) {
		clog(LOG_ERR, "Listen sock failed\n");
		close(fd);
		return -1;
	}

	return fd;
}

static void us_server_io_cb(EV_P_ ev_io *w, int r)
{
	int sock;
	struct us_session *sess;

	sock = accept(w->fd, NULL, NULL);
	if (sock < 0)
		return;
	sess = us_sess_new(sock);
	if (sess == NULL) {
		close(sock);
	}
}

int us_session_init(void)
{
	int fd = new_server(US_PORT);
	if (fd < 0)
		return -1;

	fd_nonblock(fd);
	ev_io_init(&us_server_io, us_server_io_cb,
	           fd, EV_READ);
	ev_io_start(us_main_loop, &us_server_io);

	return 0;
}

void us_session_release(void)
{
	ev_io_stop(us_main_loop, &us_server_io);
	close(us_server_io.fd);
}


