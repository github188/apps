1.jw-linux系统或安装了jw-storage软件的linux系统，用户程序链接了开发库可以直接运行。
2.其他linux需要按以下步骤先启动后台程序led-ctl-daemon
	a.加载驱动i2c_dev，i2c_i801
		如果i2c_i801和ACPI存在地址冲突，需要向内核传递参数"acpi_enforce_resources=lax"来降低
		ACPI对IO Map资源检查的等级
	b.从i2c_i801驱动的sys接口找到i2c节点
		sys_dir=`ls -d /sys/module/i2c_i801/drivers/pci\:i801_smbus/0000\:00\:*/i2c-*`
		i2c_node=`basename $sys_dir`
	c.在/dev下建一个软链接i2c-i801
		cd /dev
		ls -sfn $i2c_node i2c-i801
	d.启动后台程序led-ctl-daemon -t <hardware-type>
		hardware-type:
			3U16-STANDARD
			3U16-SIMPLE
			2U8-STANDARD
			2U8-ATOM
