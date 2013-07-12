#include "web-iface.h"

struct cmd_map cmd_map[] = {
	{"udv", udv_main},
	{"disk", exec_new_cmd},
	{"vg", exec_new_cmd},
	{"iscsi", exec_new_cmd},
	{"nas", exec_new_cmd},
	{"network", exec_new_cmd},
	{"nasconf", exec_new_cmd},
	{"adminmanage", exec_new_cmd},
	{"usermanage", exec_new_cmd},
	{"version", version_main},
	{"log", log_main},
	{"loglist", exec_new_cmd},
	{"sysconfig", exec_new_cmd},
	{"system", exec_new_cmd},
	{"web", exec_new_cmd},
	{"license", exec_new_cmd},
	{"shareacl", exec_new_cmd},
	{"configbak", exec_new_cmd},
	{"", NULL}
};

int g_debug = 0;

void usage()
{
	printf("Usage: [--debug] 子命令 用于调试子命令参数输出\n");
	printf("请输入子命令!\n");
	printf("      disk      - 磁盘接口\n");
	printf("      vg        - 卷组接口\n");
	printf("      udv       - 用户数据卷接口\n");
	printf("      iscsi     - iSCSI接口\n");
	printf("      nas       - NAS接口\n");
	printf("      network   - 网络管理\n");
  	printf("      nasconf   - NAS配置文件接口\n");
	printf("      log       - 日志\n");
	printf("      loglist   - 获取日志\n");
	printf("      license   - license控制\n");
	printf("      adminmanage - WEB管理员管理\n");
	printf("      usermanage - NAS用户管理\n");
	printf("      sysconfig  - 配置系统参数\n");
	printf("      system    - 系统信息、系统状态、系统参数、告警\n");
	printf("      configbak - 配置文件自动备份接口\n");
	printf("      web	- WEB站点设置\n");
	printf("      shareacl	- 共享目录权限配置\n");
	printf("      version   - 查看版本号\n");
	exit(0);
}

void input_wrong()
{
	fprintf(stdout, "{\"status\":\"false\", \"msg\":\"输入的子命令不正确!\"}\n");
}

int main(int argc, char *argv[])
{
	int offset = 1;
	struct cmd_map *p = &cmd_map[0];

	// 输入参数是否符合要求
	if (argc < 2)
		usage();

	if (!strcmp(argv[1], "--debug")) {
		g_debug = 1;
		offset = 2;
	}

	while (p->cmd) {
		if (!strcmp(argv[offset], p->name))
			return p->cmd(argc - offset, &argv[offset]);
		p++;
	}

	input_wrong();
	return 0;
}
