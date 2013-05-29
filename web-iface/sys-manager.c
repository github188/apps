#include "web-iface.h"

struct cmd_map cmd_map[] = {
  {"udv", udv_main},
  {"disk", python_cmd_main},
  {"vg", python_cmd_main},
  {"iscsi", python_cmd_main},
  {"nas", python_cmd_main},
  {"network", python_cmd_main},
  {"nasconf", python_cmd_main},
  {"adminmanage", python_cmd_main},
  {"usermanage", python_cmd_main},
  {"version", version_main},
  {"log", log_main},
  {"loglist", python_cmd_main},
  {"sysconfig", python_cmd_main},
  {"system", python_cmd_main},
  {"web", python_cmd_main},
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
	printf("      adminmanage - WEB管理员管理\n");
	printf("      usermanage - NAS用户管理\n");
	printf("      sysconfig  - 配置系统参数\n");
	printf("      system    - 系统信息、系统状态、系统参数、告警\n");
	printf("      web	- WEB站点设置\n");
	printf("      version   - 查看版本号\n");
	exit(0);
}

void input_wrong()
{
	fprintf(stdout, "{\"status\":\"false\", \"msg\":\"输入的子命令不正确!\"}\n");
}

/* 调用远程命令 */
int remote_exec(int argc, char *argv[])
{
	return 0;
}

int main(int argc, char *argv[])
{
	char *cmd_name;
	char **cmd_argv;
	int cmd_argc;
	int offset = 1;
	struct cmd_map *p = &cmd_map[0];

	//DUMP_PARM(argc, argv);

	// 去掉绝对路径
	cmd_name = last_path_component(argv[0]);

	// 直接调用
	if (!strcmp(cmd_name, "sys-manager"))
	{
		// 输入参数是否符合要求
		if ( argc < 2 )
			usage();

		if ( !strncmp(argv[1], "-h", 2))
			remote_exec(argc-2, (argv+2));

		if ( !strncmp(argv[1], "--debug", 7) )
		{
			g_debug = 1;
			offset = 2;
		}
		cmd_name = argv[offset];
		cmd_argc = argc - offset;
		cmd_argv = argv + offset;
	}
	else
	{
		// 通过软链接调用
		cmd_name += 4;  // 去掉开头'wis_'
		cmd_argc = argc;
		cmd_argv = argv;
	}

	//DBGP("cmd_name: %s", cmd_name);

	// 使用链接方式，检查输入命令
	while (p->cmd)
	{
		if (!strcmp(cmd_name, p->name))
			return p->cmd(cmd_argc, cmd_argv);
		p++;
	}

	input_wrong();

	return 0;
}
