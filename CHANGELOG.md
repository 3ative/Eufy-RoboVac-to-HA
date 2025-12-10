# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.0.0] - 2025-12-11

### 🎉 Major Performance Optimization Release

This release completely rewrites the integration to eliminate database performance issues and modernize for Home Assistant 2025.5+.

### Added
- **NEW:** Shared connection manager prevents connection spam and conflicts
- **NEW:** Separate battery sensor entity with optimized 60-second updates
- **NEW:** Separate charging binary sensor entity with optimized 60-second updates
- **NEW:** Smart caching system prevents "unavailable" flickers during brief disconnects
- **NEW:** State change detection prevents unnecessary database writes
- **NEW:** Configurable rate limiting with minimum update intervals
- **NEW:** Improved error handling and automatic reconnection logic
- **NEW:** Modern `StateVacuumEntity` implementation with `VacuumActivity` enum
- **NEW:** Comprehensive logging for debugging connection issues

### Changed
- **PERFORMANCE:** Reduced database writes by 78% (from ~26,000/day to ~5,760/day)
- **PERFORMANCE:** Vacuum update interval: 5s → 30s (6x improvement)
- **PERFORMANCE:** Battery sensor updates: 10s → 60s (6x improvement)
- **PERFORMANCE:** Charging sensor: constant polling → 60s updates
- Modernized vacuum entity to use `activity` property instead of deprecated `state`
- Updated to use `VacuumEntityFeature` enum (HA 2025.5+ requirement)
- Optimized attribute updates to reduce database load
- Improved entity availability logic with cached values
- All entities now share a single connection to the vacuum
- Platform loading moved to modern `async_load_platform` method

### Fixed
- **CRITICAL:** Fixed Home Assistant watchdog timeout reboots caused by excessive database writes
- **CRITICAL:** Fixed connection spam causing "Connection reset by peer" errors
- Fixed indentation error in `tuya.py` line 580
- Fixed entity "unavailable" flickers during temporary connection issues
- Fixed deprecated `VacuumEntity` warnings for HA 2025.5+
- Fixed missing `async_stop` method causing service errors
- Fixed configuration key handling for both `access_token` and `local_key`
- Fixed battery and charging attributes for xiaomi-vacuum-card compatibility

### Removed
- **BREAKING:** Removed `platform.py` (replaced with modern platform loading in `__init__.py`)
- Removed deprecated battery properties from vacuum entity (now separate sensor)
- Removed excessive debug logging that contributed to database load

### Technical Details
- Connection manager uses `asyncio.Lock` for thread-safe operations
- Rate limiting: 30s default, 10s minimum for forced updates
- Entities maintain last known good values during update failures
- All platforms (`vacuum`, `sensor`, `binary_sensor`) share connection instance
- Compatible with Home Assistant 2025.5+ through 2025.8+

### Migration Notes
**No breaking changes** - existing configurations work without modification.

**New entities created:**
- `sensor.{name}_battery` - Battery percentage sensor
- `binary_sensor.{name}_charging` - Charging status sensor

**Optional:** You can hide these new entities if you only use the vacuum attributes.

### Performance Comparison

| Metric | v1.0 | v2.0 | Improvement |
|--------|------|------|-------------|
| Database writes/day | ~26,000 | ~5,760 | **78% reduction** |
| Vacuum updates | 5s | 30s | **6x slower** |
| Battery updates | 10s | 60s | **6x slower** |
| Watchdog reboots | Frequent | **None** | ✅ **Eliminated** |
| Connection errors | Common | **Rare** | ✅ **Fixed** |

---

## [1.0.0] - 2021-10-12

### Initial Release
- Basic Eufy RoboVac integration for Home Assistant
- Support for T2118 model
- Vacuum entity with controls (start, pause, stop, return)
- Fan speed control (Off, Standard, Boost IQ, Max)
- Battery level reporting
- Spot cleaning and locate functions

### Known Issues (Fixed in v2.0.0)
- Excessive database writes causing performance issues
- Watchdog timeout reboots on some systems
- Connection spam and "Connection reset by peer" errors
- Deprecated code warnings in HA 2025.5+

---

## How to Report Issues

Found a bug? Have a feature request?

1. Check [existing issues](https://github.com/3ative/Eufy-RoboVac-to-HA/issues)
2. Create a new issue with:
   - Home Assistant version
   - Eufy RoboVac model
   - Log entries (if applicable)
   - Description of the issue

---

## Credits

- Original integration: [Richard Mitchell](https://github.com/mitchellrj/eufy_robovac)
- Optimization and modernization: [3ative](https://github.com/3ative)
- Testing and feedback: Eufy RoboVac community

---

**Thank you to everyone who uses and supports this integration!** ❤️

[Buy me a coffee](https://www.buymeacoffee.com/3ative) | [Support on Patreon](https://www.patreon.com/3ative)
