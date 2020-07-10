ZFS backup with snapshot management
===================================

Inspired by duplicity, but applied with ZFS.

System Requirement
------------------

- Python 3
- ZFS, and the `zfs` command available.
- rclone (optional).

Commands
--------

- `zfs-backup perform`
- `zfs-backup lock`
- `zfs-backup unlock`
- `zfs-backup snapshot`
- `zfs-backup export-intermediate [-f/--full] [-i/--incremental]`
- `zfs-backup upload-intermediate-to-remote`
- `zfs-backup prune-snapshots [-y]`
- `zfs-backup prune-intermediate [-y]`
- `zfs-backup prune-remote [-y]`
- `zfs-backup verify-checksums`
- `zfs-backup show [--include-remote]`

### Global flags

`zfs-backup [-c/--config <file/to/config>] [--dry-run] [-i/--ignore-lock]`

Descriptions
------------

**`zfs-backup perform`**

Performs a full backup sequence as specified by the config file. See [Config
File](#config-file) and [Backup Sequence](#backup-sequence) for details.

**`zfs-backup lock`**

Creates a lockfile in the path specified in the config file. All operations will
check against this lockfile unless `--ignore-lock` is specified.

**`zfs-backup unlock`**

Deletes the lockfile created with the `lock` command.

**`zfs-backup snapshot`**

Creates a snapshot with ZFS with the filesystem specified in the config file. If
the config file specified pre and post snapshot actions, those commands will be
run before and after the actual zfs snapshot

**`zfs-backup export-intermediate [-f/--full] [-i/--incremental]`**

Exports the zfs snapshot into files with encryption with `zfs send`. Files will
be `split` into configured max size specified in the config file. By default,
this command will generate either incremental or full backup files based on the
[backup lifecycle](#backup-lifecycle) specified in the config file. This
behaviour can be overridden with either the `--full` or the `--incremental`
flag.

The intention of this command is so we can later upload these files via rclone.
If you're happy with just the files. Alternatively, if you don't want to
generate intermediate files locally, you can point the intermediate directory to
a network filesystem, or some FUSE thing.

**`zfs-backup upload-intermediate-to-remote`**

Calls rclone with the latest files generated via `export-intermediate` into a
remote location specified in the config file.

**`zfs-backup prune-snapshots [-y]`**

Prune the locally kept ZFS snapshots based on the `oldest_snapshot_days`
specified in the config file.

This command by default implies `--dry-run` and requires `-y` to actually
execute.

**`zfs-backup prune-intermediate [-y]`**

Prune the intermediate files based on the schedule specified in the config file.

This command by default implies `--dry-run` and requires `-y` to actually
execute.

**`zfs-backup prune-remote [-y]`**

Prune the remote files based on the schedule specified in the config file.

This command by default implies `--dry-run` and requires `-y` to actually
execute.

**`zfs-backup verify-checksums`**

Uses the exported intermediate checksum to verify against the remote backups.
This does not actually read the remote data. For example, in b2, we will
checksum against the b2 metadata checksum for each file.

Config File
-----------

Full example:

```
[main]
encryption_passphrase = abcdefg
zfs_fs                = data/photos
intermediate_basedir  = /data/backupintermediate
intermediate_checksum = yes
split_size            = 1G
remote                = b2:bucket/whatever
rclone_conf           = /path/to/rclone.conf
rclone_bwlimit        = ...
rclone_args           = ...
oldest_snapshot_days  = 120
on_failure            = /opt/bin/on-backup-failure

[backup-sequence]
step01 = lock
step02 = snapshot
step03 = export-intermediate
step04 = prune-intermediate -y
step05 = prune-snapshots -y
step06 = upload-intermediate-to-remove
step07 = prune-remote -y
step08 = unlock
step09 = verify-checksums

[lifecycle-intermediate]
# This will result in the last full backup and only the most recent backup
# stored in the intermediate basedir, along with the full backup with age 
# closest to the age of 1 week, 6 months, and 1 year.
keep-last-chain               = 0
keep-last-full-only           = 1
keep-last-incremental-only    = 1
keep-full-with-age-closest-to = 1w,6m,1y

[lifecycle-remote]
# This will result in the last full chain (full + all subsequent incremental
# until the most recent one) and 2 more full backups before that being kept.
keep-last-chains    = 1
keep-last-full-only = 3
```

### Main configurations

### Backup Sequence

### Backup Lifecycle

Intermediate Directory Layout
-----------------------------


