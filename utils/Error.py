from discord.ext import commands


class FeatureDisabled(commands.CheckFailure):
    pass


class PrefixNotInitialised(commands.CommandError):
    pass


class PrefixAlreadyPresent(commands.CommandError):
    pass


class PrefixNotPresent(commands.CommandError):
    pass
