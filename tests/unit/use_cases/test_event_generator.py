"""Unit tests for the EventGenerator use case.

Validates that the generator coordinates the topology, temporal profile,
and templates to produce realistic, volume-appropriate log events.
"""

from datetime import datetime, timezone

from core.domain.temporal import TemporalProfile
from core.domain.topology_config import OSDistribution, SegmentTemplate, TopologyConfig
from core.domain.topology_factory import TopologyFactory
from core.use_cases.event_generator import EventGenerator
from tests.unit.domain.conftest import InMemoryEventPublisher


class TestEventGenerator:
    """The EventGenerator coordinates event creation for the whole topology."""

    def test_generator_initialization(self) -> None:
        """Generator initializes correctly with the provided topology."""
        config = TopologyConfig(
            num_branches=1,
            workstations_per_branch=10,
            employees_per_branch=10,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ]
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()
        
        generator = EventGenerator(branches=branches, publisher=publisher)
        assert generator.total_workstations == 10

    def test_estimated_eps_respects_temporal_multiplier(self) -> None:
        """Estimated EPS calculates base_eps * temporal_multiplier for all PCs."""
        config = TopologyConfig(
            num_branches=1,
            workstations_per_branch=10,
            employees_per_branch=10,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ],
            base_eps=2.0,  # 10 PCs * 2 EPS = 20 Base EPS total
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()
        
        # Create a rigid profile so we know exactly what to expect
        profile = TemporalProfile(
            hourly_multipliers=[1.0] * 12 + [0.5] * 12
        )
        
        generator = EventGenerator(
            branches=branches,
            publisher=publisher,
            temporal_profile=profile
        )
        
        # At 10am, multiplier is 1.0 -> EPS should be 20
        dt_morning = datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)
        assert generator.estimated_eps(dt_morning) == 20.0
        
        # At 14pm, multiplier is 0.5 -> EPS should be 10
        dt_afternoon = datetime(2026, 1, 15, 14, 0, tzinfo=timezone.utc)
        assert generator.estimated_eps(dt_afternoon) == 10.0

    def test_generate_tick_publishes_events(self) -> None:
        """Generator must create events and send them to the publisher."""
        config = TopologyConfig(
            num_branches=1,
            workstations_per_branch=50,
            employees_per_branch=50,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ],
            base_eps=5.0, # High rate to ensure we get events
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()
        
        profile = TemporalProfile(hourly_multipliers=[1.0] * 24)
        
        generator = EventGenerator(
            branches=branches,
            publisher=publisher,
            temporal_profile=profile,
            seed=42  # Deterministic Poisson distribution
        )
        
        events = generator.generate_tick()
        
        # It must return events
        assert len(events) > 0
        
        # It must have pushed events to the publisher via publish_batch
        assert len(publisher.published_events) == len(events)
        
        # Check event content
        first_event = events[0]
        assert first_event.branch_code == "SUC001"
        assert first_event.os_type.value == "windows"
        assert "windows_event_id" in first_event.metadata
