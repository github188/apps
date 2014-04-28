#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>
#include "../pic_ctl/pic_ctl.h"

struct pic_ver
{
	uint32_t minor:8;
	uint32_t major:8;
	uint32_t rev:16;
};

struct option longopts[] = {
	{"details",		0, NULL, 'd'},
	{0,0,0,0}
};

static int details_flag = 0;

void usage()
{
	fprintf(stderr, "pic-version [ --details | -d ]\n"
		"pic-version --help\n");
	exit(-1);
}

int parser(int argc, char *argv[])
{
	int c, freq = 0;
	while((c=getopt_long(argc, argv, "d", longopts, NULL))!=-1) {
		switch (c) {
		case 'd':
			details_flag = 1;
			break;
		case 'h':
		case -1:
		case '?':
			return -1;
		}
	}
	
	return 0;
}


int main( int argc, char *argv[] )
{
	uint32_t version;
	uint32_t pic_fm_build_date;
	uint32_t pic_fm_git_id;
	int ret;
	uint8_t ver_str[128];


	if ( parser ( argc, argv ) < 0 ) {
		usage();
	}

	ret = pic_get_version ( &version );
	if ( ret < 0 ) {
		printf ( "pic" );
		return -1;
	}

	if ( details_flag != 1 ) {
		sprintf ( ver_str, "%d.%d", (( struct pic_ver *)(&version))->major, 
								(( struct pic_ver *)(&version))->minor );
		goto show;
	}

	ret = pic_get_build_date ( &pic_fm_build_date );
	if ( ret < 0 ) {
		return -1;
	} 

	ret = pic_get_scm_id ( &pic_fm_git_id );
	if ( ret < 0 ) {
		return -1;
	}

	
	sprintf  ( ver_str, "V%d.%d_%04d%02d%02d_%02x%02x%02x\n", 
					(( struct pic_ver *)(&version))->major,
					(( struct pic_ver *)(&version))->minor,
					((( pic_fm_build_date & 0xff000000 ) >> 24 ) * 100 ) + (( pic_fm_build_date & 0x00ff0000 ) >> 16 ),
					( pic_fm_build_date & 0x0000ff00 ) >> 8,
					( pic_fm_build_date & 0x000000ff ),
					(( pic_fm_git_id & 0x00ff0000 ) >> 16 ),
					(( pic_fm_git_id & 0x0000ff00 ) >> 8 ),
					(( pic_fm_git_id & 0x000000ff )));
	
show:
	printf ( "%s", ver_str );
	return 0;

}
