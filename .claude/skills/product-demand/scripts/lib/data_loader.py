"""
Data Loading Utilities for Demand Forecasting
Generalized loader for any entity (vehicles, energy, batteries, commodities, etc.)
"""

import json
import os
from typing import Dict, List, Tuple, Optional


class DataLoader:
    """Handles loading and accessing forecasting data for any entity"""

    def __init__(self, entity_file_path: str, taxonomy_file_path: Optional[str] = None):
        """
        Initialize data loader

        Args:
            entity_file_path: Path to entity JSON file (e.g., Passenger_Cars.json)
            taxonomy_file_path: Path to taxonomy JSON file (optional)
        """
        self.entity_file_path = entity_file_path
        self.taxonomy_file_path = taxonomy_file_path

        # Load entity data
        self.entity_data = self._load_entity_data()

        # Load taxonomy if provided
        self.taxonomy = self._load_taxonomy() if taxonomy_file_path else None

    def _load_entity_data(self) -> dict:
        """Load entity curves data from JSON file"""
        with open(self.entity_file_path, 'r') as f:
            data = json.load(f)

        # Handle different JSON structures
        # Some files have a top-level key (e.g., {"Passenger Cars": {...}})
        # Others are direct dictionaries
        if len(data) == 1 and isinstance(list(data.values())[0], dict):
            # Likely has entity name as top-level key
            entity_name = list(data.keys())[0]
            return data[entity_name]
        else:
            return data

    def _load_taxonomy(self) -> Optional[dict]:
        """Load taxonomy and dataset mappings"""
        if not self.taxonomy_file_path or not os.path.exists(self.taxonomy_file_path):
            return None

        with open(self.taxonomy_file_path, 'r') as f:
            return json.load(f)

    def _load_json(self, file_path: str) -> dict:
        """Load JSON file"""
        with open(file_path, 'r') as f:
            return json.load(f)

    def get_dataset(self, dataset_name: str) -> dict:
        """
        Get a specific dataset by name

        Args:
            dataset_name: Name of the dataset (metric)

        Returns:
            Dataset dictionary with metadata and regions
        """
        if dataset_name not in self.entity_data:
            raise ValueError(f"Dataset {dataset_name} not found in entity data")

        return self.entity_data[dataset_name]

    def get_data_for_region(
        self,
        dataset_name: str,
        region: str,
        subkey: Optional[str] = None
    ) -> Tuple[List[int], List[float]]:
        """
        Get X,Y data for a specific dataset and region

        Args:
            dataset_name: Name of the dataset
            region: Region name (e.g., "China", "USA", "Europe", "Rest_of_World", "Global")
            subkey: Optional subkey for nested data (e.g., "standard", "TaaSAdj")

        Returns:
            Tuple of (years, values)
        """
        dataset = self.get_dataset(dataset_name)

        if "regions" not in dataset:
            raise ValueError(f"Dataset {dataset_name} has no regions field")

        region_data = dataset["regions"].get(region, {})

        if not region_data:
            raise ValueError(f"No data for region {region} in dataset {dataset_name}")

        # Handle different data structures
        if subkey:
            # User specified a subkey
            if subkey not in region_data:
                raise ValueError(f"Subkey {subkey} not found in {dataset_name} for region {region}")
            years = region_data[subkey]["X"]
            values = region_data[subkey]["Y"]
        elif "X" in region_data and "Y" in region_data:
            # Direct X/Y structure
            years = region_data["X"]
            values = region_data["Y"]
        elif "standard" in region_data:
            # Nested with "standard" subkey
            years = region_data["standard"]["X"]
            values = region_data["standard"]["Y"]
        else:
            raise ValueError(f"Unexpected data structure for {dataset_name} in region {region}")

        return years, values

    def get_cost_data(self, product_name: str, region: str) -> Tuple[List[int], List[float]]:
        """
        Get cost curve for a product in a region (using taxonomy if available)

        Args:
            product_name: Product name (e.g., "EV_Cars", "ICE_Cars")
            region: Region name

        Returns:
            Tuple of (years, costs)
        """
        if self.taxonomy:
            # Use taxonomy to find dataset name
            try:
                dataset_name = self.taxonomy["data"][product_name]["cost"][region]
            except KeyError:
                raise ValueError(
                    f"Cannot find cost dataset for {product_name} in {region} via taxonomy"
                )
        else:
            # Fallback: construct dataset name (e.g., "EV_Cars_Cost")
            dataset_name = f"{product_name}_Cost"

        return self.get_data_for_region(dataset_name, region)

    def get_demand_data(self, product_name: str, region: str) -> Tuple[List[int], List[float]]:
        """
        Get demand/sales curve for a product in a region (using taxonomy if available)

        Args:
            product_name: Product name (e.g., "Passenger_Vehicles", "BEV_Cars")
            region: Region name

        Returns:
            Tuple of (years, demand_values)
        """
        if self.taxonomy:
            # Use taxonomy to find dataset name
            try:
                demand_mapping = self.taxonomy["data"][product_name]["demand"]

                if isinstance(demand_mapping, dict):
                    dataset_name = demand_mapping[region]
                else:
                    dataset_name = demand_mapping
            except KeyError:
                raise ValueError(
                    f"Cannot find demand dataset for {product_name} in {region} via taxonomy"
                )
        else:
            # Fallback: construct dataset name (e.g., "BEV_Cars_Demand")
            dataset_name = f"{product_name}_Demand"

        return self.get_data_for_region(dataset_name, region)

    def get_all_regions(self) -> List[str]:
        """Get list of all available regions in the entity data"""
        # Get first dataset to extract regions
        if not self.entity_data:
            return []

        first_dataset_name = list(self.entity_data.keys())[0]
        first_dataset = self.entity_data[first_dataset_name]

        if "regions" in first_dataset:
            return list(first_dataset["regions"].keys())

        return []

    def get_entity_type(self, product_name: str) -> str:
        """
        Get entity type for a product

        Args:
            product_name: Product name

        Returns:
            Entity type: "disruptor", "incumbent", "chimera", "market", or "unknown"
        """
        if not self.taxonomy:
            # Try to infer from dataset metadata
            try:
                # Look for a dataset with this product name
                for dataset_name, dataset in self.entity_data.items():
                    if product_name in dataset_name:
                        metadata = dataset.get("metadata", {})
                        return metadata.get("entity_type", "unknown")
            except:
                pass
            return "unknown"

        # Use taxonomy
        try:
            return self.taxonomy["data"][product_name].get("entity_type", "unknown")
        except KeyError:
            return "unknown"

    def list_all_datasets(self) -> List[str]:
        """Get list of all available datasets in the entity"""
        return list(self.entity_data.keys())

    def get_metadata(self, dataset_name: str) -> dict:
        """
        Get metadata for a dataset

        Args:
            dataset_name: Name of the dataset

        Returns:
            Metadata dictionary
        """
        dataset = self.get_dataset(dataset_name)
        return dataset.get("metadata", {})
