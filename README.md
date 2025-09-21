# Satellite Collision Detection System

**Started by:** Shivansh Mishra
**Date:** 19 September 2025  

## Problem Statement
With thousands of satellites and space debris orbiting Earth, the risk of collisions is rising. This project aims to detect possible collisions and alert relevant systems to prevent damage.

## Proposed Solution
- Collect satellite position data (TLE data from CelesTrak / NORAD).
- Simulate or propagate satellite orbits.
- Detect potential conjunctions (close approaches).
- Provide alerts or visualizations for predicted collision events.

## Planned Tech Stack
- **Language:** C++ / Python
- **Libraries:** For parsing TLE, orbital calculations (SGP4 library)
- **Output:** Command-line results + optional visualization dashboard

## Goals
- Basic prototype to detect close-approach events
- Future scope: Real-time dashboard, predictive modeling
