#include <libudev.h>
#include <stdint.h>
#include <regex.h>
#include <errno.h>
#include <string.h>

#include "clog.h"
#include "us_ev.h"
#include "types.h"
#include "us_mon.h"

#define MAX_SLOT	(128)

struct us_mon {
	struct udev		*udev;
	struct udev_monitor	*mon;

	ev_io			udev_io;
	struct list		mon_list;
};

static struct us_mon us_mon;

static void us_mon_do_action(const char *path, const char *dev, int act)
{
	struct list *p;

	list_for_each(p, &us_mon.mon_list) {
		struct mon_node *e = list_entry(p, struct mon_node, list);

		if (e->on_event(path, dev, act) == MA_HANDLED)
			break;
	}
}

static void udev_io_cb(EV_P_ ev_io *w, int r)
{
	struct us_mon *ud = container_of(w, struct us_mon, udev_io);
	struct udev_device *dev;
	const char *path;
	const char *dev_node;
	const char *action;
	int act;

	dev = udev_monitor_receive_device(ud->mon);
	if (dev == NULL)
		return;
	path = udev_device_get_devpath(dev);
	dev_node = udev_device_get_devnode(dev);
	action = udev_device_get_action(dev);
	printf("*** Get %s, event: %s\n", dev_node, action);

	if (path == NULL || dev_node == NULL || action == NULL)
		goto out;

	if (strcmp(action, "add") == 0)
		act = MA_ADD;
	else if (strcmp(action, "remove") == 0)
		act = MA_REMOVE;
	else
		act = MA_CHANGE;

	us_mon_do_action(path, dev_node, act);
out:
	udev_device_unref(dev);
}

int us_mon_init(void)
{
	struct udev *udev;
	struct udev_monitor *mon;

	memset(&us_mon, sizeof(us_mon), 0);
	init_list(&us_mon.mon_list);

	udev = udev_new();
	if (udev == NULL) {
		clog(LOG_EMERG, "Udev init failed\n");
		return -1;
	}
	mon = udev_monitor_new_from_netlink(udev, "udev");
	if (mon == NULL) {
		clog(LOG_EMERG, "Udev monitor init failed\n");
		goto failed_mon;
	}

	if (udev_monitor_filter_add_match_subsystem_devtype(mon,
	                                                    "block",
	                                                    "disk") < 0) {
		clog(LOG_EMERG, "Udev monitor add match failed: %s\n",
		     strerror(errno));
		goto failed_mon;
	}
	udev_monitor_set_receive_buffer_size(mon, 128 * 1024);
	if (udev_monitor_enable_receiving(mon) < 0) {
		clog(LOG_EMERG, "Udev monitor enable failed\n");
		goto failed_enable_mon;
	}
	us_mon.udev = udev;
	us_mon.mon = mon;
	ev_io_init(&us_mon.udev_io, udev_io_cb,
	           udev_monitor_get_fd(mon), EV_READ);
	ev_io_start(us_main_loop, &us_mon.udev_io);

	return 0;

failed_enable_mon:
	udev_monitor_unref(mon);
failed_mon:
	udev_unref(udev);
	return -1;
}

void us_mon_release(void)
{
	ev_io_stop(us_main_loop, &us_mon.udev_io);
	udev_monitor_unref(us_mon.mon);
	udev_unref(us_mon.udev);
}

int us_mon_register_notifier(struct mon_node *node)
{
	list_add_tail(&node->list, &us_mon.mon_list);
	return 0;
}

void us_mon_unregister_notifier(struct mon_node *node)
{
	list_del(&node->list);
}

void us_mon_enum_dev(void)
{
	struct us_mon *ud = &us_mon;
	struct udev *udev = ud->udev;
	struct udev_enumerate *uenum;
	struct udev_list_entry *devs, *dev_list;

	uenum = udev_enumerate_new(udev);
	if (uenum == NULL) {
		clog(LOG_ERR, "%s: alloc enumerator failed: %s\n",
		     __func__, strerror(errno));
		return;
	}

	if (udev_enumerate_add_match_subsystem(uenum, "block") < 0) {
		clog(LOG_ERR, "%s: Add match failed: %s\n",
		     __func__, strerror(errno));
		goto out;
	}

	if (udev_enumerate_scan_devices(uenum) < 0) {
		clog(LOG_ERR, "%s: Scan device failed: %s\n",
		     __func__, strerror(errno));
		goto out;
	}

	devs = udev_enumerate_get_list_entry(uenum);
	udev_list_entry_foreach(dev_list, devs) {
		struct udev_device *dev;
		const char *path;
		const char *node;

		path = udev_list_entry_get_name(dev_list);
		if (path == NULL)
			continue;

		dev = udev_device_new_from_syspath(udev, path);
		if (dev == NULL) {
			clog(LOG_ERR, "%s: create device failed: %s\n",
			     __func__, strerror(errno));
			continue;
		}
		node = udev_device_get_devnode(dev);
		if (node == NULL) {
			clog(LOG_ERR, "%s: create node failed: %s\n",
			     __func__, strerror(errno));
		} else {
			us_mon_do_action(path, node, MA_ADD);
		}
		udev_device_unref(dev);
	}

out:
	udev_enumerate_unref(uenum);
}
