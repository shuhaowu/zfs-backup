from setuptools import setup, find_packages

setup(
  name="zfs-backup",
  description="Backup ZFS",
  packages=find_packages(),
  entry_points={
    "console_scripts": [
      "zfs-backup=zfs_backup:Main.main",
    ],
  }
)
