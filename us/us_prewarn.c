#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <linux/netlink.h>
#include <arpa/inet.h>
#include "us_ev.h"
#include "us_prewarn.h"
#include "vsd_warning.h"
#include "us_disk.h"
#include "../common/log.h"

extern struct ev_loop *us_main_loop;

static struct sockaddr_nl src_addr, dest_addr;

int nl_open(void)
{
	int nl_fd;

	nl_fd = socket(PF_NETLINK, SOCK_RAW, NETLINK_VSD);
	if (nl_fd == -1) {
		printf("%s %s\n", __FUNCTION__, strerror(errno));
		return -1;
	}

	memset(&src_addr, 0, sizeof(src_addr));
	src_addr.nl_family = AF_NETLINK;
	src_addr.nl_pid = getpid();
	src_addr.nl_groups = 0; /* not in mcast groups */

	memset(&dest_addr, 0, sizeof(dest_addr));
	dest_addr.nl_family = AF_NETLINK;
	dest_addr.nl_pid = 0; /* kernel */
	dest_addr.nl_groups = 0; /* unicast */

	return nl_fd;
}

static int nl_write(int fd, void *data, int len)
{
	struct iovec iov[2];
	struct msghdr msg;
	struct nlmsghdr nlh = {0};

	iov[0].iov_base = &nlh;
	iov[0].iov_len = NLMSG_HDRLEN;
	iov[1].iov_base = data;
	iov[1].iov_len = NLMSG_SPACE(len) - NLMSG_HDRLEN;

	nlh.nlmsg_len = NLMSG_SPACE(len);
	nlh.nlmsg_pid = getpid();
	nlh.nlmsg_flags = 0;
	nlh.nlmsg_type = 0;

	memset(&msg, 0, sizeof(msg));
	msg.msg_name= (void *)&dest_addr;
	msg.msg_namelen = sizeof(dest_addr);
	msg.msg_iov = iov;
	msg.msg_iovlen = 2;

	return sendmsg(fd, &msg, 0);
}

static int nl_read(int fd, void *data, int len, int wait)
{
	struct iovec iov[2];
	struct msghdr msg;
	struct nlmsghdr nlh;
	int res;

	iov[0].iov_base = &nlh;
	iov[0].iov_len = NLMSG_HDRLEN;
	iov[1].iov_base = data;
	iov[1].iov_len = NLMSG_ALIGN(len);

	memset(&msg, 0, sizeof(msg));
	msg.msg_name = (void *)&src_addr;
	msg.msg_namelen = sizeof(src_addr);
	msg.msg_iov = iov;
	msg.msg_iovlen = 2;

	res = recvmsg(fd, &msg, wait ? 0 : MSG_DONTWAIT);
	if (res > 0) {
		res -= NLMSG_HDRLEN;
		if (res < 0)
			res = -EPIPE;
		else if (res < iov[1].iov_len)
			printf("read netlink fd (%d) error: received %d"
					" bytes but expected %zd bytes (%d)", fd, res,
					iov[1].iov_len, len);
	}

	return res;
}

static void nl_io_cb(EV_P_ ev_io *w, int r)
{
	struct vsd_warning_info warning_info;
	char disk_slot[32], msg[128];

	if (nl_read(w->fd, &warning_info, sizeof(warning_info), 1) < 0) {
		if ( (EINTR!=errno) && (EAGAIN!=errno) )
		{
			clog(CL_ERROR, "read netlink fd (%d) failed: %s", w->fd, strerror(errno));
			return;
		}
	}

	if (!disk_name2slot(warning_info.disk_name, disk_slot))
	{
		// TODO: log wrning
		// LogInsert(NULL, "SysMon", "Auto", "Warning", msg);
		sprintf(msg, "磁盘 %s 预警，检测到坏块！", disk_slot);
		LogInsert(NULL, "DiskPreWarning", "Auto", "Error", msg);
		return;
	}

	clog(CL_ERROR, "disk pre warning received, but convert disk slot error!");
}

ev_io nl_readable;

int us_prewarn_init(void)
{
	int nl_fd;
	int warning_level = WARNING_LEVEL_3;

	if ((nl_fd = nl_open()) < 0) {
		clog(CL_ERROR, "netlink open failed");
		return -1;
	}

	// set default warning level
	if (nl_write(nl_fd, &warning_level, sizeof(warning_level)) < 0) {
		clog(CL_ERROR, "set warning level error!");
		close(nl_fd);
		return -1;
	}

	ev_io_init(&nl_readable, nl_io_cb, nl_fd, EV_READ);
	ev_io_start(us_main_loop, &nl_readable);

	return 0;
}

void us_prewarn_release(void)
{
	ev_io_stop(us_main_loop, &nl_readable);
}
