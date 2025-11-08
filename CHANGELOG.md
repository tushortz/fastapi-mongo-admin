## Changelog

### Version 0.0.3

#### New Features

- **Sortable Tables**: Click any column header to sort data ascending/descending
  - Visual indicators show current sort column and direction
  - Sort state persists during pagination
  - Works with both list and search endpoints

- **Form Pagination**: Forms automatically paginated for better UX
  - Maximum 5 fields per page
  - Previous/Next navigation buttons
  - Page indicator showing current page
  - All field values preserved across pages during submission

- **Advanced Server-Side Filtering**:
  - **Text Fields**: Case-insensitive regex matching for text/string fields
  - **Enum Fields**: Direct/exact matching for enum fields
  - **Boolean Fields**: True/False dropdown filters
  - **Date Fields**: Date picker with day-range matching
  - Filters work in combination with search queries
  - All filtering performed server-side for better performance

- **Enhanced Search**:
  - Server-side text search across multiple string fields
  - Support for MongoDB JSON queries
  - Search combined with active filters
  - Improved search performance with backend filtering

- **Dark Mode Support**: Complete dark mode theme for the admin UI
  - Toggle between light and dark themes with a single click
  - Theme preference persisted in localStorage
  - Comprehensive dark mode styling for all UI components
  - Smooth theme transitions with visual feedback
  - Separate CSS files for light and dark modes for optimal performance

#### Improvements

- **Filter UI**:
  - Filters automatically regenerate when schema changes
  - Filter section hidden when no filterable fields available
  - Better filter label formatting with titleize
  - Filters reset when changing collections

- **Table Headers**:
  - Clickable headers with hover effects
  - Active sort column highlighted with blue background
  - Sort indicators (↑ for ascending, ↓ for descending, ↕ for unsorted)

- **Form Experience**:
  - Paginated forms reduce visual clutter
  - All fields accessible via navigation
  - Form state maintained across page changes

- **API Enhancements**:
  - Added `sort_field` and `sort_order` parameters to list and search endpoints
  - Improved query building for filters
  - Better error handling for invalid queries

- **Theme Management**:
  - Automatic theme initialization on page load
  - Reactive theme switching using custom Store pattern
  - Consistent color scheme across all UI elements
  - Proper contrast ratios for accessibility in both themes
  - Improved dark mode toggle functionality with CSS file switching
  - Dark mode styles now properly applied via separate `darkmode.css` file
  - Light mode uses `lightmode.css` for optimal performance

- **Sidebar Enhancement**:
  - Fixed sidebar collapse functionality
  - Corrected CSS selectors to use ID selector (`#sidenav`) instead of class selector
  - Sidebar now properly collapses and expands when toggle button is clicked

- **Code Cleanup**:
  - Removed unused Svelte dependency
  - Removed Svelte CDN import that was never used
  - Updated documentation to reflect custom reactive state management instead of Svelte-like

#### Bug Fixes

- Fixed form field collection when using pagination
- Fixed filter state management when switching collections
- Improved schema refetching for filters
- Fixed scope issues with data variable in loadDocuments
- Fixed sidebar not collapsing when toggle button was clicked
- Fixed CSS selector mismatch for sidebar collapsed state

### Version 0.0.2

#### New Features

- **Pydantic Model Support**: Infer schemas from Pydantic models when collections are empty
  - Register models via `pydantic_models` parameter in `create_router()`
  - Automatic schema generation from model fields, types, and defaults
  - Support for all Pydantic field types (str, int, float, bool, list, dict, Optional, etc.)

- **OpenAPI/Swagger Schema Discovery**: Automatically discover and use Pydantic models from FastAPI's OpenAPI schema
  - Pass `app` parameter to `create_router()` to enable auto-discovery
  - Smart matching: handles exact, case-insensitive, and singular/plural variations
  - Optional `openapi_schema_map` for explicit collection-to-model mapping
  - No manual registration required - models are discovered automatically

- **Enhanced Admin UI**:
  - **Modern Design**: Migrated to Tailwind CSS CDN for responsive, modern styling
  - **Reactive State Management**: Implemented custom reactive store pattern for UI updates
  - **Search Functionality**: Text search and MongoDB JSON query support
  - **Document Viewing**: View documents in modal dialogs with formatted display
  - **Document Details Page**: Full-page document view with navigation history
  - **Clickable ObjectIds**: Navigate between documents by clicking ObjectId fields
  - **Collapsible Sidebar**: Toggle sidebar visibility with state persistence
  - **Confirmation Modals**: Custom confirmation dialogs instead of browser alerts
  - **Type Preservation**: Maintains data types (int, float, bool, objects, arrays) when creating/editing
  - **Smart Form Generation**: Form fields automatically generated based on schema types
  - **Better UX**: Centered modals, loading indicators, and improved error messages

#### Improvements

- **Schema Inference Priority**:
  1. Existing documents (if collection has data)
  2. Registered Pydantic models (if provided)
  3. OpenAPI/Swagger schemas (if app is provided)
  4. Empty schema (fallback)

- **Form Field Generation**:
  - Better handling of different data types
  - Proper rendering of objects and arrays as JSON textareas
  - Type validation and preservation during form submission
  - Support for nullable fields and default values

- **API Enhancements**:
  - Schema endpoint now supports multiple inference sources
  - Better error handling and logging
  - Improved type conversion and validation

#### Bug Fixes

- Fixed modal centering issues
- Fixed CSS selector errors with Tailwind classes
- Improved form data type preservation
- Better handling of empty collections

#### Documentation

- Updated README with comprehensive examples
- Added documentation for Pydantic model support
- Added documentation for OpenAPI schema discovery
- Enhanced API reference with schema inference details

### Version 0.0.1

- Initial release
- Generic CRUD operations
- Schema introspection
- Admin UI
- ObjectId serialization utilities