from configparser import ConfigParser
import os
import logging

from .command import Command


class Context(object):
  def __init__(self, config_path):
    self.logger = logging.getLogger("config")
    self.logger.debug("reading config file at {}".format(config_path))

    c = ConfigParser(allow_no_value=True)
    c["main"] = {
      "intermediate_checksum": False,
      "split_size": "1G",
      "remote": "",
      "rclone_conf": os.environ.get("RCLONE_CONFIG", os.path.join(os.path.expanduser("~"), ".rclone.conf")),
      "rclone_bwlimit": "",
      "rclone_args": "",
      "oldest_snapshot_days": 120,
      "on_failure": "",
      "remote_prune_disabled": True,
    }

    c["backup-sequences"] = {
      "step1": "lock",
      "step2": "snapshot",
      "step3": "export-intermediate",
      "step4": "prune-intermediate -y",
      "step5": "prune-snapshots -y",
      "step6": "unlock",
    }

    c["lifecycle-remote"] = {}

    c.read(config_path)

    for k in ["encryption_passphrase", "zfs_fs", "intermediate_basedir"]:
      if k not in c["main"]:
        raise KeyError("{} must be specified in [main]".format(k))

    if not os.path.isdir(c["main"]["intermediate_basedir"]):
      raise ValueError("{} is not a valid directory".format(c["main"]["intermediate_basedir"]))

    if not c["main"]["remote"]:
      self.logger.warn("no remote defined, uploading will not work")

    for k in ["lifecycle-intermediate"]:
      if k not in c:
        raise KeyError("[{}] must be defined in config file")

    self.main = c["main"]
    self.lifecycle_intermediate = c["lifecycle-intermediate"]
    self.lifecycle_remote = c["lifecycle-remote"]

    self.backup_sequences = []
    for k in sorted(list(c["backup-sequences"].keys())):
      self.backup_sequences.append(c["backup-sequences"][k])

    for k in self.main:
      setattr(self, k, self.main[k])

    self.oldest_snapshot_days = c["main"].getint("oldest_snapshot_days")
    self.intermediate_checksum = c["main"].getboolean("intermediate_checksum")
    self.remote_prune_disabled = c["main"].getboolean("remote_prune_disabled")

    self.c = c

    # Other variables
    self.lock_path = os.path.join(self.intermediate_basedir, "_lock")

  def try_lock(self):
    try:
      open(self.lock_path, "x")
    except FileExistsError:
      return False
    else:
      return True

  def unlock(self):
    try:
      os.remove(self.lock_path)
    except FileNotFoundError:
      pass

  def show(self, logger=None, mask_passphrase=True):
    if logger is None:
      logger = self.logger

    other_info = {
      "lock_path": self.lock_path,
      "locked": os.path.exists(self.lock_path),
    }

    logger.info("Configuration")
    logger.info("=============")

    maxl = len(max(
      list(self.main.keys()) + list(self.lifecycle_intermediate.keys()) + list(self.lifecycle_remote.keys()) + list(other_info.keys()),
      key=lambda v: len(v)
    ))

    self._log_section(logger, "main", self.main, maxl)
    self.logger.info("")
    self._log_section(logger, "backup-sequences", {"step_" + str(i + 1): s for i, s in enumerate(self.backup_sequences)}, maxl)
    self.logger.info("")
    self._log_section(logger, "lifecycle-intermediate", self.lifecycle_intermediate, maxl)
    self.logger.info("")
    self._log_section(logger, "lifecycle-remote", self.lifecycle_remote, maxl)
    self.logger.info("")
    self._log_section(logger, "_internals", other_info, maxl)

  def _log_section(self, logger, section_name, section, maxl):
    logger.info("[{}]".format(section_name))
    for k in section:
      logger.info("{: <{width}} = {}".format(k, section[k], width=maxl))


class ShowContext(Command):
  """Shows the context as seen by zfs-backup."""
  @classmethod
  def name(cls):
    return "show-context"

  def run(self):
    self.context.show()


class Lock(Command):
  """Attempt to create a lock file and thus disallow other calls to perform."""
  def run(self):
    self.logger.debug("creating lock file")

    if not self.args.dry_run:
      if not self.context.try_lock():
        raise RuntimeError("lockfile already exists!")
      else:
        self.logger.debug("lock acquired")


class Unlock(Command):
  """Remove the lock file and thus allow other calls to perform."""
  def run(self):
    self.logger.debug("deleting lock file")

    if not self.args.dry_run:
      self.context.unlock()
      self.logger.debug("lock file removed")
