# EON Backup

## How to do it manually

First enable Tethering from EON settings and connect to EON from your backup device (like a laptop) over wifi. Eon will have IP: 192.168.43.1 . 

EON has ssh service enabled and allows to connect with a private key that can be copied from https://community.comma.ai/wiki/index.php/Configuring_OpenPilot

And then you may copy any file from EON like this:
```
scp -i eon.pem root@192.168.43.1:/data/media/0/realdata/<remaining file path> ./
```

You may first connect to EON and get a list of available files in the realdata directory. Or just use the realdata with -r:
```
scp -i eon.pem -r root@192.168.43.1:/data/media/0/realdata/ ./
```


## How to automate it

The above will work- but we can do better. Take a small foot print computer with wifi (like raspberri pi) and a USB storage (those large backup disks are great) and run an ansible script to copy file from EON every 5 minutes or so. If there are lot of files available copy one file at a time - so it does not take a lot of resource. EON uses Snapdragon Neural Processing Engine - so probably wont have any problem having some IO on it. Tests on thousand mile trip shows no issue - but is not widely tested yet.

The script should calculate sha256sum on eon and send it back and the once a file is copied it is verified on the backup system and then it can issue a delete command (optionally).

Comma.ai uses the drive data to improve the openpilot, so it's important that the file is being uploaded to comma server. There are two ways to do it- either copy it back to EON if it was deleted to free disk space, or duplicate the upload logic on the backup system so it can upload when the car arrives home and it can connect to home network.

Enable Tethering works for manula copying- but to make it completely automated, the backup system should work as access point when it can not connect users home network. So, EON will automatically connect to backup system when car leaves home. The backup system will disable the access point when the home network is reachable, so EON will automatically connect to home network instead of backup system.

## Preparing raspbian disk image

Run the ansible playbook on your developer machine:

```
ansible-playbook prepare.yaml --ask-sudo-pass
```

This will download the raspbian image and add wifi access point configuration.

Now you may prepare an SD card with following command (replace sdX with your device name):

```
dd bs=4M if=2019-09-26-raspbian-buster-lite.img of=/dev/sdX conv=fsync
```

If you insert the SD card into a raspberri pi 3 model B, it should boot, connect to it, install ```dnsmasq``` + ```hostapd``` and be ready as an access point after a restart.

You may connect your EON to this access point.

If you want the eonbackup system to connect to your home network as well you may change the rootfs/etc/network/interfaces.d/wlan0 file. You will need ssid and password which you may create using:

```
$wpa_passphrase myssid topsecretpass

network={
        ssid="myssid"
        #psk="topsecretpass"
        psk=2ee6f26cc554cc88e8f7751385989425dfcd2c979b4d82f0104e80a58a41f584
}
```
Take your ssid and psk value and replace those in wlan0 file.

### If you need to change to different version of raspbian

Download the OS image and find out the boot and rootfs partition properties. 
You will need the ```Start``` offset for boot and rootfs partitions.

```
$parted 2019-09-26-raspbian-buster-lite.img 
GNU Parted 3.2
Using 2019-09-26-raspbian-buster-lite.img
Welcome to GNU Parted! Type 'help' to view a list of commands.
(parted) u                                                                
Unit?  [compact]? B                                                       
(parted) print                                                            
Model:  (file)
Disk 2019-09-26-raspbian-buster-lite.img: 2248146944B
Sector size (logical/physical): 512B/512B
Partition Table: msdos
Disk Flags: 

Number  Start       End          Size         Type     File system  Flags
 1      4194304B    272629759B   268435456B   primary  fat32        lba
 2      272629760B  2248146943B  1975517184B  primary  ext4
```

## The backup service application

Its a C++ service / deamon application that copies files over ssh once EON connects to the access point.

Work in progress. Its the main application and its not there yet :D.

Stay tuned.  

