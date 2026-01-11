"""
Tests for experimental utilities for causal inference and counterfactual analysis.

This module tests:
- FactualCounterfactualPair
- ExperimentResults
- generate_counterfactual_pairs
- run_ablation_study
- compare_interventions
"""

import pytest
import numpy as np

from interphyre.interventions.experiments import (
    FactualCounterfactualPair,
    ExperimentResults,
    generate_counterfactual_pairs,
    run_ablation_study,
    compare_interventions,
)
from interphyre.interventions.state import StateSnapshot
from interphyre.engine import Box2DEngine
from interphyre.levels import load_level
from interphyre.config import SimulationConfig


# ============================================================================
# FactualCounterfactualPair Tests (8-10 tests)
# ============================================================================

@pytest.fixture
def simple_engine_factory(intervention_config):
    """Factory fixture for creating engines."""
    def factory():
        level = load_level("two_body_problem", seed=42)
        return Box2DEngine(level, config=intervention_config)
    return factory


@pytest.fixture
def boost_velocity_intervention():
    """Intervention that boosts velocity."""
    def intervene(engine):
        if "green_ball" in engine.bodies:
            body = engine.bodies["green_ball"]
            vx, vy = body.linearVelocity.x, body.linearVelocity.y
            body.linearVelocity = (vx * 1.5, vy * 1.5)
    return intervene


@pytest.mark.fast
@pytest.mark.intervention
def test_factual_counterfactual_pair_creation(intervention_env):
    """Test basic FactualCounterfactualPair instantiation."""
    engine = intervention_env.engine
    
    # Run simulation and capture snapshot
    for _ in range(10):
        engine.world.Step(engine.config.time_step, engine.config.velocity_iters, engine.config.position_iters)
        engine.time_update(engine.config.time_step)
    
    snapshot = StateSnapshot.capture(engine)
    
    pair = FactualCounterfactualPair(
        snapshot=snapshot,
        factual_result={"success": False, "reward": 0.0},
        counterfactual_result={"success": True, "reward": 1.0},
    )
    
    assert pair.snapshot == snapshot
    assert pair.factual_result == {"success": False, "reward": 0.0}
    assert pair.counterfactual_result == {"success": True, "reward": 1.0}


@pytest.mark.fast
@pytest.mark.intervention
def test_pair_with_intervention(intervention_env):
    """Test pair with intervention object stored."""
    engine = intervention_env.engine
    
    for _ in range(10):
        engine.world.Step(engine.config.time_step, engine.config.velocity_iters, engine.config.position_iters)
        engine.time_update(engine.config.time_step)
    
    snapshot = StateSnapshot.capture(engine)
    
    # Create mock intervention
    mock_intervention = lambda e: None
    
    pair = FactualCounterfactualPair(
        snapshot=snapshot,
        factual_result={"success": False},
        counterfactual_result={"success": True},
        intervention=mock_intervention,
    )
    
    assert pair.intervention == mock_intervention


@pytest.mark.fast
@pytest.mark.intervention
def test_causal_effect_positive(intervention_config):
    """Test causal effect when factual fails and counterfactual succeeds."""
    level = load_level("two_body_problem", seed=42)
    engine = Box2DEngine(level, config=intervention_config)
    snapshot = StateSnapshot.capture(engine)
    
    pair = FactualCounterfactualPair(
        snapshot=snapshot,
        factual_result={"success": False},
        counterfactual_result={"success": True},
    )
    
    effect = pair.causal_effect()
    assert effect == 1.0, f"Expected causal effect=1.0, got {effect}"


@pytest.mark.fast
@pytest.mark.intervention
def test_causal_effect_negative(intervention_config):
    """Test causal effect when factual succeeds and counterfactual fails."""
    level = load_level("two_body_problem", seed=42)
    engine = Box2DEngine(level, config=intervention_config)
    snapshot = StateSnapshot.capture(engine)
    
    pair = FactualCounterfactualPair(
        snapshot=snapshot,
        factual_result={"success": True},
        counterfactual_result={"success": False},
    )
    
    effect = pair.causal_effect()
    assert effect == -1.0, f"Expected causal effect=-1.0, got {effect}"


@pytest.mark.fast
@pytest.mark.intervention
def test_causal_effect_no_change(intervention_config):
    """Test causal effect when both outcomes are the same."""
    level = load_level("two_body_problem", seed=42)
    engine = Box2DEngine(level, config=intervention_config)
    snapshot = StateSnapshot.capture(engine)
    
    pair = FactualCounterfactualPair(
        snapshot=snapshot,
        factual_result={"success": True},
        counterfactual_result={"success": True},
    )
    
    effect = pair.causal_effect()
    assert effect == 0.0, f"Expected causal effect=0.0, got {effect}"


