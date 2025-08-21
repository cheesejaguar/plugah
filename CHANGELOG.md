# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-01-21

### Added
- Stable public API with four-phase execution pipeline
  - `startup_phase()` - Generate discovery questions
  - `process_discovery()` - Process answers into PRD
  - `plan_organization()` - Create OAG from PRD
  - `execute()` - Execute the planned organization
- Top-level exports: `BoardRoom`, `BudgetPolicy`
- State persistence methods (`to_dict()`, `from_dict()`, `save_state()`, `load_state()`)
- Mock mode for CI testing via `PLUGAH_MODE=mock` environment variable
- Exception hierarchy for better error handling
  - `PlugahError` - Base exception
  - `InvalidInput` - Invalid input validation
  - `BudgetExceeded` - Budget limit exceeded
  - `ProviderError` - LLM provider errors
- Public types: `ExecutionResult`, `PRD`, `Event`, `OAG`
- JSON schemas for PRD and OAG structures
- Event streaming support via `events_stream()` async iterator
- Execution event callbacks via `on_event` parameter

### Changed
- Refactored BoardRoom to provide stable, documented API surface
- Moved internal implementation to separate modules
- Updated README with comprehensive API documentation
- Bumped version to 0.2.0 for semantic versioning

### Fixed
- Type hints for better IDE support
- Consistent async/await patterns across all methods

## [0.1.0] - 2024-01-15

### Added
- Initial release
- Core orchestration system with organizational hierarchy
- Startup discovery phase with co-founders
- Dynamic organization planning based on PRD
- Budget management with CFO oversight
- OKR/KPI tracking and metrics rollup
- Task execution with budget gates
- CrewAI integration for agent materialization
- Web interface for interactive experience
- CLI demo for quick testing

[0.2.0]: https://github.com/cheesejaguar/plugah/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/cheesejaguar/plugah/releases/tag/v0.1.0