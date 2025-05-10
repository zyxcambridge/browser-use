# Browser-Use Project Index

## Directory Structure

### Core Modules
- **agent/**: Core agent functionality
  - `service.py`: Main agent service implementation
  - `memory/`: Memory management components
  - `message_manager/`: Message handling and communication
  - `gif.py`: GIF recording functionality
  - `playwright_script_generator.py`: Script generation for browser automation

- **browser/**: Browser interaction layer
  - `browser.py`: Main browser interface
  - `chrome.py`: Chrome browser implementation
  - `context.py`: Browser context management
  - `utils/`: Browser-related utility functions

- **controller/**: API controllers
  - `service.py`: Controller service implementation
  - `views.py`: API endpoints

- **dom/**: DOM tree processing
  - `service.py`: DOM manipulation utilities
  - `buildDomTree.js`: JavaScript DOM tree builder
  - `clickable_element_processor/`: Element interaction handlers

- **telemetry/**: Monitoring and analytics
  - `service.py`: Telemetry collection
  - `views.py`: Metrics reporting

### Supporting Components
- **docs/**: Documentation (MDX format)
- **examples/**: Usage examples across different scenarios
- **tests/**: Test suite (pytest)
- **static/**: Static assets
- **eval/**: Evaluation frameworks

## Key Files
- `README.md`: Project overview
- `pyproject.toml`: Python project configuration
- `Dockerfile`: Containerization setup
- `pytest.ini`: Test configuration
- `.pre-commit-config.yaml`: Pre-commit hooks

## Architecture Overview
[Architecture diagram](docs/images/browser-use.png)