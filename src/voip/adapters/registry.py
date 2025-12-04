"""
Adapter Registry - Routes requests to correct provider adapter.
"""

import logging
from typing import Dict, Type

from src.voip.adapters.base import BaseVoIPAdapter, AdapterConfig
from src.voip.adapters.netsapiens.client import NetSapiensAdapter
from src.voip.adapters.mock.client import MockAdapter


logger = logging.getLogger("voip.adapters.registry")


class AdapterRegistry:
    """Registry of all available VoIP adapters."""
    
    _adapters: Dict[str, Type[BaseVoIPAdapter]] = {
        "netsapiens": NetSapiensAdapter,
        "mock": MockAdapter,
    }
    
    @classmethod
    def get_adapter(cls, provider_type: str, config: AdapterConfig) -> BaseVoIPAdapter:
        adapter_class = cls._adapters.get(provider_type.lower())
        
        if not adapter_class:
            supported = ", ".join(cls._adapters.keys())
            raise ValueError(f"Unsupported provider: {provider_type}. Supported: {supported}")
        
        logger.info(f"Creating adapter for: {provider_type}")
        return adapter_class(config)
    
    @classmethod
    def list_supported_providers(cls) -> list:
        return list(cls._adapters.keys())
    
    @classmethod
    def is_supported(cls, provider_type: str) -> bool:
        return provider_type.lower() in cls._adapters
