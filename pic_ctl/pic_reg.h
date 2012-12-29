#ifndef PIC_REG_H
#define PIC_REG_H

enum {
	PIC_HZ		= 16,
};

enum {
	PIC_ADDRESS	= 0x30,

	PIC_VERH	= 0x00,
	PIC_VERL	= 0x01,

	PIC_WDT		= 0x05,
	PIC_LED_START	= 0x10,
};

#endif
