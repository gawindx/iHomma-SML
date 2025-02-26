# Changelog

## [0.2.2] - 2024-02-26
### Amended
-Improvement of bulbs availability detection via "HLK_" verification
-Optimization of Timeouts UDP management
-Refactoring of the network communication code
-Update of documentation for groups

### Corrected
-Correction of the Decoding of UDP (Bytes Conversion -> Str) responses
-Improvement of state restoration after unavailability
-Correction of synchronization between groups and individual bulbs

## [0.2.0] - 2024-02-18
### Added
-Support for bulbs groups
-Shared state manager for group/bulb synchronization
-Detailed logs for debugging
-Adaptive timer for the availability of bulbs

### modified
-Improvement of states management
-Optimization of network communications
-Reorganization of the code with separate device class

### Corrected
-State restoration after unavailability
-Management of unique identifiers
-Synchronization between groups and individual bulbs

## [0.2.0] - 2024-02-18
### Initial Commit
-ON/OFF control
-Luminosity adjustment
-Color temperature change (2700K-6500K)
-RGB colors
-predefined light effects