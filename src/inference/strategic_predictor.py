"""
Strategic F1 Predictor - Top-Level Hybrid System

Combines:
1. ML models (lap time, pit probability)
2. Physics-based tyre degradation curves
3. Strategic decision logic

This provides ACTIONABLE strategy recommendations, not just probabilities.
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
from src.inference.predictor import F1StrategyPredictor


class StrategicF1Predictor:
    """
    Top-level strategic prediction system.

    Uses ML + physics to provide actionable pit stop recommendations.
    """

    # Expected tyre life by compound (laps before critical degradation)
    COMPOUND_EXPECTED_LIFE = {
        'SOFT': 20,      # Soft tyres last ~20 laps before critical
        'MEDIUM': 30,    # Medium tyres last ~30 laps
        'HARD': 40       # Hard tyres last ~40 laps
    }

    # Optimal pit window (% of expected life)
    OPTIMAL_PIT_WINDOW = (0.75, 0.95)  # Pit between 75-95% of expected life

    # Critical degradation threshold (% of expected life)
    CRITICAL_THRESHOLD = 1.0

    def __init__(self, registry_path="data/registry"):
        """Initialize with ML predictor."""
        self.ml_predictor = F1StrategyPredictor(registry_path)

    def predict_strategy(self, race_state: dict) -> dict:
        """
        Predict complete race strategy with actionable recommendations.

        Args:
            race_state: Current race state (same format as ML predictor)

        Returns:
            Strategic prediction with:
            - lap_time_sec: Predicted lap time
            - tyre_wear_pct: Tyre wear percentage (0-100%)
            - degradation_rate: How fast tyre is degrading
            - pit_urgency: Urgency score (0-100)
            - pit_recommendation: Clear text recommendation
            - should_pit_in_3: Boolean - pit in next 3 laps?
            - optimal_pit_lap: Recommended pit lap
            - horizon_model: Which model to use (M4 or M5)
            - time_loss_vs_fresh: Seconds lost vs fresh tyres
        """
        # Get ML predictions
        ml_pred = self.ml_predictor.predict_single_lap(race_state)

        # Extract race state info
        compound = race_state['Compound']
        tyre_life = race_state['TyreLife']
        lap_number = race_state['LapNumber']
        lap_time = ml_pred['lap_time_sec']

        # Calculate tyre wear metrics
        tyre_wear_pct = self._calculate_tyre_wear(compound, tyre_life)
        degradation_rate = self._calculate_degradation_rate(race_state, lap_time)

        # Calculate pit urgency (0-100 scale)
        pit_urgency = self._calculate_pit_urgency(
            tyre_wear_pct, degradation_rate, compound, tyre_life
        )

        # Determine if should pit in next 3 laps
        should_pit_in_3 = pit_urgency >= 80  # High urgency threshold

        # Calculate optimal pit lap
        optimal_pit_lap = self._calculate_optimal_pit_lap(
            compound, tyre_life, lap_number, pit_urgency
        )

        # Determine which horizon model to use
        horizon_model = "M5_SHORT" if should_pit_in_3 else "M4_LONG"
        laps_until_pit = ml_pred['laps_until_pit_short'] if should_pit_in_3 else ml_pred['laps_until_pit']

        # Calculate time loss vs fresh tyres
        time_loss_vs_fresh = self._calculate_time_loss(tyre_life, compound, lap_time)

        # Generate clear recommendation
        recommendation = self._generate_recommendation(
            pit_urgency, tyre_wear_pct, compound, tyre_life, should_pit_in_3, optimal_pit_lap, lap_number
        )

        return {
            # ML predictions
            'lap_time_sec': lap_time,
            'ml_pit_probability': ml_pred['pit_probability'],
            'ml_pit_in_3': ml_pred['will_pit_in_3'],

            # Strategic metrics
            'tyre_wear_pct': tyre_wear_pct,
            'degradation_rate': degradation_rate,
            'pit_urgency': pit_urgency,
            'time_loss_vs_fresh': time_loss_vs_fresh,

            # Decision outputs
            'should_pit_in_3': should_pit_in_3,
            'optimal_pit_lap': optimal_pit_lap,
            'laps_until_pit': laps_until_pit,
            'horizon_model': horizon_model,

            # Clear recommendation
            'recommendation': recommendation,
            'pit_window_status': self._get_pit_window_status(tyre_wear_pct)
        }

    def _calculate_tyre_wear(self, compound: str, tyre_life: int) -> float:
        """Calculate tyre wear as % of expected life."""
        expected_life = self.COMPOUND_EXPECTED_LIFE.get(compound, 30)
        wear_pct = (tyre_life / expected_life) * 100
        return min(wear_pct, 100.0)  # Cap at 100%

    def _calculate_degradation_rate(self, race_state: dict, current_lap_time: float) -> str:
        """
        Calculate degradation rate based on lap time delta.

        Returns: 'Low', 'Medium', or 'High'
        """
        # Use rolling average and current lap time to measure degradation
        rolling_avg = race_state.get('Rolling5LapTime', current_lap_time)
        delta = current_lap_time - rolling_avg

        if delta < 0.5:
            return 'Low'
        elif delta < 1.5:
            return 'Medium'
        else:
            return 'High'

    def _calculate_pit_urgency(
        self, tyre_wear_pct: float, degradation_rate: str, compound: str, tyre_life: int
    ) -> float:
        """
        Calculate pit urgency score (0-100).

        Logic:
        - 0-40: No rush, stay out
        - 40-60: Approaching window
        - 60-80: In optimal window
        - 80-100: Critical, must pit soon
        """
        urgency = 0.0

        # Base urgency from tyre wear
        urgency += tyre_wear_pct * 0.8  # Max 80 points from wear

        # Degradation rate multiplier
        deg_multipliers = {'Low': 0.9, 'Medium': 1.1, 'High': 1.3}
        urgency *= deg_multipliers.get(degradation_rate, 1.0)

        # Compound-specific adjustments
        if compound == 'SOFT' and tyre_life > 22:
            urgency += 15  # SOFT critical after 22 laps
        elif compound == 'MEDIUM' and tyre_life > 32:
            urgency += 10
        elif compound == 'HARD' and tyre_life > 42:
            urgency += 10

        return min(urgency, 100.0)

    def _calculate_optimal_pit_lap(
        self, compound: str, current_tyre_life: int, current_lap: int, urgency: float
    ) -> int:
        """Calculate the optimal lap to pit."""
        expected_life = self.COMPOUND_EXPECTED_LIFE.get(compound, 30)

        # If already past optimal window, pit ASAP
        if current_tyre_life >= expected_life * 0.95:
            return current_lap + 1

        # If in optimal window, pit within 2-3 laps
        if current_tyre_life >= expected_life * 0.75:
            return current_lap + 2

        # Calculate laps to reach optimal window (80% of expected life)
        target_life = int(expected_life * 0.8)
        laps_to_wait = max(0, target_life - current_tyre_life)

        return current_lap + laps_to_wait

    def _calculate_time_loss(self, tyre_life: int, compound: str, current_lap_time: float) -> float:
        """
        Estimate time loss per lap vs fresh tyres.

        Based on tyre degradation curves.
        """
        expected_life = self.COMPOUND_EXPECTED_LIFE.get(compound, 30)
        wear_ratio = tyre_life / expected_life

        # Exponential degradation after 75% life
        if wear_ratio < 0.75:
            # Minimal degradation in first 75%
            time_loss = 0.1 * wear_ratio
        else:
            # Rapid degradation in final 25%
            excess_wear = wear_ratio - 0.75
            time_loss = 0.2 + (excess_wear * 15)  # Up to 3-4 seconds loss

        return round(time_loss, 2)

    def _get_pit_window_status(self, wear_pct: float) -> str:
        """Get human-readable pit window status."""
        if wear_pct < 60:
            return "STAY_OUT"
        elif wear_pct < 75:
            return "APPROACHING_WINDOW"
        elif wear_pct < 95:
            return "IN_OPTIMAL_WINDOW"
        else:
            return "CRITICAL_PIT_NOW"

    def _generate_recommendation(
        self, urgency: float, wear_pct: float, compound: str,
        tyre_life: int, should_pit_in_3: bool, optimal_pit_lap: int, current_lap: int
    ) -> str:
        """Generate clear, actionable recommendation."""

        if urgency >= 90:
            return f"🔴 CRITICAL: Pit IMMEDIATELY! {compound} tyres at {wear_pct:.0f}% wear ({tyre_life} laps). Time loss increasing rapidly."

        elif urgency >= 75:
            return f"🟠 HIGH PRIORITY: Pit within 2-3 laps. {compound} tyres at {wear_pct:.0f}% wear. Optimal lap: {optimal_pit_lap}"

        elif urgency >= 60:
            return f"🟡 IN WINDOW: Good time to pit. {compound} tyres at {wear_pct:.0f}% wear. Target lap: {optimal_pit_lap}"

        elif urgency >= 40:
            return f"🟢 APPROACHING: Pit window opens in ~{optimal_pit_lap - current_lap} laps. {compound} at {wear_pct:.0f}% wear."

        else:
            laps_remaining = self.COMPOUND_EXPECTED_LIFE.get(compound, 30) - tyre_life
            return f"🟢 STAY OUT: {compound} tyres fresh ({wear_pct:.0f}% wear). ~{laps_remaining} laps remaining."

    def compare_compounds(self, race_state: dict) -> dict:
        """
        Compare all three compounds for current conditions.

        Returns strategic comparison with recommendations.
        """
        compounds = ['SOFT', 'MEDIUM', 'HARD']
        comparison = []

        for compound in compounds:
            # Create state for this compound
            test_state = race_state.copy()
            test_state['Compound'] = compound
            test_state['CompoundCode'] = {'SOFT': 1, 'MEDIUM': 2, 'HARD': 3}[compound]

            # Get strategic prediction
            pred = self.predict_strategy(test_state)

            comparison.append({
                'compound': compound,
                'lap_time': pred['lap_time_sec'],
                'expected_life': self.COMPOUND_EXPECTED_LIFE[compound],
                'time_loss_per_lap': pred['time_loss_vs_fresh'],
                'pit_urgency': pred['pit_urgency'],
                'recommendation': 'Best for pace' if compound == 'SOFT'
                                else 'Balanced strategy' if compound == 'MEDIUM'
                                else 'Longest stint'
            })

        # Determine best compound based on race situation
        # (Could be enhanced with remaining laps, position, etc.)
        comparison_sorted = sorted(comparison, key=lambda x: x['lap_time'])

        return {
            'comparison': comparison,
            'recommended': comparison_sorted[0]['compound'],
            'analysis': f"For current conditions, {comparison_sorted[0]['compound']} offers best pace "
                       f"({comparison_sorted[0]['lap_time']:.2f}s). "
                       f"Consider race situation and stint length targets."
        }