@pytest.mark.fast
@pytest.mark.intervention
def test_causal_effect_custom_outcome_key(intervention_config):
    """Test causal effect with custom outcome key."""
    level = load_level("two_body_problem", seed=42)
    engine = Box2DEngine(level, config=intervention_config)
    snapshot = StateSnapshot.capture(engine)
    
    pair = FactualCounterfactualPair(
        snapshot=snapshot,
        factual_result={"reward": 0.5},
        counterfactual_result={"reward": 0.8},
    )
    
    effect = pair.causal_effect(outcome_key="reward")
    assert abs(effect - 0.3) < 1e-9, f"Expected causal effect≈0.3, got {effect}"


@pytest.mark.fast
@pytest.mark.intervention
def test_causal_effect_missing_key(intervention_config):
    """Test causal effect defaults to 0 for missing keys."""
    level = load_level("two_body_problem", seed=42)
    engine = Box2DEngine(level, config=intervention_config)
    snapshot = StateSnapshot.capture(engine)
    
    pair = FactualCounterfactualPair(
        snapshot=snapshot,
        factual_result={"success": True},
        counterfactual_result={"success": True},
    )
    
    # Missing key should default to 0
    effect = pair.causal_effect(outcome_key="nonexistent")
    assert effect == 0.0, f"Expected causal effect=0.0 for missing key, got {effect}"


@pytest.mark.fast
@pytest.mark.intervention
def test_pair_snapshot_immutability(intervention_env):
    """Test that StateSnapshot is frozen/immutable."""
    engine = intervention_env.engine
    
    for _ in range(10):
        engine.world.Step(engine.config.time_step, engine.config.velocity_iters, engine.config.position_iters)
        engine.time_update(engine.config.time_step)
    
    snapshot = StateSnapshot.capture(engine)
    
    pair = FactualCounterfactualPair(
        snapshot=snapshot,
        factual_result={"success": False},
        counterfactual_result={"success": True},
    )
    
    # Try to modify snapshot (should fail)
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        pair.snapshot.step_index = 999


@pytest.mark.fast
@pytest.mark.intervention
def test_pair_metadata(intervention_config):
    """Test that pair can store metadata."""
    level = load_level("two_body_problem", seed=42)
    engine = Box2DEngine(level, config=intervention_config)
    snapshot = StateSnapshot.capture(engine)
    
    pair = FactualCounterfactualPair(
        snapshot=snapshot,
        factual_result={"success": False},
        counterfactual_result={"success": True},
        metadata={"trial_id": 42, "intervention_type": "boost"},
    )
    
    assert pair.metadata["trial_id"] == 42
    assert pair.metadata["intervention_type"] == "boost"


# ============================================================================
# ExperimentResults Tests (10-12 tests)
# ============================================================================

@pytest.mark.fast
def test_experiment_results_creation_empty():
    """Test empty ExperimentResults initialization."""
    results = ExperimentResults()
    
    assert len(results.trials) == 0, "Should start with empty trials"
    assert len(results.metadata) == 0, "Should start with empty metadata"


@pytest.mark.fast
def test_add_trial_single():
    """Test adding a single trial."""
    results = ExperimentResults()
    results.add_trial({"success": True, "reward": 1.0})
    
    assert len(results.trials) == 1, "Should have 1 trial"
    assert results.trials[0] == {"success": True, "reward": 1.0}


@pytest.mark.fast
def test_add_trial_multiple():
    """Test adding multiple trials."""
    results = ExperimentResults()
    results.add_trial({"success": True, "reward": 1.0})
    results.add_trial({"success": False, "reward": 0.0})
    results.add_trial({"success": True, "reward": 0.8})
    
    assert len(results.trials) == 3, "Should have 3 trials"


@pytest.mark.fast
def test_get_mean_basic():
    """Test mean calculation for a key."""
    results = ExperimentResults()
    results.add_trial({"reward": 1.0})
    results.add_trial({"reward": 2.0})
    results.add_trial({"reward": 3.0})
    
    mean = results.get_mean("reward")
    assert abs(mean - 2.0) < 1e-9, f"Expected mean=2.0, got {mean}"


