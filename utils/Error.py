from discord.ext import commands


class FeatureDisabled(commands.CheckFailure):
    pass


class PrefixNotInitialised(commands.CommandError):
    pass


class PrefixAlreadyPresent(commands.CommandError):
    pass


class PrefixNotPresent(commands.CommandError):
    pass


class BlacklistedUser(commands.CheckFailure):
    pass


class BlacklistedGuild(commands.CheckFailure):
    pass


class UserAlreadyBlacklisted(commands.CommandError):
    pass


class GuildAlreadyBlacklisted(commands.CommandError):
    pass
