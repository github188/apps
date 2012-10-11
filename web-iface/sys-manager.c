#include "web-iface.h"

struct cmd_map cmd_map[] = {
  {"udv", udv_main},
  {"disk", external_main},
  {"vg", external_main},
  {"iscsi", python_cmd_main},
  {"nas", python_cmd_main},
  {"", NULL}
};

void usage()
{
  printf("请输入子命令!\n");
  printf("    支持的子命令:\n");
  printf("      disk  - 磁盘接口\n");
  printf("      vg    - 卷组接口\n");
  printf("      udv   - 用户数据卷接口\n");
  printf("      iscsi - iSCSI接口\n");
  printf("      nas   - NAS接口\n");
  exit(0);
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

    // 检查是否远程调用
    if ( !strncmp(argv[1], "-h", 2))
      remote_exec(argc-2, (argv+2));

    // 本地调用
    cmd_name = argv[1];
    cmd_argc = argc - 1;
    cmd_argv = argv + 1;
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
    {
      p->cmd(cmd_argc, cmd_argv);
      break;
    }
    p++;
  }

  return 0;
}
