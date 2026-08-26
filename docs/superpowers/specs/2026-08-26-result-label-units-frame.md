# Result label units and plot frame spec

## Goal
Correct two visual regressions reported from Google Colab in anaStruct Plus v0.2.4.

## Requirements
- Horizontal result plots keep the transverse numeric scale hidden, but the left plot spine remains visible so the plot frame does not look vertically clipped.
- Vertical result plots keep the transverse numeric scale hidden, but the bottom plot spine remains visible for the same reason.
- Moment annotations include the configured moment unit directly beside every displayed relevant value.
- Shear annotations include the configured force unit directly beside every displayed relevant value.
- Axial annotations use the same force-unit behavior for consistency.
- Titles retain their current units.
- `values_only=True` and solver behavior remain unchanged.
- Validate with automated tests and the real anaStruct 4 m reference render.
