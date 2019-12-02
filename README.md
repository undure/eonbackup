# EON Backup

## How to do it manually

First enable Tethering from EON settings and connect to EON from your backup device (like a laptop) over wifi. Eon will have IP: 192.168.43.1 . 

EON has ssh service enabled and allows to connect with a private key that can be copied from https://community.comma.ai/wiki/index.php/Configuring_OpenPilot

And then you may copy any file from EON like this:
```
scp -i comma.pem root@192.168.43.1:/data/media/0/realdata/<remaining file path> ./
```

You may first connect to EON and get a list of available files in the realdata directory. Or just use the realdata with -r:
```
scp -i comma.pem -r root@192.168.43.1:/data/media/0/realdata/ ./
```


## How to automate it

The above will work- but we can do better. Take a small foot print computer with wifi (like raspberri pi) and a USB storage (those large backup disks are great) and run an ansible script to copy file from EON every 5 minutes or so. If there are lot of files available copy one file at a time - so it does not take a lot of resource. EON uses Snapdragon Neural Processing Engine - so probably wont have any problem having some IO on it. Tests on thousand mile trip shows no issue - but is not widely tested yet.

  
