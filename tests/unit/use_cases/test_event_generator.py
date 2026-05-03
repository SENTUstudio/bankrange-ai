"""Unit tests for the EventGenerator use case.

Validates that the generator coordinates the topology, temporal profile,
and templates to produce realistic, volume-appropriate log events.
"""

from datetime import UTC, datetime

import pytest

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
            ],
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
        profile = TemporalProfile(hourly_multipliers=[1.0] * 12 + [0.5] * 12)

        generator = EventGenerator(branches=branches, publisher=publisher, temporal_profile=profile)

        # At 10am, multiplier is 1.0 -> EPS should be 20
        dt_morning = datetime(2026, 1, 15, 10, 0, tzinfo=UTC)
        assert generator.estimated_eps(dt_morning) == 20.0

        # At 14pm, multiplier is 0.5 -> EPS should be 10
        dt_afternoon = datetime(2026, 1, 15, 14, 0, tzinfo=UTC)
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
            base_eps=5.0,  # High rate to ensure we get events
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()

        profile = TemporalProfile(hourly_multipliers=[1.0] * 24)

        generator = EventGenerator(
            branches=branches,
            publisher=publisher,
            temporal_profile=profile,
            seed=42,  # Deterministic Poisson distribution
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

    def test_set_scale_multiplier_changes_estimated_eps(self) -> None:
        """set_scale_multiplier must multiply the base estimated EPS."""
        config = TopologyConfig(
            num_branches=1,
            workstations_per_branch=10,
            employees_per_branch=10,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ],
            base_eps=2.0,
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()

        profile = TemporalProfile(hourly_multipliers=[1.0] * 24)
        generator = EventGenerator(
            branches=branches,
            publisher=publisher,
            temporal_profile=profile,
        )

        dt = datetime(2026, 1, 15, 10, 0, tzinfo=UTC)
        base_eps = generator.estimated_eps(dt)
        assert base_eps == 20.0

        generator.set_scale_multiplier(2.5)
        scaled_eps = generator.estimated_eps(dt)
        assert scaled_eps == 50.0

        # _profile must remain the original instance
        assert generator._profile is profile

    def test_set_scale_multiplier_zero_returns_zero_eps(self) -> None:
        """Scale of zero must stop generation entirely."""
        config = TopologyConfig(
            num_branches=1,
            workstations_per_branch=10,
            employees_per_branch=10,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ],
            base_eps=2.0,
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()

        profile = TemporalProfile(hourly_multipliers=[1.0] * 24)
        generator = EventGenerator(
            branches=branches,
            publisher=publisher,
            temporal_profile=profile,
        )

        generator.set_scale_multiplier(0.0)
        dt = datetime(2026, 1, 15, 10, 0, tzinfo=UTC)
        assert generator.estimated_eps(dt) == 0.0

        events = generator.generate_tick(dt)
        assert len(events) == 0

    def test_set_scale_multiplier_negative_raises_valueerror(self) -> None:
        """Negative scale must be rejected immediately."""
        config = TopologyConfig(
            num_branches=1,
            workstations_per_branch=1,
            employees_per_branch=1,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ],
            base_eps=1.0,
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()
        generator = EventGenerator(branches=branches, publisher=publisher)

        with pytest.raises(ValueError):
            generator.set_scale_multiplier(-1.0)

    def test_poisson_count_with_zero_rate_returns_zero(self) -> None:
        """Poisson count with rate <= 0 must return 0."""
        config = TopologyConfig(
            num_branches=1,
            workstations_per_branch=1,
            employees_per_branch=1,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ],
            base_eps=1.0,
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()
        generator = EventGenerator(branches=branches, publisher=publisher)

        assert generator._poisson_count(0.0) == 0
        assert generator._poisson_count(-1.0) == 0

    def test_poisson_count_returns_reasonable_values(self) -> None:
        """Poisson count with positive rate should return non-negative values."""
        config = TopologyConfig(
            num_branches=1,
            workstations_per_branch=1,
            employees_per_branch=1,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ],
            base_eps=1.0,
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()
        generator = EventGenerator(branches=branches, publisher=publisher, seed=42)

        counts = [generator._poisson_count(2.0) for _ in range(100)]
        assert all(c >= 0 for c in counts)
        assert sum(counts) > 0  # Should generate some events

    def test_get_username_is_deterministic(self) -> None:
        """Username must be deterministically derived from hostname."""
        from core.domain.entities import Workstation
        from core.domain.value_objects import IPAddress, MacAddress, OSType

        ws = Workstation(
            hostname="SUC001-PC-001",
            os_type=OSType.WINDOWS,
            ip_address=IPAddress(value="10.1.1.10"),
            mac_address=MacAddress(value="AA:BB:CC:DD:EE:01"),
            eps=2.0,
        )

        config = TopologyConfig(
            num_branches=1,
            workstations_per_branch=1,
            employees_per_branch=1,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ],
            base_eps=1.0,
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()
        generator = EventGenerator(branches=branches, publisher=publisher)

        username = generator._get_username(ws)
        assert username == "user_suc001_pc_001"

    def test_generate_metadata_returns_dict(self) -> None:
        """_generate_metadata must return a dict with expected keys."""
        from core.domain.event_templates import EventTemplate
        from core.domain.value_objects import EventType, Severity

        config = TopologyConfig(
            num_branches=1,
            workstations_per_branch=1,
            employees_per_branch=1,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ],
            base_eps=1.0,
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()
        generator = EventGenerator(branches=branches, publisher=publisher, seed=42)

        template = EventTemplate(
            event_type=EventType.AUTHENTICATION,
            severity=Severity.INFO,
            message_template="Login by {username}",
            metadata_keys=["windows_event_id", "logon_type"],
        )

        metadata = generator._generate_metadata(template)
        assert isinstance(metadata, dict)
        assert "windows_event_id" in metadata
        assert "logon_type" in metadata

    def test_metadata_value_for_unknown_key(self) -> None:
        """_metadata_value_for with unknown key should return 'unknown_<key>'."""
        config = TopologyConfig(
            num_branches=1,
            workstations_per_branch=1,
            employees_per_branch=1,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ],
            base_eps=1.0,
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()
        generator = EventGenerator(branches=branches, publisher=publisher)

        result = generator._metadata_value_for("nonexistent_key")
        assert result == "unknown_nonexistent_key"

    def test_metadata_value_for_known_keys(self) -> None:
        """_metadata_value_for with known keys should return plausible values."""
        config = TopologyConfig(
            num_branches=1,
            workstations_per_branch=1,
            employees_per_branch=1,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ],
            base_eps=1.0,
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()
        generator = EventGenerator(branches=branches, publisher=publisher, seed=42)

        # Test a few known keys
        assert isinstance(generator._metadata_value_for("windows_event_id"), int)
        assert isinstance(generator._metadata_value_for("process_id"), int)
        assert generator._metadata_value_for("protocol") in ["TCP", "UDP", "TLS"]
        assert isinstance(generator._metadata_value_for("destination_ip"), str)
        assert "." in generator._metadata_value_for("destination_ip")

    def test_create_event_structure(self) -> None:
        """_create_event must produce a valid LogEvent with correct fields."""
        from core.domain.entities import Workstation
        from core.domain.event_templates import EventTemplate
        from core.domain.value_objects import EventType, IPAddress, MacAddress, OSType, Severity

        ws = Workstation(
            hostname="SUC001-PC-001",
            os_type=OSType.WINDOWS,
            ip_address=IPAddress(value="10.1.1.10"),
            mac_address=MacAddress(value="AA:BB:CC:DD:EE:01"),
            eps=2.0,
        )

        config = TopologyConfig(
            num_branches=1,
            workstations_per_branch=1,
            employees_per_branch=1,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ],
            base_eps=1.0,
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()
        generator = EventGenerator(branches=branches, publisher=publisher, seed=42)

        template = EventTemplate(
            event_type=EventType.AUTHENTICATION,
            severity=Severity.INFO,
            message_template="Login by {username}",
            metadata_keys=["windows_event_id"],
        )

        from datetime import UTC, datetime
        tick_time = datetime(2026, 1, 15, 10, 0, tzinfo=UTC)
        event = generator._create_event(ws, "SUC001", template, tick_time)

        assert event.hostname == "SUC001-PC-001"
        assert event.branch_code == "SUC001"
        assert event.event_type == EventType.AUTHENTICATION
        assert event.os_type == OSType.WINDOWS
        assert "windows_event_id" in event.metadata

    def test_generate_tick_with_zero_multiplier_returns_empty(self) -> None:
        """When scale_multiplier is 0, generate_tick should return empty list."""
        config = TopologyConfig(
            num_branches=1,
            workstations_per_branch=10,
            employees_per_branch=10,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ],
            base_eps=2.0,
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()
        profile = TemporalProfile(hourly_multipliers=[1.0] * 24)
        generator = EventGenerator(
            branches=branches,
            publisher=publisher,
            temporal_profile=profile,
            seed=42,
        )

        generator.set_scale_multiplier(0.0)
        events = generator.generate_tick()
        assert events == []

    def test_generate_tick_publishes_batch(self) -> None:
        """generate_tick should call publish_batch on the publisher."""
        config = TopologyConfig(
            num_branches=1,
            workstations_per_branch=50,
            employees_per_branch=50,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ],
            base_eps=5.0,
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()
        profile = TemporalProfile(hourly_multipliers=[1.0] * 24)
        generator = EventGenerator(
            branches=branches,
            publisher=publisher,
            temporal_profile=profile,
            seed=42,
        )

        events = generator.generate_tick()
        assert len(events) > 0
        assert len(publisher.published_events) == len(events)

    def test_branches_property(self) -> None:
        """branches property should return the original branches."""
        config = TopologyConfig(
            num_branches=2,
            workstations_per_branch=5,
            employees_per_branch=5,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ],
            base_eps=1.0,
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()
        generator = EventGenerator(branches=branches, publisher=publisher)

        assert generator.branches is branches
        assert len(generator.branches) == 2

    def test_total_workstations(self) -> None:
        """total_workstations should reflect the topology size."""
        config = TopologyConfig(
            num_branches=2,
            workstations_per_branch=5,
            employees_per_branch=5,
            os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
            segment_templates=[
                SegmentTemplate(name_prefix="vlan", vlan_id=1, cidr_prefix="10.{branch_idx}.0.0/24")
            ],
            base_eps=1.0,
        )
        factory = TopologyFactory()
        branches = factory.create(config)
        publisher = InMemoryEventPublisher()
        generator = EventGenerator(branches=branches, publisher=publisher)

        assert generator.total_workstations == 10