@pytest.mark.fast
def test_get_mean_empty_trials():
    """Test mean calculation handles empty trials gracefully."""
    results = ExperimentResults()
    
    mean = results.get_mean("reward")
    # numpy.mean of empty list returns nan, which is expected behavior
    import numpy as np
    assert np.isnan(mean) or mean == 0.0, f"Expected mean=0.0 or nan for empty trials, got {mean}"


@pytest.mark.fast
def test_get_std_basic():
    """Test standard deviation calculation."""
    results = ExperimentResults()
    results.add_trial({"reward": 1.0})
    results.add_trial({"reward": 2.0})
    results.add_trial({"reward": 3.0})
    
    std = results.get_std("reward")
    expected_std = np.std([1.0, 2.0, 3.0])
    assert abs(std - expected_std) < 1e-6, f"Expected std≈{expected_std}, got {std}"


@pytest.mark.fast
def test_get_success_rate_all_success():
    """Test success rate when all trials succeed."""
    results = ExperimentResults()
    results.add_trial({"success": True})
    results.add_trial({"success": True})
    results.add_trial({"success": True})
    
    rate = results.get_success_rate()
    assert abs(rate - 1.0) < 1e-9, f"Expected success rate=1.0, got {rate}"


@pytest.mark.fast
def test_get_success_rate_half_success():
    """Test success rate when half trials succeed."""
    results = ExperimentResults()
    results.add_trial({"success": True})
    results.add_trial({"success": False})
    results.add_trial({"success": True})
    results.add_trial({"success": False})
    
    rate = results.get_success_rate()
    assert abs(rate - 0.5) < 1e-9, f"Expected success rate=0.5, got {rate}"


@pytest.mark.fast
def test_get_success_rate_no_trials():
    """Test success rate with no trials."""
    results = ExperimentResults()
    
    rate = results.get_success_rate()
    assert rate == 0.0, f"Expected success rate=0.0 for no trials, got {rate}"


@pytest.mark.fast
def test_summary_basic():
    """Test summary returns dict with mean/std for all keys."""
    results = ExperimentResults()
    results.add_trial({"reward": 1.0, "steps": 10})
    results.add_trial({"reward": 2.0, "steps": 20})
    results.add_trial({"reward": 3.0, "steps": 30})
    
    summary = results.summary()
    
    assert "num_trials" in summary
    assert summary["num_trials"] == 3
    assert "reward_mean" in summary
    assert "reward_std" in summary
    assert "steps_mean" in summary
    assert "steps_std" in summary


@pytest.mark.fast
def test_summary_includes_success_rate():
    """Test that summary includes success_rate if available."""
    results = ExperimentResults()
    results.add_trial({"success": True})
    results.add_trial({"success": False})
    
    summary = results.summary()
    
    assert "success_rate" in summary, "Summary should include success_rate"
    assert abs(summary["success_rate"] - 0.5) < 1e-9


@pytest.mark.fast
def test_summary_empty_trials():
    """Test summary with empty trials."""
    results = ExperimentResults()
    
    summary = results.summary()
    
    assert summary == {"num_trials": 0}, f"Expected empty summary, got {summary}"


# ============================================================================
# generate_counterfactual_pairs Tests (6-8 tests)
# ============================================================================

@pytest.mark.fast
@pytest.mark.intervention
def test_generate_counterfactual_pairs_basic(simple_engine_factory, boost_velocity_intervention):
    """Test that generate_counterfactual_pairs returns list of pairs."""
    pairs = generate_counterfactual_pairs(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        interventions=[boost_velocity_intervention],
        simulation_steps=20,
        num_trials=1,
        seed=42,
    )
    
    assert isinstance(pairs, list), "Should return list of pairs"
    assert len(pairs) > 0, "Should have at least one pair"


@pytest.mark.fast
@pytest.mark.intervention
def test_generate_pairs_correct_count(simple_engine_factory, boost_velocity_intervention):
    """Test that correct number of pairs is generated (num_trials × num_interventions)."""
    pairs = generate_counterfactual_pairs(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        interventions=[boost_velocity_intervention],
        simulation_steps=20,
        num_trials=3,
        seed=42,
    )
    
    # Should have 3 trials × 1 intervention = 3 pairs
    assert len(pairs) == 3, f"Expected 3 pairs, got {len(pairs)}"


