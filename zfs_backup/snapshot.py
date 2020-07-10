from datetime import datetime

from .command import Command


class Snapshot(Command):
  """Calls ZFS and creates a snapshot."""
  def run(self):
    snapshot_id = datetime.now().strftime("%Y%m%d%H%M%S")
    zfs_name = "{}@{}".format(self.args.zfs_fs, snapshot_id)


class PruneSnapshot(Command):
  """Removes ZFS snapshots from based on oldest_snapshot_days."""
  @classmethod
  def name(cls):
    return "prune-snapshot"
