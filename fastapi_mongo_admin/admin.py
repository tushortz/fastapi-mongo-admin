"""Admin registry and ModelAdmin base class."""

from typing import Any, Iterable, Type, Union, Dict, Optional
from pydantic import BaseModel


class ModelAdmin:
    """
    Base class for admin configuration of a Pydantic model.
    
    Provides options to control the display, filtering, and behavior of models
    in the admin interface, similar to Django's ModelAdmin.
    """
    # The Pydantic model this admin class is for
    model: Optional[Type[BaseModel]] = None
    
    # The MongoDB collection name for this model (Required)
    collection_name: Optional[str] = None
    
    # Fields to display in the list view (table columns)
    list_display: Optional[list[str]] = None
    
    # Fields to use for text search
    search_fields: Optional[list[str]] = None
    
    # Fields to provide filters for in the list view
    list_filter: Optional[list[str]] = None
    
    # Number of items to display per page
    list_per_page: int = 100
    
    # Optional mapping of model field names to database collection field names
    # Example: {"model_field": "db_field"}
    field_mapping: Optional[Dict[str, str]] = None
    
    def __init__(self, model: Optional[Type[BaseModel]] = None):
        if model:
            self.model = model

class AdminSite:
    """Registry for MongoDB models in the admin interface.
    
    This class manages which models are visible in the admin UI and how they
    are configured (columns, search, etc.).
    """
    def __init__(self):
        self._registry: Dict[str, ModelAdmin] = {}

    def register(
        self, 
        model_or_iterable: Union[Type[BaseModel], Iterable[Type[BaseModel]]], 
        admin_class: Optional[Type[ModelAdmin]] = None, 
        **options: Any
    ) -> None:
        """Register model(s) with an optional ModelAdmin class.
        
        Args:
            model_or_iterable: A single Pydantic model class or an iterable of models.
            admin_class: Optional ModelAdmin subclass for custom configuration.
            **options: Optional keyword arguments to override ModelAdmin attributes.
        """
        if isinstance(model_or_iterable, type) and issubclass(model_or_iterable, BaseModel):
            models = [model_or_iterable]
        else:
            models = model_or_iterable

        for model in models:
            # Mandate collection name from options or admin_class
            collection_name = options.get("collection_name")
            
            if admin_class:
                admin_obj = admin_class(model)
                if not collection_name:
                    collection_name = getattr(admin_obj, "collection_name", None)
            else:
                admin_obj = ModelAdmin(model)
            
            if not collection_name:
                raise ValueError(
                    f"collection_name must be specified for model {model.__name__} "
                    "either in the ModelAdmin class or as a registration option."
                )
            
            # Apply options as overrides
            for key, value in options.items():
                if hasattr(admin_obj, key) or key in ["list_display", "search_fields", "list_filter"]:
                    setattr(admin_obj, key, value)
                
            self._registry[collection_name] = admin_obj

    def get_model_admin(self, collection_name: str) -> Optional[ModelAdmin]:
        """Get the ModelAdmin instance for a collection."""
        return self._registry.get(collection_name)

    def get_registered_collections(self) -> list[str]:
        """Get the list of all registered collection names."""
        return list(self._registry.keys())

    def get_pydantic_models(self) -> Dict[str, Type[BaseModel]]:
        """Get a mapping of collection names to Pydantic models."""
        return {name: admin.model for name, admin in self._registry.items() if admin.model}

    def get_models(self) -> Iterable[Type[BaseModel]]:
        """Get all registered Pydantic models."""
        return [admin.model for admin in self._registry.values() if admin.model]

# Default admin site instance
AdminSiteAlias = AdminSite # Alias for internal consistency
MongoAdmin = AdminSite    # Backward compatibility alias
site = AdminSite()
