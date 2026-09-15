"""AzureRepository provides CRUD operations for Azure Cosmos DB containers.

This class manages connection and operations for a specified Cosmos DB database and container.
It supports creating, reading, updating, and deleting items using the Azure Cosmos Python SDK.
"""

import logging

from azure.cosmos import ContainerProxy, CosmosClient, PartitionKey

logger = logging.getLogger(__name__)


class AzureRepository:
    """Repository for Azure Cosmos DB container operations.

    Args:
        connection_string (str): Connection string for Cosmos DB.
        database_name (str): Name of the Cosmos DB database.
        container_name (str): Name of the Cosmos DB container.

    """

    def __init__(self, connection_string: str, database_name: str, container_name: str):
        self.connection_string = connection_string
        self.client = CosmosClient.from_connection_string(connection_string)
        self.database = self.client.get_database_client(database_name)

    def get_container(self, container_name: str) -> ContainerProxy:
        """Get a container client for the specified container name.

        Args:
            container_name (str): The name of the container.
        """
        self.database.create_container_if_not_exists(
            id=container_name, partition_key=PartitionKey("/id")
        )
        return self.database.get_container_client(container_name)

    def create_item(self, item: dict, container_name: str) -> dict:
        """Create a new item in the Cosmos DB container.

        Args:
            item (dict): The item to be created.
            container_name (str): The name of the container where the item will be created.

        Returns:
            dict: The created item.

        """
        container = self.get_container(container_name)
        created = container.create_item(item)
        return created

    def read_item(self, item_id: str, container_name: str) -> dict:
        """Read an item from the Cosmos DB container by its ID.

        Args:
            item_id (str): The ID of the item to read.
            container_name (str): The name of the container where the item is located.

        Returns:
            dict: The retrieved item.

        """
        container = self.get_container(container_name)
        item = container.read_item(item=item_id, partition_key=item_id)
        return item

    def update_item(self, updated_item: dict, container_name: str) -> dict:
        """Update an existing item in the Cosmos DB container.

        Args:
            updated_item (dict): The updated item data.
            container_name (str): The name of the container where the item is located.

        Returns:
            dict: The upserted item.

        """
        container = self.get_container(container_name)
        upserted = container.upsert_item(updated_item)
        return upserted

    def delete_item(self, item_id: str, container_name: str) -> dict | None:
        """Delete an item from the Cosmos DB container by its ID.

        Args:
            item_id (str): The ID of the item to delete.
            container_name (str): The name of the container where the item is located.

        Returns:
            dict: The result of the delete operation.

        """
        container = self.get_container(container_name)
        result = container.delete_item(item=item_id, partition_key=item_id)
        return result

    def read_most_recent_items(self, limit: int, container_name: str) -> list[dict]:
        """Retrieve the N most recent items based on _ts timestamp.

        Args:
            limit (int): The number of most recent items to retrieve.
            container_name (str): The name of the container from which to retrieve items.

        Returns:
            list[dict]: List of the most recent items ordered by timestamp descending.

        """
        query = f"SELECT * FROM c ORDER BY c._ts DESC OFFSET 0 LIMIT {limit}"
        items = list(
            self.get_container(container_name).query_items(
                query=query, enable_cross_partition_query=True
            )
        )
        return items

    def count_items(self, container_name: str) -> int:
        """Count the number of items in the specified container.

        Args:
            container_name (str): The name of the container to count items in.

        Returns:
            int: The number of items in the container.

        """
        query = "SELECT VALUE COUNT(1) FROM c"
        results = list(
            self.get_container(container_name).query_items(
                query=query, enable_cross_partition_query=True
            )
        )
        return results[0] if results else 0

    def read_oldest_items(self, limit: int, container_name: str) -> list[dict]:
        """Retrieve the N oldest items based on _ts timestamp.

        Args:
            limit (int): The number of oldest items to retrieve.
            container_name (str): The name of the container from which to retrieve items.

        Returns:
            list[dict]: List of the oldest items ordered by timestamp ascending.

        """
        query = f"SELECT * FROM c ORDER BY c._ts ASC OFFSET 0 LIMIT {limit}"
        items = list(
            self.get_container(container_name).query_items(
                query=query, enable_cross_partition_query=True
            )
        )
        return items