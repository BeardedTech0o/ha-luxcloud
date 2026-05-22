# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [1.0.0] — 2025-05-22

### Added
- Initial release
- Cloud API client for LuxPower inverters (Global and EU regions)
- 30+ sensor entities: solar power, battery power & SOC, grid import/export, load power, PV string voltages & currents, temperatures, daily and lifetime energy totals, inverter status and work mode
- AC charge switch
- Number controls: AC charge current limit, discharge cutoff SOC, charge cutoff SOC
- Work mode select: Self-use, Feed-in Priority, Backup, Manual
- Config flow with credential validation and duplicate-entry protection
- Reauthentication flow for expired sessions
- Reconfiguration flow to update credentials or region without re-adding
- `luxcloud.refresh` service for on-demand data refresh
- Diagnostics support with redacted credential output
- Entity categories: `DIAGNOSTIC` for technical sensors, `CONFIG` for controls
- Entity and icon translations
- HACS support via `hacs.json`
- GitHub Actions: HACS validation, hassfest validation, release asset upload
- Config flow test suite

[Unreleased]: https://github.com/BeardedTech0o/ha-luxcloud/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/BeardedTech0o/ha-luxcloud/releases/tag/v1.0.0
