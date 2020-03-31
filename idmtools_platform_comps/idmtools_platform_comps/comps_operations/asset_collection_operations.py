from dataclasses import field, dataclass
from typing import Type
from uuid import UUID

from COMPS.Data import AssetCollection as COMPSAssetCollection, QueryCriteria, AssetCollectionFile
from idmtools.assets import AssetCollection, Asset
from idmtools.entities.iplatform_ops.iplatform_asset_collection_operations import IPlatformAssetCollectionOperations


@dataclass
class CompsPlatformAssetCollectionOperations(IPlatformAssetCollectionOperations):
    platform: 'COMPSPlaform'  # noqa F821
    platform_type: Type = field(default=COMPSAssetCollection)

    def get(self, asset_collection_id: UUID, **kwargs) -> COMPSAssetCollection:
        children = kwargs.get('children')
        children = children if children is not None else ["assets", "tags"]
        return COMPSAssetCollection.get(id=asset_collection_id, query_criteria=QueryCriteria().select_children(children))

    def platform_create(self, asset_collection: AssetCollection, **kwargs) -> COMPSAssetCollection:
        ac = COMPSAssetCollection()
        for asset in asset_collection:
            # using checksum is not accurate and not all systems will support de-duplication
            if asset.checksum is None:
                ac.add_asset(AssetCollectionFile(file_name=asset.filename, relative_path=asset.relative_path),
                             data=asset.bytes)
            else:  # We should already have this asset so we should have a md5sum
                ac.add_asset(AssetCollectionFile(file_name=asset.filename, relative_path=asset.relative_path,
                                                 md5_checksum=asset.checksum))

        # Add tags
        if asset_collection.tags:
            ac.set_tags(asset_collection.tags)

        ac.save()
        asset_collection.uid = ac.id
        asset_collection._platform_object = asset_collection
        return ac

    def to_entity(self, asset_collection: COMPSAssetCollection, **kwargs) -> AssetCollection:
        ac = AssetCollection()
        ac.uid = asset_collection.id
        ac.tags = asset_collection.tags
        for asset in asset_collection.assets:
            a = Asset(relative_path=asset.relative_path, filename=asset.file_name, checksum=asset.md5_checksum)
            a.persisted = True
            ac.assets.append(a)

        return ac