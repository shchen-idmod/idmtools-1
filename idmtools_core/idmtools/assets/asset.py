import os
from dataclasses import dataclass, field
from typing import TypeVar, Union, List, Callable, Any


@dataclass(repr=False)
class Asset:
    """
    A class representing an asset. An asset can either be related to a physical
    asset present on the computer or directly specified by a filename and content.
    """

    absolute_path: 'str' = field(default=None)
    relative_path: 'str' = field(default=None)
    filename: 'str' = field(default=None)
    content: 'Any' = field(default=None)
    persisted: 'bool' = field(default=False)
    handler: 'Callable' = field(default=None)

    def __post_init__(self):
        if not self.absolute_path and not (self.filename and self.content):
            raise ValueError("Impossible to create the asset without either absolute path or filename and content!")

        self.filename = self.filename or os.path.basename(self.absolute_path)

    def __repr__(self):
        return f"<Asset: {os.path.join(self.relative_path, self.filename)} from {self.absolute_path}>"

    @property
    def extension(self):
        return os.path.splitext(self.filename)[1].lstrip('.').lower()

    @property
    def relative_path(self):
        return self._relative_path or ""

    @relative_path.setter
    def relative_path(self, relative_path):
        self._relative_path = relative_path.strip(" \\/") if not isinstance(relative_path,
                                                                            property) and relative_path else None

    @property
    def bytes(self):
        if isinstance(self.content, bytes):
            return self.content
        return str.encode(self.handler(self.content))

    @property
    def content(self):
        """
        Returns:
            The content of the file, either from the content attribute or by opening the absolute path.
        """
        if not self._content and self.absolute_path:
            with open(self.absolute_path, "rb") as fp:
                self._content = fp.read()

        return self._content

    @content.setter
    def content(self, content):
        self._content = None if isinstance(content, property) else content

    # region Equality and Hashing
    def __eq__(self, other):
        return self.__key() == other.__key()

    def __key(self):
        if self.absolute_path:
            return self.absolute_path

        if self.filename and self.relative_path:
            return self.filename, self.relative_path

        return self._content, self.filename

    def __hash__(self):
        return hash(self.__key())
    # endregion


TAsset = TypeVar("TAsset", bound=Asset)
# Assets types
TAssetList = List[TAsset]

# Filters types
TAssetFilter = Union[Callable[[TAsset], bool], Callable]
TAssetFilterList = List[TAssetFilter]
