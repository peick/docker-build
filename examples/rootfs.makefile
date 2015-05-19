all:
	mkdir -p rootfs.chroot/data
	echo "Test123" > rootfs.chroot/data/test
	pwd
	tar -C rootfs.chroot -cf rootfs.tar .

clean:
	rm -rf rootfs.chroot

dist-clean: clean
	rm -f rootfs.tar
