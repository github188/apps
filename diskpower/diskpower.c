#include <stdint.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>

#include "diskpower.h"

#define I2C_DEV		"/dev/i2c-i801"

static int i2c_is_initialized;
static int i2c_fd;

int do_read_diskpw(uint8_t reg1, uint8_t reg2)
{
	int count = 10;
	int ret;
	while(count--) {
		ret = i2c_smbus_read_byte_data(i2c_fd ,reg1);
		if (ret >= 0)
			return ret;
	}
	return PERR_IOERR;

}

int i2c_read_diskpw(void)
{
	uint8_t reg1, reg2;
	int mode1= 0,mode2 = 0, mode3 = 0, mode4 =0;

	if (ioctl(i2c_fd, I2C_SLAVE_FORCE, I2C_ADDRESS_DISKPW1) < 0) {
		return PERR_NODEV;
	}
	reg1 = I2C_GP1_MODE1;
	reg2 = I2C_GP1_MODE2;
	if ((mode1 = do_read_diskpw(reg1, reg2)) < 0) {
		return PERR_IOERR;
	}
	reg1 = I2C_GP2_MODE1;
	reg2 = I2C_GP2_MODE2;
	if ((mode2 = do_read_diskpw(reg1, reg2)) < 0) {
		return PERR_IOERR;
	}


	if (ioctl(i2c_fd, I2C_SLAVE_FORCE, I2C_ADDRESS_DISKPW2) < 0) {
		return PERR_NODEV;
	}
	reg1 = I2C_GP1_MODE1;
	reg2 = I2C_GP1_MODE2;
	if ((mode3 = do_read_diskpw(reg1, reg2)) < 0) {
		return PERR_IOERR;
	}
	reg1 = I2C_GP2_MODE1;
	reg2 = I2C_GP2_MODE2;
	if ((mode4 = do_read_diskpw(reg1, reg2)) < 0) {
		return PERR_IOERR;
	}
	return ((mode1 & 0xf) |((mode2 & 0xf) << 4)  |
		((mode3 & 0xf) << 8) | ((mode4 & 0xf) << 12));

}

int do_write_diskpw(int mode, uint8_t reg1, uint8_t reg2)
{
	int count = 10;
	int value;
	int ret;

	while(count--) {
		value = i2c_smbus_read_byte_data(i2c_fd, reg2);
		if (value == -1)
			continue;
		value &= 0xf0;
		ret = i2c_smbus_write_byte_data(i2c_fd, reg2, value);
		if (ret == -1)
			continue;

		ret = i2c_smbus_write_byte_data(i2c_fd ,reg1, mode);
		if (ret == 0)
			return PERR_SUCCESS;
	}
	return PERR_IOERR;

}

int i2c_write_diskpw(int mode)
{

	uint8_t reg1, reg2;
	int  mode1, mode2, mode3, mode4;


	mode1 = mode & 0xf;
	mode2 = (mode >> 4) & 0xf;
	mode3 = (mode >> 8) & 0xf;
	mode4 = (mode >> 12) & 0xf;

	if (ioctl(i2c_fd, I2C_SLAVE_FORCE, I2C_ADDRESS_DISKPW1) < 0) {
		return PERR_NODEV;
	}
	reg1 = I2C_GP1_MODE1;
	reg2 = I2C_GP1_MODE2;
	if (do_write_diskpw(mode1, reg1, reg2) < 0) {
		return PERR_IOERR;
	}
	reg1 = I2C_GP2_MODE1;
	reg2 = I2C_GP2_MODE2;
	if (do_write_diskpw(mode2, reg1, reg2) < 0) {
		return PERR_IOERR;
	}


	if (ioctl(i2c_fd, I2C_SLAVE_FORCE, I2C_ADDRESS_DISKPW2) < 0) {
		return PERR_NODEV;
	}
	reg1 = I2C_GP1_MODE1;
	reg2 = I2C_GP1_MODE2;
	if (do_write_diskpw(mode3, reg1, reg2) < 0) {
		return PERR_IOERR;
	}
	reg1 = I2C_GP2_MODE1;
	reg2 = I2C_GP2_MODE2;
	if (do_write_diskpw(mode4, reg1, reg2) < 0) {
		return PERR_IOERR;
	}

	return PERR_SUCCESS;
}

