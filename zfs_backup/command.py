import logging
import subprocess


class Command(object):
  known_commands = []

  @classmethod
  def name(cls):
    return cls.__name__.lower()

  @classmethod
  def main(cls, args):
    o = cls(args)
    o.run()

  @classmethod
  def add_arguments(cls, parser):
    pass

  def __init__(self, args):
    self.args = args
    self.context = args.context
    self.logger = logging.getLogger(self.__class__.name())

  def _execute(self, cmd, capture=False, raises=True, encoding="utf-8", log=True):
    if log:
      self.logger.info("+ {}".format(cmd))

    stdout = subprocess.PIPE if capture else None
    status = subprocess.run(cmd, stdout=stdout, check=raises, shell=True)

    if capture:
      status.stdout = status.stdout.decode(encoding)

    return status
