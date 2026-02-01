# Changelog

All notable changes to Interphyre will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-01

### Initial Release

#### Added
- 25 physics-based puzzle levels with procedural generation
- Gymnasium-compatible environment interface (`PhyreEnv`)
- Intervention system for multi-turn control and counterfactuals
- Multiple rendering backends (Pygame, OpenCV)
- Comprehensive documentation and examples
- Data collection tools for RL research
- Viewer module for visualization (`python -m interphyre.viewer`)

#### Features
- Deterministic physics simulation using Box2D
- One-shot and intervention-based gameplay modes
- Custom level creation API
- Video recording and visualization tools
- Contact tracking and success condition system
- State snapshot and restoration for branching simulations

#### Physics Objects
- Ball: Dynamic and static spheres
- Bar: Rectangular obstacles and platforms
- Basket: U-shaped containers

#### Levels
One-ball levels: basket_case, catapult, dive_bomb, flagpole_sitta, just_a_nudge,
locust_swarm, mind_the_gap, off_the_rails, pass_the_parcel, pinball_machine,
seesaw, the_cradle, tipping_point, two_body_problem

Two-ball levels: Additional levels with multiple dynamic balls

#### Tools
- Data collection with CEM and random agents
- Random agent benchmarking
- Interactive visualization and demo modes
- Video recording (MP4/GIF export)
