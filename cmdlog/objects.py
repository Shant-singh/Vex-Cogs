import datetime
from dataclasses import dataclass
from sys import getsizeof
from typing import Optional, Union

import discord
from discord.channel import DMChannel, TextChannel
from discord.guild import Guild

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass(repr=False)  # repr=False will prevent data held here going to sentry if an error occurs
class IDFKWhatToNameThis:
    id: int
    name: str

    def __sizeof__(self) -> int:
        # using getsizeof includes things like garbage
        return getsizeof(self.id) + getsizeof(self.name)


# TODO: remove the mixin... now application commands exist it's too convoluted


class LogMixin:
    """Base for logged data"""

    def __init__(
        self,
        author: Optional[discord.User],
        com_name: str,
        msg_id: Optional[int] = None,
        channel: Optional[Union[DMChannel, TextChannel]] = None,
        guild: Optional[Guild] = None,
        log_content: Optional[bool] = None,
        content: Optional[str] = None,
        application_command: Optional[int] = None,
        target: Optional[Union[discord.User, discord.PartialMessage]] = None,
    ):
        if author is None:
            return

        # ALL COMMANDS
        self.command = com_name
        self.user = IDFKWhatToNameThis(id=author.id, name=f"{author.name}#{author.discriminator}")

        # TEXT COMMANDS
        if msg_id:
            self.msg_id = msg_id
        self.channel: Optional[IDFKWhatToNameThis] = None
        self.guild: Optional[IDFKWhatToNameThis] = None
        if guild and channel:
            assert not isinstance(channel, DMChannel)
            self.channel = IDFKWhatToNameThis(id=channel.id, name=f"#{channel.name}")
            self.guild = IDFKWhatToNameThis(id=guild.id, name=guild.name)
        self.content: Optional[str] = None
        if log_content and content is not None:
            self.content = content

        # USER/MESSAGE COMMANDS
        self.app_type = application_command
        self.target: Optional[IDFKWhatToNameThis] = None

        if isinstance(target, discord.User):
            t_name = target.name if isinstance(target, discord.User) else ""
            self.target = IDFKWhatToNameThis(id=target.id, name=t_name)

        self.time = datetime.datetime.now().strftime(TIME_FORMAT)

    def __str__(self) -> str:
        raise NotImplementedError()

    def __sizeof__(self) -> int:
        # using getsizeof here will include other stuff eg garbage
        size = 0

        size += getsizeof(self.command)
        size += getsizeof(self.user)
        size += getsizeof(self.msg_id)
        size += getsizeof(self.channel)
        size += getsizeof(self.guild)
        size += getsizeof(self.time)
        size += getsizeof(self.target)

        return size


class LoggedCommand(LogMixin):
    """Inherits from LogMixin, for a logged command"""

    def __repr__(self) -> str:  # if enabled, this is what is sent to sentry when an error occurs
        # (if this obj has been generated at that point)
        return "<LoggedCommand with data removed>"

    def __str__(self) -> str:  # this is what is logged locally
        com = self.content or self.command
        if not self.guild or not self.channel:
            return f"Text command '{com}' ran by {self.user.id} ({self.user.name}) in our DMs."

        assert self.msg_id is not None
        return (
            f"Text command '{com}' ran by {self.user.id} ({self.user.name}) "
            f"with message ID {self.msg_id} "
            f"in channel {self.channel.id} ({self.channel.name}) "
            f"in guild {self.guild.id} ({self.guild.name})"
        )


class LoggedComError(LogMixin):
    """Inherits from LogMixin, for a logged error"""

    def __repr__(self) -> str:  # if enabled, this is what is sent to sentry when an error occurs
        # (if this obj has been generated at that point)
        return "<LoggedComError with data removed>"

    def __str__(self) -> str:  # this is what is logged locally
        com = self.content or self.command
        if not self.guild or not self.channel:
            return (
                f"Text command '{com}' raised an error by {self.user.id} ({self.user.name})"
                " in our DMs."
            )

        assert self.msg_id is not None
        return (
            f"Text command '{com}' raised an error by {self.user.id} ({self.user.name}) "
            f"with message ID {self.msg_id} "
            f"in channel {self.channel.id} ({self.channel.name}) "
            f"in guild {self.guild.id} ({self.guild.name})"
        )


class LoggedAppCom(LogMixin):
    """Inherits from LogMixin, for a logged Application Command."""

    def __repr__(self) -> str:  # if enabled, this is what is sent to sentry when an error occurs
        # (if this obj has been generated at that point)
        return f"<LoggedAppCom with data removed app_type={self.app_type}>"

    def __str__(self) -> str:  # this is what's logged locally
        assert self.app_type is not None

        if self.app_type == 1:  # slash com
            if not self.guild or not self.channel:
                return (
                    f"Slash command '{self.command}' ran by {self.user.id} ({self.user.name}) in "
                    "our DMs."
                )
            return (
                f"Slash command '{self.command}' ran by {self.user.id} ({self.user.name}) "
                f"in channel {self.channel.id} ({self.channel.name}) "
                f"in guild {self.guild.id} ({self.guild.name})"
            )

        assert self.target is not None

        if self.app_type == 2:  # user command
            if not self.guild or not self.channel:
                return (
                    f"User command '{self.command}' ran by {self.user.id} ({self.user.name}) "
                    f"targeting user {self.target.name} ({self.target.id})"
                    "in our DMs."
                )

            return (
                f"User command '{self.command}' ran by {self.user.id} ({self.user.name}) "
                f"targeting user {self.target.name} ({self.target.id})"
                f"in channel {self.channel.id} ({self.channel.name}) "
                f"in guild {self.guild.id} ({self.guild.name})"
            )

        if self.app_type == 3:  # message command
            if not self.guild or not self.channel:
                return (
                    f"Message command '{self.command}' ran by {self.user.id} ({self.user.name}) "
                    f"targeting message {self.target.id}"
                    "in our DMs."
                )

            return (
                f"Message command '{self.command}' ran by {self.user.id} ({self.user.name}) "
                f"targeting message {self.target.id}"
                f"in channel {self.channel.id} ({self.channel.name}) "
                f"in guild {self.guild.id} ({self.guild.name})"
            )

        return ""
