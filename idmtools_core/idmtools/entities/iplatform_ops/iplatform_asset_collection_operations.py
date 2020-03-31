from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Type, NoReturn
from uuid import UUID

from idmtools.assets import AssetCollection
from idmtools.core import CacheEnabled
from idmtools.entities.iplatform_ops.utils import batch_create_items


@dataclass
class IPlatformAssetCollectionOperations(CacheEnabled, ABC):
    platform: 'IPlatform'
    platform_type: Type

    def pre_create(self, asset_collection: AssetCollection, **kwargs) -> NoReturn:
        """
        Run the platform/AssetCollection post creation events

        Args:
            asset_collection: AssetCollection to run post-creation events
            **kwargs: Optional arguments mainly for extensibility

        Returns:
            NoReturn
        """
        asset_collection.pre_creation()

    def post_create(self, asset_collection: AssetCollection, **kwargs) -> NoReturn:
        """
        Run the platform/AssetCollection post creation events

        Args:
            asset_collection: AssetCollection to run post-creation events
            **kwargs: Optional arguments mainly for extensibility

        Returns:
            NoReturn
        """
        asset_collection.post_creation()

    def create(self, asset_collection: AssetCollection, do_pre: bool = True, do_post: bool = True, **kwargs) -> Any:
        """
        Creates an AssetCollection from an IDMTools AssetCollection object. Also performs pre-creation and post-creation
        locally and on platform

        Args:
            asset_collection: AssetCollection to create
            do_pre: Perform Pre creation events for item
            do_post: Perform Post creation events for item
            **kwargs: Optional arguments mainly for extensibility

        Returns:
            Created platform item and the UUID of said item
        """
        if asset_collection.status is not None:
            return asset_collection._platform_object
        if do_pre:
            self.pre_create(asset_collection, **kwargs)
        ret = self.platform_create(asset_collection, **kwargs)
        if do_post:
            self.post_create(asset_collection, **kwargs)
        return ret

    @abstractmethod
    def platform_create(self, asset_collection: AssetCollection, **kwargs) -> Any:
        """
        Creates an workflow_item from an IDMTools AssetCollection object

        Args:
            asset_collection: AssetCollection to create
            **kwargs: Optional arguments mainly for extensibility

        Returns:
            Created platform item and the UUID of said item
        """
        pass

    def batch_create(self, asset_collections: List[AssetCollection], display_progress: bool = True, **kwargs) -> \
            List[AssetCollection]:
        """
        Provides a method to batch create asset collections items

        Args:
            asset_collections: List of asset collection items to create
            display_progress: Show progress bar
            **kwargs:

        Returns:
            List of tuples containing the create object and id of item that was created
        """
        return batch_create_items(asset_collections, create_func=self.create, display_progress=display_progress,
                                  progress_description="Uploading Assets", **kwargs)

    @abstractmethod
    def get(self, asset_collection_id: UUID, **kwargs) -> Any:
        """
        Returns the platform representation of an AssetCollection

        Args:
            asset_collection_id: Item id of AssetCollection
            **kwargs:

        Returns:
            Platform Representation of an AssetCollection
        """
        pass

    def to_entity(self, asset_collection: Any, **kwargs) -> AssetCollection:
        """
        Converts the platform representation of AssetCollection to idmtools representation

        Args:
            asset_collection: Platform AssetCollection object

        Returns:
            IDMTools suite object
        """
        return asset_collection