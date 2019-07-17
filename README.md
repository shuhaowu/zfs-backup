ZFS Backup
==========

This utility creates snapshot of ZFS filesystems and then uploads them to
somewhere else via rclone. The main command to use is `zfs-backup perform`. The
operation goes through several different phases (each phase can be manually
executed as a command):

0. Check if the backup creation is "locked" via the lock file. Quit if a lock
   file is found.
1. Run the `preperform` script if exists.
2. `zfs-backup lock`: Creates a lockfile at `{intermediate_basedir}/lock`.
3. `zfs-backup snapshot`: Creates the snapshot with ZFS.
    1. Before the snapshot, run the `presnapshot` script. This can be used to
       shutdown services that's possibly using the files.
    2. After the snapshot, run the `postsnapshot` script. This can be used to
       restart the services that needs the files.
    3. Note: the snapshot should be instantaneous due to how ZFS works.
4. `zfs-backup export-intermediate`: Send the ZFS snapshot into encrypted files
    on disk each with a maximum of 2GB.
    1. If there's a previous snapshot exist, it will send an incremental
       snapshot; otherwise, it will export a full snapshot.
    2. It is possible to manually create a full snapshot via the `--full` flag
       if this phase is run manually.
    3. The backup files are stored in `{intermediate_basedir}/{zfs_fs}@YYYYmmddHHMMMSS`.
    4. The files are encrypted first and than split. To reconstruct the backup,
       merge them together in order and then decrypt them.
5. `zfs-backup prune-intermediate`: Removes the encrypted files generated by
   the previous backup.
   1. These are files within `{intermediate_basedir}/{zfs_fs@YYYYmmddHHMMSS}`.
6. `zfs-backup prune-snapshots`: Remove ZFS snapshots that are
   `>oldest_snapshot_days` old.
7. `zfs-backup rclone`: Run rclone to upload the files generated during
   `export-intermediate` using `rclone sync`. 
   1. `RCLONE_CONFIG` environment variable is respected.
   2. Bandwidth limitation can be specified via `rclone_bwlimit`, which is
      passed to `--bwlimit` of rclone.
8. Run the `postperform` script if exists.

Configuration is specified within a directory. It is passed to zfs-backup 
either via the `--confdir` flag (shorthand `-c`) or using the 
`ZFS_BACKUP_CONFDIR` environment variable. The directory has the following 
structures:

```
config_dir/
    config.ini
    presnapshot  # optional, chmod +x
    postsnapshot # optional, chmod +x
    preperform   # optional, chmod +x
    postperform  # optional, chmod +x
```

The `presnapshot`, `postsnapshot`, `preperform`, and `postperform` scripts are optional. If they do not exist, they will not run. `config.ini` is specified as follows:

```
[main]
key                  = abcdefg   # Symmetric encryption key for GPG. Required.
zfs_fs               = data      # The ZFS fs to backup. Required.
intermediate_basedir = /data/2   # A path for the GPG split files. Required.
upload_to            = b2:       # The rclone path to upload to. Required.
split_size           = 1G        # The size of the split files. This arg is 
                                 # passed to `split --bytes`. Defaults to 1G.
oldest_snapshot_days = 120       # The number of days before a snapshot is
                                 # pruned. Defaults to 120. 
rclone_conf          = /p/r.conf # The path to rclone.conf. Defaults to 
                                 # value found in the environment variable
                                 # RCLONE_CONFIG. If that is not available, 
                                 # get it from ~/.rclone.conf of the user 
                                 # running this program.
rclone_bwlimit       = ....      # Argument is passed to `rclone --bwlimit`.
                                 # Default to empty (which means rclone is not
                                 # called with --bwlimit).
```