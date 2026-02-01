"""
Base repository interface for Vietnam Gold Dashboard.
Defines the abstract Repository pattern.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar('T')


class Repository(ABC, Generic[T]):
    """
    Abstract base class for all data repositories.
    
    Each repository is responsible for fetching data from a single source
    and returning a validated pydantic model.
    """
    
    @abstractmethod
    def fetch(self) -> T:
        """
        Fetch data from the source.
        
        Returns:
            Pydantic model instance with validated data
            
        Raises:
            requests.exceptions.RequestException: If network request fails
            ValueError: If data parsing/validation fails
        """
        pass