@pytest.mark.fast
@pytest.mark.intervention
def test_generate_pairs_multiple_interventions(simple_engine_factory):
    """Test generation with multiple interventions."""
    def intervention1(engine):
        if "green_ball" in engine.bodies:
            body = engine.bodies["green_ball"]
            body.linearVelocity = (0, 0)
    
    def intervention2(engine):
        if "green_ball" in engine.bodies:
            body = engine.bodies["green_ball"]
            vx, vy = body.linearVelocity.x, body.linearVelocity.y
            body.linearVelocity = (vx * 2.0, vy * 2.0)
    
    pairs = generate_counterfactual_pairs(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        interventions=[intervention1, intervention2],
        simulation_steps=20,
        num_trials=2,
        seed=42,
    )
    
    # Should have 2 trials × 2 interventions = 4 pairs
    assert len(pairs) == 4, f"Expected 4 pairs, got {len(pairs)}"


@pytest.mark.fast
@pytest.mark.intervention
def test_generate_pairs_intervention_timing(simple_engine_factory, boost_velocity_intervention):
    """Test that snapshot is captured at intervention_step."""
    pairs = generate_counterfactual_pairs(
        engine_factory=simple_engine_factory,
        intervention_step_index=15,
        interventions=[boost_velocity_intervention],
        simulation_steps=30,
        num_trials=1,
        seed=42,
    )
    
    assert len(pairs) > 0
    # Snapshot should be at step 15
    assert pairs[0].snapshot.step_index == 15, \
        f"Expected snapshot at step 15, got {pairs[0].snapshot.step_index}"


@pytest.mark.fast
@pytest.mark.intervention
def test_generate_pairs_with_seed(simple_engine_factory, boost_velocity_intervention):
    """Test that seed makes generation deterministic."""
    pairs1 = generate_counterfactual_pairs(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        interventions=[boost_velocity_intervention],
        simulation_steps=20,
        num_trials=2,
        seed=42,
    )
    
    pairs2 = generate_counterfactual_pairs(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        interventions=[boost_velocity_intervention],
        simulation_steps=20,
        num_trials=2,
        seed=42,
    )
    
    # Results should be identical with same seed
    assert len(pairs1) == len(pairs2)
    # Compare factual results (should be same)
    assert pairs1[0].factual_result == pairs2[0].factual_result


@pytest.mark.fast
@pytest.mark.intervention
def test_generate_pairs_metadata_populated(simple_engine_factory, boost_velocity_intervention):
    """Test that pairs have metadata populated."""
    pairs = generate_counterfactual_pairs(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        interventions=[boost_velocity_intervention],
        simulation_steps=20,
        num_trials=1,
        seed=42,
    )
    
    assert len(pairs) > 0
    assert "trial_idx" in pairs[0].metadata
    assert "intervention_step_index" in pairs[0].metadata
    assert "simulation_steps" in pairs[0].metadata


# ============================================================================
# run_ablation_study Tests (4-6 tests)
# ============================================================================

@pytest.mark.fast
@pytest.mark.intervention
def test_ablation_study_freeze_basic(simple_engine_factory):
    """Test ablation study with freeze type."""
    results = run_ablation_study(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        object_names=["green_ball"],
        simulation_steps=20,
        ablation_type="freeze",
    )
    
    assert isinstance(results, dict), "Should return dict of results"
    assert "green_ball" in results, "Should have results for green_ball"
    assert isinstance(results["green_ball"], ExperimentResults)


@pytest.mark.fast
@pytest.mark.intervention
def test_ablation_study_remove_basic(simple_engine_factory):
    """Test ablation study with remove type."""
    results = run_ablation_study(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        object_names=["green_ball"],
        simulation_steps=20,
        ablation_type="remove",
    )
    
    assert isinstance(results, dict)
    assert "green_ball" in results
    assert isinstance(results["green_ball"], ExperimentResults)


@pytest.mark.fast
@pytest.mark.intervention
def test_ablation_study_multiple_objects(simple_engine_factory):
    """Test ablation study with multiple objects."""
    results = run_ablation_study(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        object_names=["green_ball", "red_ball"],
        simulation_steps=20,
        ablation_type="freeze",
    )
    
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    assert "green_ball" in results
    assert "red_ball" in results


@pytest.mark.fast
@pytest.mark.intervention
def test_ablation_study_results_format(simple_engine_factory):
    """Test that ablation study returns ExperimentResults."""
    results = run_ablation_study(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        object_names=["green_ball"],
        simulation_steps=20,
        ablation_type="freeze",
    )
    
    exp_results = results["green_ball"]
    assert isinstance(exp_results, ExperimentResults)
    assert len(exp_results.trials) == 1, "Should have 1 trial per object"
    assert "baseline_success" in exp_results.trials[0]
    assert "ablated_success" in exp_results.trials[0]
    assert "causal_effect" in exp_results.trials[0]


