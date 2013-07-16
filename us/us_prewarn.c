#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <linux/netlink.h>
#include <arpa/inet.h>

#include "clog.h"
#include "safe_popen.h"
#include "script.h"
#include "us_ev.h"
#include "../monitor/sys-mon.h"
#include "disk_utils.h"
#include "vsd_warning.h"
#include "us_prewarn.h"
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

extern struct us_disk_pool us_dp;
static void nl_io_cb(EV_P_ ev_io *w, int r)
{
	struct vsd_warning_info warning_info;
	struct us_disk *disk;
	struct disk_warning_info *dwi;
	char dev[16], msg[128];

	if (nl_read(w->fd, &warning_info, sizeof(warning_info), 1) < 0) {
		if ( (EINTR!=errno) && (EAGAIN!=errno) )
		{
			clog(CL_ERROR, "read netlink fd (%d) failed: %s", w->fd, strerror(errno));
			return;
		}
	}

	sprintf(dev, "/dev/%s", warning_info.disk_name);
	disk = find_disk(&us_dp, dev);
	if (!disk) {
		clog(CL_ERROR, "disk warning, cann't find %s slot!",
			warning_info.disk_name);

		sprintf(msg, "磁盘预警: %s 出现%s, 已修复扇区计数: %u",
			warning_info.disk_name,
			(warning_info.warning_area == (1<<WARNING_AREA_BAD_SECT)) ?
			"新坏块" : "关键坏块", warning_info.mapped_cnt);
		LogInsert(NULL, "DiskWarning", "Auto", "Error", msg);
		return;
	}
	
	dwi = &disk->di.wi;
	dwi->warning_area = warning_info.warning_area;
	dwi->mapped_cnt = warning_info.mapped_cnt;
	/* 最大可修复扇区数不更新，磁盘上线时设置固定值 */

	sprintf(msg, "磁盘预警: 0:%d 出现%s, 已修复扇区计数: %u, "
			"最大可修复扇区数: %u",	disk->slot,
			(dwi->warning_area == (1<<WARNING_AREA_BAD_SECT)) ?
			"新坏块" : "关键坏块", dwi->mapped_cnt,
			dwi->max_map_cnt);
	LogInsert(NULL, "DiskWarning", "Auto", "Error", msg);
	sprintf(msg, "disks=0:%d", disk->slot);
	sysmon_event("disk", "led_blink2s1", msg, "");
	
	/* 启动热替换 */
	if (dwi->mapped_cnt > dwi->max_map_cnt/2 || 
		dwi->warning_area == (1<<WARNING_AREA_SUPER) ||
		dwi->warning_area == (1<<WARNING_AREA_SECT_MAP)) {
		char cmd[128];
		sprintf(cmd, "%s %s hotrep", DISK_SCRIPT, dev);
		safe_system(cmd);
	}
}

ev_io nl_readable;

int us_prewarn_init(void)
{
	int nl_fd;
	int warning_level = WARNING_LEVEL_2;

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
