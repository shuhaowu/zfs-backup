import argparse
import logging
import os
import os.path
import sys

from .command import Command
from .perform import Perform
from .snapshot import Snapshot, PruneSnapshot
from .context import Context, ShowContext, Lock, Unlock

# Since this is registered at the beginning, all code will have access to this array.
Command.known_commands = [
  Perform,
  ShowContext,
  Lock,
  Unlock,
  Snapshot,
  PruneSnapshot,
]


class Main(object):
  @classmethod
  def main(cls):
    global_parser = argparse.ArgumentParser(description="ZFS backup with snapshot management")
    global_parser.add_argument(
      "-c", "--config", default=os.environ.get("ZFS_BACKUP_CONFIG", None),
      help="the config ini file path (could also be specified by ZFS_BACKUP_CONFIG env var)"
    )

    global_parser.add_argument(
      "--dry-run", action="store_true", default=False,
      help="only print out what needs to be done instead of actually doing things"
    )

    global_parser.add_argument(
      "-v", "--verbose", action="store_true", default=False,
      help="print verbosely"
    )

    subparsers = global_parser.add_subparsers()

    for command in Command.known_commands:
      parser = subparsers.add_parser(command.name(), help=command.__doc__)
      command.add_arguments(parser)
      parser.set_defaults(f=command.main)

    global_parser.set_defaults(f=Perform.main)

    args = global_parser.parse_args()
    if args.config is None:
      print("error: must specify --config or ZFS_BACKUP_CONFIG", file=sys.stderr)
      sys.exit(1)

    if not os.path.isfile(args.config):
      print("error: {} is not a valid file".format(args.config), file=sys.stderr)
      sys.exit(1)

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(format="[%(name)-10s][%(levelname).1s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=level)

    args.context = Context(args.config)

    args.f(args)