@pytest.mark.fast
@pytest.mark.intervention
def test_ablation_study_causal_effect_calculation(simple_engine_factory):
    """Test that causal effect is calculated as ablated - baseline."""
    results = run_ablation_study(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        object_names=["green_ball"],
        simulation_steps=20,
        ablation_type="freeze",
    )
    
    trial = results["green_ball"].trials[0]
    baseline = trial["baseline_success"]
    ablated = trial["ablated_success"]
    effect = trial["causal_effect"]
    
    expected_effect = float(ablated) - float(baseline)
    assert abs(effect - expected_effect) < 1e-9, \
        f"Expected causal_effect={expected_effect}, got {effect}"


# ============================================================================
# compare_interventions Tests (4-6 tests)
# ============================================================================

@pytest.mark.fast
@pytest.mark.intervention
def test_compare_interventions_baseline(simple_engine_factory):
    """Test that baseline is included in comparison results."""
    def intervention1(engine):
        if "green_ball" in engine.bodies:
            body = engine.bodies["green_ball"]
            body.linearVelocity = (0, 0)
    
    results = compare_interventions(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        interventions={"freeze_green": intervention1},
        simulation_steps=20,
        num_trials=2,
        seed=42,
    )
    
    assert "baseline" in results, "Should include baseline"
    assert isinstance(results["baseline"], ExperimentResults)


@pytest.mark.fast
@pytest.mark.intervention
def test_compare_interventions_single(simple_engine_factory):
    """Test comparison with single intervention."""
    def intervention1(engine):
        if "green_ball" in engine.bodies:
            body = engine.bodies["green_ball"]
            body.linearVelocity = (0, 0)
    
    results = compare_interventions(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        interventions={"freeze_green": intervention1},
        simulation_steps=20,
        num_trials=2,
        seed=42,
    )
    
    assert len(results) == 2, f"Expected 2 results (baseline + 1 intervention), got {len(results)}"
    assert "baseline" in results
    assert "freeze_green" in results


@pytest.mark.fast
@pytest.mark.intervention
def test_compare_interventions_multiple(simple_engine_factory):
    """Test comparison with multiple interventions."""
    def intervention1(engine):
        if "green_ball" in engine.bodies:
            body = engine.bodies["green_ball"]
            body.linearVelocity = (0, 0)
    
    def intervention2(engine):
        if "green_ball" in engine.bodies:
            body = engine.bodies["green_ball"]
            vx, vy = body.linearVelocity.x, body.linearVelocity.y
            body.linearVelocity = (vx * 2.0, vy * 2.0)
    
    results = compare_interventions(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        interventions={"freeze": intervention1, "boost": intervention2},
        simulation_steps=20,
        num_trials=2,
        seed=42,
    )
    
    assert len(results) == 3, f"Expected 3 results (baseline + 2 interventions), got {len(results)}"
    assert "baseline" in results
    assert "freeze" in results
    assert "boost" in results


@pytest.mark.fast
@pytest.mark.intervention
def test_compare_interventions_num_trials(simple_engine_factory):
    """Test that each intervention has correct number of trials."""
    def intervention1(engine):
        if "green_ball" in engine.bodies:
            body = engine.bodies["green_ball"]
            body.linearVelocity = (0, 0)
    
    results = compare_interventions(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        interventions={"freeze": intervention1},
        simulation_steps=20,
        num_trials=5,
        seed=42,
    )
    
    # Each should have 5 trials
    assert len(results["baseline"].trials) == 5, \
        f"Baseline should have 5 trials, got {len(results['baseline'].trials)}"
    assert len(results["freeze"].trials) == 5, \
        f"Intervention should have 5 trials, got {len(results['freeze'].trials)}"


@pytest.mark.fast
@pytest.mark.intervention
def test_compare_interventions_with_seed(simple_engine_factory):
    """Test that seed makes comparison deterministic."""
    def intervention1(engine):
        if "green_ball" in engine.bodies:
            body = engine.bodies["green_ball"]
            body.linearVelocity = (0, 0)
    
    results1 = compare_interventions(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        interventions={"freeze": intervention1},
        simulation_steps=20,
        num_trials=2,
        seed=42,
    )
    
    results2 = compare_interventions(
        engine_factory=simple_engine_factory,
        intervention_step_index=10,
        interventions={"freeze": intervention1},
        simulation_steps=20,
        num_trials=2,
        seed=42,
    )
    
    # Baseline results should be identical
    assert results1["baseline"].trials == results2["baseline"].trials, \
        "Results should be identical with same seed"