int i2c_diskpw_set(int disk_id, int mode)
{
	int old = 0, new_stat = 0;
	if (disk_id < 0 || disk_id > 16)
		return PERR_NODEV;
	if (mode != I2C_DISKPW_ON && mode != I2C_DISKPW_OFF)
		return PERR_NODEV;
	old = i2c_read_diskpw();
	if (old < 0) {
		return PERR_IOERR;
	}

	if (mode == I2C_DISKPW_ON)
		new_stat = old | (1 << (disk_id -1));
	else
		new_stat = old & ~(1 << (disk_id -1));

	if (i2c_write_diskpw(new_stat) < 0)
		return PERR_IOERR;

	return PERR_SUCCESS;
}

int do_init_diskpw(int fd)
{

	int  ret;
	//uint8_t g_config_reg_value;
	int value;

	/* g_config_reg_value = i2c_smbus_read_byte_data(fd, I2C_CONF_DISK); */
	/* if (g_config_reg_value == 255) { */
	/*	return PERR_IOERR; */
	/* } */
	/* g_config_reg_value |= 0x80; */
	/* ret = i2c_smbus_write_byte_data(fd, I2C_CONF_DISK, g_config_reg_value); */
	/* if (ret == -1) */
	/*	return PERR_IOERR; */

	/*
	value = i2c_smbus_read_byte_data(fd, I2C_GP1_MODE1);
	value |= 0x0f;
	ret = i2c_smbus_write_byte_data(fd, I2C_GP1_MODE1, value);
	if (ret == -1)
		return PERR_IOERR;
	*/
	value = i2c_smbus_read_byte_data(fd, I2C_GP1_MODE2);
	if (value == -1)
		return PERR_IOERR;
	value &= 0xf0;
	ret = i2c_smbus_write_byte_data(fd, I2C_GP1_MODE2, value);
	if (ret == -1)
		return PERR_IOERR;

	/*
	value = i2c_smbus_read_byte_data(fd, I2C_GP2_MODE1);
	value |= 0x0f;
	ret = i2c_smbus_write_byte_data(fd, I2C_GP2_MODE1, value);
	if (ret == -1)
		return PERR_IOERR;
	*/
	value = i2c_smbus_read_byte_data(fd, I2C_GP2_MODE2);
	if (value == -1)
		return PERR_IOERR;
	value &= 0xf0;
	ret = i2c_smbus_write_byte_data(fd, I2C_GP2_MODE2, value);
	if (ret == -1)
		return PERR_IOERR;

	return 0;
}

int i2c_init_diskpw(void)
{
	int fd;

	if (i2c_is_initialized)
		return 0;
	fd = open(I2C_DEV, O_RDWR);
	if (fd < 0)
		return PERR_NODEV;

	if (ioctl(fd, I2C_SLAVE_FORCE, I2C_ADDRESS_DISKPW1) < 0) {
		close(fd);
		return PERR_NODEV;
	}

	if (do_init_diskpw(fd) < 0) {
		close(fd);
		return PERR_IOERR;
	}

	if (ioctl(fd, I2C_SLAVE_FORCE, I2C_ADDRESS_DISKPW2) < 0) {
		close(fd);
		return PERR_IOERR;
	}

	if (do_init_diskpw(fd) < 0) {
		close(fd);
		return PERR_IOERR;
	}

	i2c_is_initialized = 1;
	i2c_fd = fd;
	return 0;

}

void i2c_release_disk(void)
{
	i2c_fd = 0;
	i2c_is_initialized = 0;

}
