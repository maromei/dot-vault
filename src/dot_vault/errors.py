"""
General idea behind the error setup:

    Every error that the Tool raises inherits from :class:`DotVaultError`.
    Each :class:`DotVaultError` has a `source` attribute, which can be set to
    certain set of errors.

    Conesquently there are two ways to specify errors:
        - as type union: `type SomeUnion = Error1 | Error2`
        - as class: `class SomeError(DotVaultError[Error1 | Error2]): ...`

    The first way should be used in most cases. The second way when
    specifying a certain action / endpoint. It is hard to define what exactly it is.
    But f.e. one CLI action is to check whether something is installed.
    This specific action has its own error.
"""

from __future__ import annotations
from pathlib import Path


class DotVaultError[SourceExc: Exception = Exception](Exception):
    msg: str | None = None
    _source: SourceExc | None = None

    #: This value is defined in the built-in :class:`Exception` class.
    #: It is set if we do `raise SecondException from FirstException`.
    __cause__: BaseException | None = None

    def __init__(self, msg: str | None = None, source: SourceExc | None = None):
        super().__init__(self, msg)
        self.source = source
        self.msg = msg

    @property
    def source(self) -> SourceExc | None:
        return self._source

    @source.setter
    def source(self, val: SourceExc | None) -> None:
        self._source = val
        self.__cause__ = val


class ScriptRunFailed(DotVaultError):
    pass


class MoreThanOneFileFound(DotVaultError):
    pass


class InvalidReturnFileFormat(DotVaultError):
    pass


class DotVaultDirDoesNotExist(DotVaultError):
    pass


class ModuleDirDoesNotExist(DotVaultError):
    pass


class ScriptDirDoesNotExist(DotVaultError):
    pass


class TargetDoesNotExist(DotVaultError):
    pass


class ScriptFileDoesNotExist[SourceExc: Exception = Exception](
    DotVaultError[SourceExc]
):
    file_path: Path

    def __init__(self, msg: str, file_path: Path, source: SourceExc | None = None):
        super().__init__(msg, source)
        self.file_path = file_path


class ModuleConfigDoesNotExist[T: Exception = Exception](DotVaultError[T]):
    file_path: Path

    def __init__(self, msg: str, file_path: Path, source: T | None = None):
        super().__init__(msg=msg, source=source)
        self.file_path = file_path


############################
### Module Config Errors ###
############################


ModuleDirErrors = DotVaultDirDoesNotExist | ModuleDirDoesNotExist


#########################
### Get Script Errors ###
#########################

type GetScriptErrors = (
    DotVaultDirDoesNotExist
    | ModuleDirDoesNotExist
    | ScriptDirDoesNotExist
    | ScriptFileDoesNotExist
    | MoreThanOneFileFound
)

#######################
### Check Installed ###
#######################


type CheckInstalledFailedErrors = (
    InvalidReturnFileFormat
    | ScriptRunFailed
    | DotVaultDirDoesNotExist
    | ModuleDirDoesNotExist
    | ScriptDirDoesNotExist
    | ScriptFileDoesNotExist
    | MoreThanOneFileFound
)


class CheckInstallFailed(DotVaultError[CheckInstalledFailedErrors]):
    pass


######################
### Install Failed ###
######################


InstallFailedErrors = (
    DotVaultDirDoesNotExist | ModuleDirDoesNotExist | ScriptRunFailed | GetScriptErrors
)


class InstallFailed(DotVaultError[InstallFailedErrors]):
    pass
