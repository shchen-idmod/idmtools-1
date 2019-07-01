import logging
from typing import Optional, Tuple, List, Dict, Any
from idmtools_local.client.base import BaseClient
from idmtools_local.config import API_PATH


logger = logging.getLogger(__name__)


class ExperimentsClient(BaseClient):
    base_url = f'{API_PATH}/experiments'

    @classmethod
    def get_all(cls, id: Optional[str] = None, tag: Optional[List[Tuple[str, str]]] = None) -> List[Dict[str, Any]]:
        """
        Get all experiments with options to filter by id or tags

        Args:
            id (Optional[str]):  ID of the experiment
            tag (Optional[List[Tuple[str, str]]]): List of tags/values to filter experiment by

        Returns:
            List[Dict[str, Any]]: returns list of experiments
        """
        args = dict(tag=tag if tag is not None and len(tag) > 0 else None)
        args = {k: v for k, v in args.items() if v is not None}
        response = cls.get(id, params=args)
        if response.status_code != 200:
            if logger.isEnabledFor(logging.DEBUG):
                logging.debug(f'Error fetching simulations {cls.base_url if id is None else cls.base_url + "/" + id}'
                              f'Response Status Code: {response.status_code}. Response Content: {response.text}')
            data = response.json()
            raise RuntimeError(data['message'])
        result = response.json()
        return result

    @classmethod
    def get_one(cls, id: str, tag: Optional[List[Tuple[str, str]]] = None) -> Dict[str, Any]:
        """
        Convenience method to get one simulation

        Args:
            id (str):  ID of the experiment
            tag (Optional[List[Tuple[str, str]]]): List of tags/values to filter experiment by

        Returns:
            dict: Dictionary containing the experiment objects
        """
        result = cls.get_all(id, tag)
        if len(result) < 1:
            raise RuntimeError(f"Cannot find experiment with ID {id}")
        return result[0]

    @classmethod
    def delete(cls, id: str, delete_data: bool = False, ignore_doesnt_exist: bool = True) -> bool:
        """
        Delete an experiment. Optinally you can delete the experiment data. WARNING: Deleting the data is irreversible

        Args:
            id (str): ID of the experiments
            delete_data (bool): Delete data directory including simulations
            ignore_doesnt_exist: Ignore error if the specific experiment doesn't exist

        Returns:
            True if deletion is succeeded
        """
        response = super().delete(id, params=dict(data=delete_data))

        if response.status_code != 204 and (response.status_code != 404 and ignore_doesnt_exist):
            return False
        elif response.status_code != 204:
            data = response.json()
            raise RuntimeError(data['message'])
        return True
