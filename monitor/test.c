#include <stdio.h>
#include <string.h>
#include <getopt.h>

struct option test_opt[] = {
	{"module",	required_argument,	NULL,	'm'},
	{"event",	required_argument,	NULL,	'e'},
	{"param",	required_argument,	NULL,	'p'},
	{"msg",		required_argument,	NULL,	's'},
	{0, 0, 0, 0}
};

void test_usage()
{
	puts("");
	puts("test <OPTIONS>");
	puts("  --module,-m  <module_name>");
	puts("  --event,-e   <event>");
	puts("  --param,-p   <param>");
	puts("  --msg,-s     <message>");
	puts("");
	exit(1);
}

int main(int argc, char *argv[])
{
	char module[128] = {0},
	     event[128] = {0},
	     param[128] = {0},
	     msg[128] = {0};
	char c;

	opterr = 0;
	while( (c=getopt_long(argc, argv, "m:e:p:s:", test_opt, NULL)) != -1)
	{
		switch (c)
		{
		case 'm':
			strcpy(module, optarg);
			continue;
		case 'e':
			strcpy(event, optarg);
			continue;
		case 'p':
			strcpy(param, optarg);
			continue;
		case 's':
			strcpy(msg, optarg);
			continue;
		case '?':
		default:
			test_usage();
			break;
		}
	}

	if (module[0] == '\0')
	{
		fprintf(stderr, "module not set!\n");
		goto error;
	}

	if (event[0] == '\0')
	{
		fprintf(stderr, "event not set!\n");
		goto error;
	}

	if (param[0] == '\0')
	{
		fprintf(stderr, "param not set!\n");
		goto error;
	}

	if (msg[0] == '\0')
	{
		fprintf(stderr, "msg not set!\n");
		goto error;
	}
	
	sysmon_event(module, event, param, msg);
	return 0;

error:
	test_usage();

	return 0;
}
