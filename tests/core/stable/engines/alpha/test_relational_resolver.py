# Copyright 2026 Emcie Co Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from lagom import Container

from parlant.core.engines.alpha.guideline_matching.guideline_match import GuidelineMatch
from parlant.core.engines.alpha.relational_resolver import RelationalResolver
from parlant.core.journey_guideline_projection import JourneyGuidelineProjection
from parlant.core.journeys import JourneyStore
from parlant.core.relationships import (
    RelationshipEntityKind,
    RelationshipKind,
    RelationshipEntity,
    RelationshipStore,
)
from parlant.core.guidelines import GuidelineStore
from parlant.core.tags import TagStore, Tag


async def test_that_relational_resolver_prioritizes_indirectly_between_guidelines(
    container: Container,
) -> None:
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    resolver = container[RelationalResolver]

    g1 = await guideline_store.create_guideline(condition="x", action="y")
    g2 = await guideline_store.create_guideline(condition="y", action="z")
    g3 = await guideline_store.create_guideline(condition="z", action="t")

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=g1.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=g2.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=g2.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=g3.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    result = await resolver.resolve(
        [g1, g2, g3],
        [
            GuidelineMatch(guideline=g1, score=8, rationale=""),
            GuidelineMatch(guideline=g2, score=5, rationale=""),
            GuidelineMatch(guideline=g3, score=9, rationale=""),
        ],
        journeys=[],
    )

    assert result.matches == [GuidelineMatch(guideline=g1, score=8, rationale="")]


async def test_that_relational_resolver_prioritizes_between_journey_nodes(
    container: Container,
) -> None:
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    journey_store = container[JourneyStore]

    resolver = container[RelationalResolver]

    j1_condition = await guideline_store.create_guideline(
        condition="Customer is interested in Journey 1"
    )
    j2_condition = await guideline_store.create_guideline(
        condition="Customer is interested in Journey 2"
    )

    j1 = await journey_store.create_journey(
        title="Journey 1",
        description="Description for Journey 1",
        conditions=[j1_condition.id],
    )

    j2 = await journey_store.create_journey(
        title="Journey 2",
        description="Description for Journey 2",
        conditions=[j2_condition.id],
    )

    j1_guidelines = await container[JourneyGuidelineProjection].project_journey_to_guidelines(j1.id)
    j2_guidelines = await container[JourneyGuidelineProjection].project_journey_to_guidelines(j2.id)

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=Tag.for_journey_id(j1.id),
            kind=RelationshipEntityKind.TAG,
        ),
        target=RelationshipEntity(
            id=Tag.for_journey_id(j2.id),
            kind=RelationshipEntityKind.TAG,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    assert len(j1_guidelines) == 1
    assert len(j2_guidelines) == 1

    result = await resolver.resolve(
        [j1_guidelines[0], j2_guidelines[0]],
        [
            GuidelineMatch(guideline=j1_guidelines[0], score=8, rationale=""),
            GuidelineMatch(guideline=j2_guidelines[0], score=5, rationale=""),
        ],
        journeys=[j1, j2],
    )

    assert result.matches == [GuidelineMatch(guideline=j1_guidelines[0], score=8, rationale="")]


async def test_that_relational_resolver_prioritizes_guideline_over_journey(
    container: Container,
) -> None:
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    journey_store = container[JourneyStore]
    projection = container[JourneyGuidelineProjection]
    resolver = container[RelationalResolver]

    # Create a standalone guideline
    standalone_guideline = await guideline_store.create_guideline(
        condition="Customer asks about drinks",
        action="Recommend Pepsi",
    )

    # Create a journey with a condition
    journey_condition = await guideline_store.create_guideline(
        condition="Customer asks about drinks"
    )

    journey = await journey_store.create_journey(
        title="Drink Recommendation Journey",
        description="Recommend Coca-Cola to the customer",
        conditions=[journey_condition.id],
    )

    # Add nodes to the journey to create a graph
    journey_node_1 = await journey_store.create_node(
        journey_id=journey.id,
        action="Ask what drink they want",
        tools=[],
    )

    journey_node_2 = await journey_store.create_node(
        journey_id=journey.id,
        action="Recommend Coca-Cola",
        tools=[],
    )

    # Add an edge between the nodes
    await journey_store.create_edge(
        journey_id=journey.id,
        source=journey_node_1.id,
        target=journey_node_2.id,
        condition=None,
    )

    # Project journey to get journey-guidelines
    journey_guidelines = await projection.project_journey_to_guidelines(journey.id)
    assert len(journey_guidelines) > 0

    # Create priority relationship: standalone guideline > journey
    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=standalone_guideline.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=Tag.for_journey_id(journey.id),
            kind=RelationshipEntityKind.TAG,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    # Both the standalone guideline and journey-guidelines match
    journey_matches = [
        GuidelineMatch(guideline=g, score=5 + i, rationale="")
        for i, g in enumerate(journey_guidelines)
    ]
    result = await resolver.resolve(
        [standalone_guideline] + list(journey_guidelines),
        [GuidelineMatch(guideline=standalone_guideline, score=8, rationale="")] + journey_matches,
        journeys=[journey],
    )

    # Only the standalone guideline should remain (all journey-guidelines are filtered out)
    assert result.matches == [GuidelineMatch(guideline=standalone_guideline, score=8, rationale="")]


async def test_that_relational_resolver_prioritizes_journey_over_guideline(
    container: Container,
) -> None:
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    journey_store = container[JourneyStore]
    projection = container[JourneyGuidelineProjection]
    resolver = container[RelationalResolver]

    # Create a journey with a condition
    journey_condition = await guideline_store.create_guideline(
        condition="Customer asks about drinks"
    )

    journey = await journey_store.create_journey(
        title="Drink Recommendation Journey",
        description="Recommend Pepsi to the customer",
        conditions=[journey_condition.id],
    )

    # Add nodes to the journey to create a graph
    journey_node_1 = await journey_store.create_node(
        journey_id=journey.id,
        action="Ask what drink they want",
        tools=[],
    )

    journey_node_2 = await journey_store.create_node(
        journey_id=journey.id,
        action="Recommend Pepsi",
        tools=[],
    )

    # Add an edge between the nodes
    await journey_store.create_edge(
        journey_id=journey.id,
        source=journey_node_1.id,
        target=journey_node_2.id,
        condition=None,
    )

    # Project journey to get journey-guidelines
    journey_guidelines = await projection.project_journey_to_guidelines(journey.id)
    assert len(journey_guidelines) > 0

    # Create a standalone guideline
    standalone_guideline = await guideline_store.create_guideline(
        condition="Customer asks about drinks",
        action="Recommend Coca-Cola",
    )

    # Create priority relationship: journey > standalone guideline
    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=Tag.for_journey_id(journey.id),
            kind=RelationshipEntityKind.TAG,
        ),
        target=RelationshipEntity(
            id=standalone_guideline.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    # Both journey-guidelines and standalone guideline match
    journey_matches = [
        GuidelineMatch(guideline=g, score=8 - i, rationale="")
        for i, g in enumerate(journey_guidelines)
    ]
    result = await resolver.resolve(
        list(journey_guidelines) + [standalone_guideline],
        journey_matches + [GuidelineMatch(guideline=standalone_guideline, score=10, rationale="")],
        journeys=[journey],
    )

    # The standalone guideline should be filtered out because journey prioritizes over it
    # Only the journey-guidelines remain
    assert result.matches == journey_matches


async def test_that_relational_resolver_filters_journey_dependent_guideline_when_journey_is_deprioritized(
    container: Container,
) -> None:
    """
    Tests the transitive effect of priority + dependency:
    - Guideline Y prioritizes over Journey J
    - Guideline X depends on Journey J
    - When Y, X, and J are all active, Y's priority over J should filter out X
      (because X depends on J, and J is deprioritized)
    """
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    journey_store = container[JourneyStore]
    resolver = container[RelationalResolver]

    # Create a journey
    journey_condition = await guideline_store.create_guideline(
        condition="Customer asks about drinks"
    )

    journey = await journey_store.create_journey(
        title="Drink Recommendation Journey",
        description="Recommend Coca-Cola to the customer",
        conditions=[journey_condition.id],
    )

    # Create guideline X that depends on the journey
    guideline_x = await guideline_store.create_guideline(
        condition="Customer asks about drinks",
        action="Recommend Sprite",
    )

    # Create dependency: X depends on Journey
    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=guideline_x.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=Tag.for_journey_id(journey.id),
            kind=RelationshipEntityKind.TAG,
        ),
        kind=RelationshipKind.DEPENDENCY,
    )

    # Create guideline Y that prioritizes over the journey
    guideline_y = await guideline_store.create_guideline(
        condition="Customer asks about drinks",
        action="Recommend Pepsi",
    )

    # Create priority: Y prioritizes over Journey
    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=guideline_y.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=Tag.for_journey_id(journey.id),
            kind=RelationshipEntityKind.TAG,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    # Both Y and X are active
    result = await resolver.resolve(
        [guideline_y, guideline_x],
        [
            GuidelineMatch(guideline=guideline_y, score=8, rationale=""),
            GuidelineMatch(guideline=guideline_x, score=6, rationale=""),
        ],
        journeys=[journey],
    )

    # Only Y should remain:
    # - Y prioritizes over J, so J is effectively deprioritized
    # - X depends on J, so when J is deprioritized, X is also filtered out
    assert result.matches == [GuidelineMatch(guideline=guideline_y, score=8, rationale="")]


async def test_that_relational_resolver_does_not_ignore_a_deprioritized_guideline_when_its_prioritized_counterpart_is_not_active(
    container: Container,
) -> None:
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    resolver = container[RelationalResolver]

    prioritized_guideline = await guideline_store.create_guideline(condition="x", action="y")
    deprioritized_guideline = await guideline_store.create_guideline(condition="y", action="z")

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=prioritized_guideline.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=deprioritized_guideline.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    matches: list[GuidelineMatch] = [
        GuidelineMatch(guideline=deprioritized_guideline, score=5, rationale=""),
    ]

    result = await resolver.resolve([prioritized_guideline, deprioritized_guideline], matches, [])

    assert result.matches == [
        GuidelineMatch(guideline=deprioritized_guideline, score=5, rationale="")
    ]


async def test_that_relational_resolver_does_not_ignore_deprioritized_journey_node_when_prioritized_journey_is_not_active(
    container: Container,
) -> None:
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    journey_store = container[JourneyStore]
    projection = container[JourneyGuidelineProjection]
    resolver = container[RelationalResolver]

    prioritized_condition = await guideline_store.create_guideline(
        condition="Customer is interested in Journey A"
    )
    deprioritized_condition = await guideline_store.create_guideline(
        condition="Customer is interested in Journey B"
    )

    prioritized_journey = await journey_store.create_journey(
        title="Journey A",
        description="High priority journey",
        conditions=[prioritized_condition.id],
    )
    deprioritized_journey = await journey_store.create_journey(
        title="Journey B",
        description="Lower priority journey",
        conditions=[deprioritized_condition.id],
    )

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=Tag.for_journey_id(prioritized_journey.id),
            kind=RelationshipEntityKind.TAG,
        ),
        target=RelationshipEntity(
            id=Tag.for_journey_id(deprioritized_journey.id),
            kind=RelationshipEntityKind.TAG,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    prioritized_guidelines = await projection.project_journey_to_guidelines(prioritized_journey.id)
    deprioritized_guidelines = await projection.project_journey_to_guidelines(
        deprioritized_journey.id
    )

    assert len(prioritized_guidelines) == 1
    assert len(deprioritized_guidelines) == 1

    deprioritized_guideline = deprioritized_guidelines[0]
    prioritized_guideline = prioritized_guidelines[0]

    result = await resolver.resolve(
        [prioritized_guideline, deprioritized_guideline],
        [
            GuidelineMatch(guideline=deprioritized_guideline, score=5, rationale=""),
        ],
        journeys=[],
    )

    assert result.matches == [
        GuidelineMatch(guideline=deprioritized_guideline, score=5, rationale="")
    ]


async def test_that_relational_resolver_prioritizes_guidelines(
    container: Container,
) -> None:
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    resolver = container[RelationalResolver]

    prioritized_guideline = await guideline_store.create_guideline(condition="x", action="y")
    deprioritized_guideline = await guideline_store.create_guideline(condition="y", action="z")

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=prioritized_guideline.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=deprioritized_guideline.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    matches: list[GuidelineMatch] = [
        GuidelineMatch(guideline=prioritized_guideline, score=8, rationale=""),
        GuidelineMatch(guideline=deprioritized_guideline, score=5, rationale=""),
    ]

    result = await resolver.resolve([prioritized_guideline, deprioritized_guideline], matches, [])

    assert result.matches == [
        GuidelineMatch(guideline=prioritized_guideline, score=8, rationale="")
    ]


async def test_that_relational_resolver_infers_guidelines_from_tags(
    container: Container,
) -> None:
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    tag_store = container[TagStore]
    resolver = container[RelationalResolver]

    g1 = await guideline_store.create_guideline(condition="x", action="y")
    g2 = await guideline_store.create_guideline(condition="y", action="z")
    g3 = await guideline_store.create_guideline(condition="z", action="t")
    g4 = await guideline_store.create_guideline(condition="t", action="u")

    t1 = await tag_store.create_tag(name="t1")

    await guideline_store.upsert_tag(guideline_id=g2.id, tag_id=t1.id)
    await guideline_store.upsert_tag(guideline_id=g3.id, tag_id=t1.id)

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=g1.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=t1.id,
            kind=RelationshipEntityKind.TAG,
        ),
        kind=RelationshipKind.ENTAILMENT,
    )

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=t1.id,
            kind=RelationshipEntityKind.TAG,
        ),
        target=RelationshipEntity(
            id=g4.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.ENTAILMENT,
    )

    result = await resolver.resolve(
        [g1, g2, g3, g4],
        [
            GuidelineMatch(guideline=g1, score=8, rationale=""),
        ],
        journeys=[],
    )

    assert len(result.matches) == 4
    assert any(m.guideline.id == g1.id for m in result.matches)
    assert any(m.guideline.id == g2.id for m in result.matches)
    assert any(m.guideline.id == g3.id for m in result.matches)
    assert any(m.guideline.id == g4.id for m in result.matches)


async def test_that_relational_resolver_does_not_ignore_a_deprioritized_tag_when_its_prioritized_counterpart_is_not_active(
    container: Container,
) -> None:
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    tag_store = container[TagStore]
    resolver = container[RelationalResolver]

    prioritized_guideline = await guideline_store.create_guideline(condition="x", action="y")
    deprioritized_guideline = await guideline_store.create_guideline(condition="y", action="z")

    deprioritized_tag = await tag_store.create_tag(name="t1")

    await guideline_store.upsert_tag(deprioritized_guideline.id, deprioritized_tag.id)

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=prioritized_guideline.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=deprioritized_tag.id,
            kind=RelationshipEntityKind.TAG,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=deprioritized_tag.id,
            kind=RelationshipEntityKind.TAG,
        ),
        target=RelationshipEntity(
            id=deprioritized_guideline.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    result = await resolver.resolve(
        [prioritized_guideline, deprioritized_guideline],
        [
            GuidelineMatch(guideline=deprioritized_guideline, score=5, rationale=""),
        ],
        journeys=[],
    )

    assert len(result.matches) == 1
    assert result.matches[0].guideline.id == deprioritized_guideline.id


async def test_that_relational_resolver_prioritizes_guidelines_from_tags(
    container: Container,
) -> None:
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    tag_store = container[TagStore]
    resolver = container[RelationalResolver]

    g1 = await guideline_store.create_guideline(condition="x", action="y")
    g2 = await guideline_store.create_guideline(condition="y", action="z")

    t1 = await tag_store.create_tag(name="t1")

    await guideline_store.upsert_tag(g2.id, t1.id)

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=g1.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=t1.id,
            kind=RelationshipEntityKind.TAG,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=t1.id,
            kind=RelationshipEntityKind.TAG,
        ),
        target=RelationshipEntity(
            id=g2.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    result = await resolver.resolve(
        [g1, g2],
        [
            GuidelineMatch(guideline=g1, score=8, rationale=""),
            GuidelineMatch(guideline=g2, score=5, rationale=""),
        ],
        journeys=[],
    )

    assert len(result.matches) == 1
    assert result.matches[0].guideline.id == g1.id


async def test_that_relational_resolver_handles_indirect_guidelines_from_tags(
    container: Container,
) -> None:
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    tag_store = container[TagStore]
    resolver = container[RelationalResolver]

    g1 = await guideline_store.create_guideline(condition="x", action="y")
    g2 = await guideline_store.create_guideline(condition="y", action="z")
    g3 = await guideline_store.create_guideline(condition="z", action="t")

    t1 = await tag_store.create_tag(name="t1")

    await guideline_store.upsert_tag(g2.id, t1.id)

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=g1.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=t1.id,
            kind=RelationshipEntityKind.TAG,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=t1.id,
            kind=RelationshipEntityKind.TAG,
        ),
        target=RelationshipEntity(
            id=g3.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    result = await resolver.resolve(
        [g1, g2, g3],
        [
            GuidelineMatch(guideline=g1, score=8, rationale=""),
            GuidelineMatch(guideline=g3, score=9, rationale=""),
        ],
        journeys=[],
    )

    assert len(result.matches) == 1
    assert result.matches[0].guideline.id == g1.id


async def test_that_relational_resolver_filters_out_guidelines_with_unmet_dependencies(
    container: Container,
) -> None:
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    resolver = container[RelationalResolver]

    source_guideline = await guideline_store.create_guideline(
        condition="Customer has not specified if it's a repeat transaction or a new one",
        action="Ask them which it is",
    )
    target_guideline = await guideline_store.create_guideline(
        condition="Customer wants to make a transaction", action="Help them"
    )

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=source_guideline.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=target_guideline.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.DEPENDENCY,
    )

    result = await resolver.resolve(
        [source_guideline, target_guideline],
        [
            GuidelineMatch(guideline=source_guideline, score=8, rationale=""),
        ],
        journeys=[],
    )

    assert result.matches == []


async def test_that_relational_resolver_filters_out_guidelines_with_unmet_dependencies_connected_through_tag(
    container: Container,
) -> None:
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    tag_store = container[TagStore]
    resolver = container[RelationalResolver]

    source_guideline = await guideline_store.create_guideline(condition="a", action="b")

    tagged_guideline_1 = await guideline_store.create_guideline(condition="c", action="d")
    tagged_guideline_2 = await guideline_store.create_guideline(condition="e", action="f")

    target_tag = await tag_store.create_tag(name="t1")

    await guideline_store.upsert_tag(tagged_guideline_1.id, target_tag.id)
    await guideline_store.upsert_tag(tagged_guideline_2.id, target_tag.id)

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=source_guideline.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=target_tag.id,
            kind=RelationshipEntityKind.TAG,
        ),
        kind=RelationshipKind.DEPENDENCY,
    )

    result = await resolver.resolve(
        [source_guideline, tagged_guideline_1, tagged_guideline_2],
        [
            GuidelineMatch(guideline=source_guideline, score=8, rationale=""),
            GuidelineMatch(guideline=tagged_guideline_1, score=10, rationale=""),
            # Missing match for tagged_guideline_2
        ],
        journeys=[],
    )

    assert len(result.matches) == 1
    assert result.matches[0].guideline.id == tagged_guideline_1.id


async def test_that_relational_resolver_filters_out_journey_nodes_with_unmet_journey_dependency_with_guideline(
    container: Container,
) -> None:
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    journey_store = container[JourneyStore]
    projection = container[JourneyGuidelineProjection]
    resolver = container[RelationalResolver]

    source_condition = await guideline_store.create_guideline(
        condition="Customer has not specified if it's a repeat transaction or a new one",
        action="Ask them which it is",
    )

    source_journey = await journey_store.create_journey(
        title="Clarify Transaction Type",
        description="Journey for asking if it's repeat or new transaction",
        conditions=[source_condition.id],
    )

    guideline = await guideline_store.create_guideline(
        condition="Customer wants to make a transaction",
        action="Help them",
    )

    source_journey_guidelines = await projection.project_journey_to_guidelines(source_journey.id)

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=Tag.for_journey_id(source_journey.id),
            kind=RelationshipEntityKind.TAG,
        ),
        target=RelationshipEntity(
            id=guideline.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.DEPENDENCY,
    )

    assert len(source_journey_guidelines) == 1

    result = await resolver.resolve(
        [source_journey_guidelines[0], guideline],
        [
            GuidelineMatch(guideline=source_journey_guidelines[0], score=8, rationale=""),
        ],
        journeys=[],
    )

    assert result.matches == []


async def test_that_relational_resolver_filters_out_journey_nodes_with_unmet_journey_dependencies(
    container: Container,
) -> None:
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    journey_store = container[JourneyStore]
    projection = container[JourneyGuidelineProjection]
    resolver = container[RelationalResolver]

    source_condition = await guideline_store.create_guideline(
        condition="Customer has not specified if it's a repeat transaction or a new one",
        action="Ask them which it is",
    )

    source_journey = await journey_store.create_journey(
        title="Clarify Transaction Type",
        description="Journey for asking if it's repeat or new transaction",
        conditions=[source_condition.id],
    )

    target_journey = await journey_store.create_journey(
        title="Validate Account",
        description="Journey for validating account",
        conditions=[],
    )

    source_journey_guidelines = await projection.project_journey_to_guidelines(source_journey.id)
    target_journey_guidelines = await projection.project_journey_to_guidelines(target_journey.id)

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=Tag.for_journey_id(source_journey.id),
            kind=RelationshipEntityKind.TAG,
        ),
        target=RelationshipEntity(
            id=Tag.for_journey_id(target_journey.id),
            kind=RelationshipEntityKind.TAG,
        ),
        kind=RelationshipKind.DEPENDENCY,
    )

    assert len(source_journey_guidelines) == 1
    assert len(target_journey_guidelines) == 1

    result = await resolver.resolve(
        [source_journey_guidelines[0], target_journey_guidelines[0]],
        [
            GuidelineMatch(guideline=source_journey_guidelines[0], score=8, rationale=""),
        ],
        journeys=[source_journey],
    )

    assert result.matches == []


async def test_that_relational_resolver_filters_dependent_guidelines_by_journey_tags_when_journeys_are_not_relatively_enabled(
    container: Container,
) -> None:
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    journey_store = container[JourneyStore]
    resolver = container[RelationalResolver]

    enabled_journey = await journey_store.create_journey(
        title="First Journey",
        description="Description",
        conditions=[],
    )
    disabled_journey = await journey_store.create_journey(
        title="Second Journey",
        description="Description",
        conditions=[],
    )

    enabled_journey_tagged_guideline = await guideline_store.create_guideline(
        condition="a", action="b"
    )
    disabled_journey_tagged_guideline = await guideline_store.create_guideline(
        condition="c", action="d"
    )

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=enabled_journey_tagged_guideline.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=Tag.for_journey_id(enabled_journey.id),
            kind=RelationshipEntityKind.TAG,
        ),
        kind=RelationshipKind.DEPENDENCY,
    )

    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=disabled_journey_tagged_guideline.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=Tag.for_journey_id(disabled_journey.id),
            kind=RelationshipEntityKind.TAG,
        ),
        kind=RelationshipKind.DEPENDENCY,
    )

    result = await resolver.resolve(
        [enabled_journey_tagged_guideline, disabled_journey_tagged_guideline],
        [
            GuidelineMatch(guideline=enabled_journey_tagged_guideline, score=8, rationale=""),
            GuidelineMatch(guideline=disabled_journey_tagged_guideline, score=10, rationale=""),
        ],
        journeys=[enabled_journey],
    )

    assert len(result.matches) == 1
    assert result.matches[0].guideline.id == enabled_journey_tagged_guideline.id


async def test_that_relational_resolver_iterates_until_stable_with_cascading_priorities(
    container: Container,
) -> None:
    """
    Tests iterative resolution with cascading priorities:
    - Guideline A prioritizes over B
    - Guideline B prioritizes over C
    - Guideline C depends on D
    - All four start as matches
    - First iteration: A deprioritizes B
    - Second iteration: C loses dependency on B (B is gone)
    - Expected: A, D remain (B deprioritized, C filtered due to lost dependency on B)
    """
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    resolver = container[RelationalResolver]

    # Create guidelines
    guideline_a = await guideline_store.create_guideline(
        condition="Customer asks about priority",
        action="Recommend option A",
    )
    guideline_b = await guideline_store.create_guideline(
        condition="Customer asks about priority",
        action="Recommend option B",
    )
    guideline_c = await guideline_store.create_guideline(
        condition="Customer asks about priority",
        action="Recommend option C",
    )
    guideline_d = await guideline_store.create_guideline(
        condition="Customer asks about priority",
        action="Recommend option D",
    )

    # A prioritizes over B
    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=guideline_a.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=guideline_b.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    # B prioritizes over C
    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=guideline_b.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=guideline_c.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    # C depends on B
    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=guideline_c.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=guideline_b.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.DEPENDENCY,
    )

    # All four are matches
    result = await resolver.resolve(
        [guideline_a, guideline_b, guideline_c, guideline_d],
        [
            GuidelineMatch(guideline=guideline_a, score=8, rationale=""),
            GuidelineMatch(guideline=guideline_b, score=7, rationale=""),
            GuidelineMatch(guideline=guideline_c, score=6, rationale=""),
            GuidelineMatch(guideline=guideline_d, score=5, rationale=""),
        ],
        journeys=[],
    )

    # Only A and D should remain:
    # - First iteration: B is deprioritized by A
    # - Second iteration: C loses dependency on B (B is gone), so C is filtered
    # - D has no relationships, remains
    assert len(result.matches) == 2
    assert any(m.guideline.id == guideline_a.id for m in result.matches)
    assert any(m.guideline.id == guideline_d.id for m in result.matches)


async def test_that_relational_resolver_handles_priority_affecting_dependency_in_second_iteration(
    container: Container,
) -> None:
    """
    Tests that priority relationships discovered via entailment affect dependencies:
    - Guideline X depends on Y
    - Guideline A entails Z
    - Z prioritizes over Y
    - Initial matches: [A, X, Y]
    - First iteration: A entails Z (now matches: [A, X, Y, Z])
    - Second iteration: Z prioritizes over Y, X loses dependency
    - Expected: Only A and Z remain
    """
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    resolver = container[RelationalResolver]

    # Create guidelines
    guideline_a = await guideline_store.create_guideline(
        condition="Customer needs help",
        action="Offer help",
    )
    guideline_x = await guideline_store.create_guideline(
        condition="Customer needs help",
        action="Provide option X",
    )
    guideline_y = await guideline_store.create_guideline(
        condition="Customer needs help",
        action="Provide option Y",
    )
    guideline_z = await guideline_store.create_guideline(
        condition="Customer needs help",
        action="Provide option Z (override)",
    )

    # X depends on Y
    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=guideline_x.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=guideline_y.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.DEPENDENCY,
    )

    # A entails Z
    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=guideline_a.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=guideline_z.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.ENTAILMENT,
    )

    # Z prioritizes over Y
    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=guideline_z.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        target=RelationshipEntity(
            id=guideline_y.id,
            kind=RelationshipEntityKind.GUIDELINE,
        ),
        kind=RelationshipKind.PRIORITY,
    )

    # Initial matches: A, X, Y
    result = await resolver.resolve(
        [guideline_a, guideline_x, guideline_y, guideline_z],
        [
            GuidelineMatch(guideline=guideline_a, score=8, rationale=""),
            GuidelineMatch(guideline=guideline_x, score=7, rationale=""),
            GuidelineMatch(guideline=guideline_y, score=6, rationale=""),
        ],
        journeys=[],
    )

    # Only A and Z should remain:
    # - First iteration: A entails Z (Z added to matches)
    # - Second iteration: Z prioritizes over Y (Y deprioritized), X loses dependency
    assert len(result.matches) == 2
    assert any(m.guideline.id == guideline_a.id for m in result.matches)
    assert any(m.guideline.id == guideline_z.id for m in result.matches)


async def test_that_relational_resolver_filters_guidelines_by_priority_keeping_only_highest(
    container: Container,
) -> None:
    """
    Tests that after all relational resolution, only guidelines sharing the
    highest priority value survive.

    - Guideline A has priority=1
    - Guideline B has priority=0 (default)
    - Both are active matches with no relationships between them
    - Expected: Only A survives because it has the highest priority
    """
    guideline_store = container[GuidelineStore]
    resolver = container[RelationalResolver]

    guideline_a = await guideline_store.create_guideline(
        condition="Customer asks about pricing",
        action="Provide premium pricing",
        priority=1,
    )
    guideline_b = await guideline_store.create_guideline(
        condition="Customer asks about pricing",
        action="Provide standard pricing",
        priority=0,
    )

    result = await resolver.resolve(
        [guideline_a, guideline_b],
        [
            GuidelineMatch(guideline=guideline_a, score=8, rationale=""),
            GuidelineMatch(guideline=guideline_b, score=9, rationale=""),
        ],
        journeys=[],
    )

    assert len(result.matches) == 1
    assert result.matches[0].guideline.id == guideline_a.id


async def test_that_relational_resolver_filters_journeys_by_priority_keeping_only_highest(
    container: Container,
) -> None:
    """
    Tests that after all relational resolution, only journeys sharing the
    highest priority value (and their guidelines) survive.

    - Journey 1 has priority=2
    - Journey 2 has priority=0 (default)
    - Both journeys' guidelines are active matches
    - Expected: Only Journey 1's guidelines survive
    """
    guideline_store = container[GuidelineStore]
    journey_store = container[JourneyStore]
    projection = container[JourneyGuidelineProjection]
    resolver = container[RelationalResolver]

    j1_condition = await guideline_store.create_guideline(
        condition="Customer is interested in Journey 1"
    )
    j2_condition = await guideline_store.create_guideline(
        condition="Customer is interested in Journey 2"
    )

    j1 = await journey_store.create_journey(
        title="Journey 1",
        description="High priority journey",
        conditions=[j1_condition.id],
        priority=2,
    )

    j2 = await journey_store.create_journey(
        title="Journey 2",
        description="Default priority journey",
        conditions=[j2_condition.id],
        priority=0,
    )

    j1_guidelines = await projection.project_journey_to_guidelines(j1.id)
    j2_guidelines = await projection.project_journey_to_guidelines(j2.id)

    assert len(j1_guidelines) == 1
    assert len(j2_guidelines) == 1

    result = await resolver.resolve(
        list(j1_guidelines) + list(j2_guidelines),
        [
            GuidelineMatch(guideline=j1_guidelines[0], score=8, rationale=""),
            GuidelineMatch(guideline=j2_guidelines[0], score=9, rationale=""),
        ],
        journeys=[j1, j2],
    )

    assert len(result.matches) == 1
    assert result.matches[0].guideline.id == j1_guidelines[0].id
    assert len(result.journeys) == 1
    assert result.journeys[0].id == j1.id


async def test_that_relational_resolver_filters_mixed_entities_by_priority_with_prioritized_guideline_to_keep_only_the_guideline(
    container: Container,
) -> None:
    """
    Tests cross-entity priority comparison between standalone guidelines and journeys.

    - Standalone guideline has priority=1
    - Journey has priority=0 (default)
    - Both are active
    - Expected: Only the standalone guideline survives; the journey and its
      guidelines are filtered out because priority=0 < priority=1
    """
    guideline_store = container[GuidelineStore]
    journey_store = container[JourneyStore]
    projection = container[JourneyGuidelineProjection]
    resolver = container[RelationalResolver]

    standalone_guideline = await guideline_store.create_guideline(
        condition="Customer asks about drinks",
        action="Recommend water",
        priority=1,
    )

    journey_condition = await guideline_store.create_guideline(
        condition="Customer asks about drinks"
    )

    journey = await journey_store.create_journey(
        title="Drink Recommendation Journey",
        description="Recommend soda",
        conditions=[journey_condition.id],
        priority=0,
    )

    journey_guidelines = await projection.project_journey_to_guidelines(journey.id)
    assert len(journey_guidelines) > 0

    journey_matches = [
        GuidelineMatch(guideline=g, score=7 + i, rationale="")
        for i, g in enumerate(journey_guidelines)
    ]

    result = await resolver.resolve(
        [standalone_guideline] + list(journey_guidelines),
        [GuidelineMatch(guideline=standalone_guideline, score=8, rationale="")] + journey_matches,
        journeys=[journey],
    )

    assert len(result.matches) == 1
    assert result.matches[0].guideline.id == standalone_guideline.id
    assert len(result.journeys) == 0


async def test_that_relational_resolver_filters_mixed_entities_by_priority_with_prioritized_journey_to_keep_only_the_journey(
    container: Container,
) -> None:
    """
    Tests cross-entity priority comparison where the journey has higher priority.

    - Standalone guideline has priority=0 (default)
    - Journey has priority=1
    - Both are active
    - Expected: Only the journey and its guidelines survive; the standalone
      guideline is filtered out because priority=0 < priority=1
    """
    guideline_store = container[GuidelineStore]
    journey_store = container[JourneyStore]
    projection = container[JourneyGuidelineProjection]
    resolver = container[RelationalResolver]

    standalone_guideline = await guideline_store.create_guideline(
        condition="Customer asks about drinks",
        action="Recommend water",
        priority=0,
    )

    journey_condition = await guideline_store.create_guideline(
        condition="Customer asks about drinks"
    )

    journey = await journey_store.create_journey(
        title="Drink Recommendation Journey",
        description="Recommend soda",
        conditions=[journey_condition.id],
        priority=1,
    )

    journey_guidelines = await projection.project_journey_to_guidelines(journey.id)
    assert len(journey_guidelines) > 0

    journey_matches = [
        GuidelineMatch(guideline=g, score=7 + i, rationale="")
        for i, g in enumerate(journey_guidelines)
    ]

    result = await resolver.resolve(
        [standalone_guideline] + list(journey_guidelines),
        [GuidelineMatch(guideline=standalone_guideline, score=10, rationale="")] + journey_matches,
        journeys=[journey],
    )

    assert all(m.guideline.id != standalone_guideline.id for m in result.matches)
    assert len(result.matches) == len(journey_guidelines)
    assert len(result.journeys) == 1
    assert result.journeys[0].id == journey.id


async def test_that_relational_resolver_deprioritizes_target_guideline_when_source_is_custom_tag(
    container: Container,
) -> None:
    """
    Tests that a custom tag used as source in a PRIORITY relationship
    deprioritizes the target guideline when a guideline tagged with that
    tag is matched.

    - Tag t1 is attached to g1
    - t1 PRIORITY → g2
    - Both g1 and g2 are matched
    - Expected: g2 is deprioritized, only g1 remains
    """
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    tag_store = container[TagStore]
    resolver = container[RelationalResolver]

    g1 = await guideline_store.create_guideline(condition="a", action="b")
    g2 = await guideline_store.create_guideline(condition="c", action="d")

    t1 = await tag_store.create_tag(name="t1")
    await guideline_store.upsert_tag(g1.id, t1.id)
    g1 = await guideline_store.read_guideline(g1.id)

    await relationship_store.create_relationship(
        source=RelationshipEntity(id=t1.id, kind=RelationshipEntityKind.TAG),
        target=RelationshipEntity(id=g2.id, kind=RelationshipEntityKind.GUIDELINE),
        kind=RelationshipKind.PRIORITY,
    )

    result = await resolver.resolve(
        [g1, g2],
        [
            GuidelineMatch(guideline=g1, score=8, rationale=""),
            GuidelineMatch(guideline=g2, score=5, rationale=""),
        ],
        journeys=[],
    )

    assert len(result.matches) == 1
    assert result.matches[0].guideline.id == g1.id


async def test_that_relational_resolver_filters_tagged_guideline_when_custom_tag_dependency_is_unmet(
    container: Container,
) -> None:
    """
    Tests that a custom tag used as source in a DEPENDENCY relationship
    deactivates the tagged guideline when the dependency target is not matched.

    - Tag t1 is attached to g1
    - t1 DEPENDENCY → g2  (g1, via t1, depends on g2)
    - g1 is matched but g2 is NOT matched
    - Expected: g1 is filtered out (unmet dependency via tag)
    """
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    tag_store = container[TagStore]
    resolver = container[RelationalResolver]

    g1 = await guideline_store.create_guideline(condition="a", action="b")
    g2 = await guideline_store.create_guideline(condition="c", action="d")

    t1 = await tag_store.create_tag(name="t1")
    await guideline_store.upsert_tag(g1.id, t1.id)
    g1 = await guideline_store.read_guideline(g1.id)

    await relationship_store.create_relationship(
        source=RelationshipEntity(id=t1.id, kind=RelationshipEntityKind.TAG),
        target=RelationshipEntity(id=g2.id, kind=RelationshipEntityKind.GUIDELINE),
        kind=RelationshipKind.DEPENDENCY,
    )

    result = await resolver.resolve(
        [g1, g2],
        [
            GuidelineMatch(guideline=g1, score=8, rationale=""),
            # g2 is NOT matched — dependency unmet
        ],
        journeys=[],
    )

    assert result.matches == []


async def test_that_relational_resolver_transitively_filters_guideline_depending_on_custom_tag_with_deprioritized_member(
    container: Container,
) -> None:
    """
    Tests the transitive effect of priority + dependency via a custom tag:
    - g1 prioritizes over g2
    - g2 is tagged with t1
    - g3 depends on tag t1
    - When all three are matched, g2 is deprioritized by g1,
      then g3 is transitively filtered (t1 member g2 was deprioritized).
      Only g1 remains.
    """
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    tag_store = container[TagStore]
    resolver = container[RelationalResolver]

    g1 = await guideline_store.create_guideline(condition="a", action="Recommend Pepsi")
    g2 = await guideline_store.create_guideline(condition="b", action="Recommend Coke")
    g3 = await guideline_store.create_guideline(condition="c", action="Recommend Sprite")

    t1 = await tag_store.create_tag(name="drink-group")
    await guideline_store.upsert_tag(g2.id, t1.id)
    g2 = await guideline_store.read_guideline(g2.id)

    # g1 prioritizes over g2 (g2 gets deprioritized)
    await relationship_store.create_relationship(
        source=RelationshipEntity(id=g1.id, kind=RelationshipEntityKind.GUIDELINE),
        target=RelationshipEntity(id=g2.id, kind=RelationshipEntityKind.GUIDELINE),
        kind=RelationshipKind.PRIORITY,
    )

    # g3 depends on tag t1 (i.e. all guidelines tagged with t1 being active)
    await relationship_store.create_relationship(
        source=RelationshipEntity(id=g3.id, kind=RelationshipEntityKind.GUIDELINE),
        target=RelationshipEntity(id=t1.id, kind=RelationshipEntityKind.TAG),
        kind=RelationshipKind.DEPENDENCY,
    )

    result = await resolver.resolve(
        [g1, g2, g3],
        [
            GuidelineMatch(guideline=g1, score=9, rationale=""),
            GuidelineMatch(guideline=g2, score=7, rationale=""),
            GuidelineMatch(guideline=g3, score=6, rationale=""),
        ],
        journeys=[],
    )

    # Only g1 should remain:
    # - g2 is deprioritized by g1
    # - g3 depends on tag t1, whose member g2 was deprioritized, so g3 is filtered
    assert result.matches == [GuidelineMatch(guideline=g1, score=9, rationale="")]


async def test_that_tag_priority_excludes_all_target_members_regardless_of_individual_priority(
    container: Container,
) -> None:
    """
    Tests that tag-level prioritization is absolute — individual-level priority
    relationships do NOT grant immunity from tag-level deprioritization:
    - t1 prioritizes over t2 (tag-level: all of t1 beats all of t2)
    - g2_1 prioritizes over g1_1 (guideline-level)
    - After resolution: g1_1 deprioritized by g2_1 (guideline-level),
      g2_1 and g2_2 deprioritized by t1 (tag-level). Only g1_2 survives.
    """
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    tag_store = container[TagStore]
    resolver = container[RelationalResolver]

    t1 = await tag_store.create_tag(name="t1")
    t2 = await tag_store.create_tag(name="t2")

    g1_1 = await guideline_store.create_guideline(condition="a", action="g1_1 action")
    g1_2 = await guideline_store.create_guideline(condition="b", action="g1_2 action")
    g2_1 = await guideline_store.create_guideline(condition="c", action="g2_1 action")
    g2_2 = await guideline_store.create_guideline(condition="d", action="g2_2 action")

    await guideline_store.upsert_tag(g1_1.id, t1.id)
    await guideline_store.upsert_tag(g1_2.id, t1.id)
    await guideline_store.upsert_tag(g2_1.id, t2.id)
    await guideline_store.upsert_tag(g2_2.id, t2.id)

    g1_1 = await guideline_store.read_guideline(g1_1.id)
    g1_2 = await guideline_store.read_guideline(g1_2.id)
    g2_1 = await guideline_store.read_guideline(g2_1.id)
    g2_2 = await guideline_store.read_guideline(g2_2.id)

    # t1 prioritizes over t2 (tag-level)
    await relationship_store.create_relationship(
        source=RelationshipEntity(id=t1.id, kind=RelationshipEntityKind.TAG),
        target=RelationshipEntity(id=t2.id, kind=RelationshipEntityKind.TAG),
        kind=RelationshipKind.PRIORITY,
    )

    # g2_1 prioritizes over g1_1 (guideline-level — does NOT grant immunity from tag-level)
    await relationship_store.create_relationship(
        source=RelationshipEntity(id=g2_1.id, kind=RelationshipEntityKind.GUIDELINE),
        target=RelationshipEntity(id=g1_1.id, kind=RelationshipEntityKind.GUIDELINE),
        kind=RelationshipKind.PRIORITY,
    )

    result = await resolver.resolve(
        [g1_1, g1_2, g2_1, g2_2],
        [
            GuidelineMatch(guideline=g1_1, score=10, rationale=""),
            GuidelineMatch(guideline=g1_2, score=10, rationale=""),
            GuidelineMatch(guideline=g2_1, score=10, rationale=""),
            GuidelineMatch(guideline=g2_2, score=10, rationale=""),
        ],
        journeys=[],
    )

    # g1_1 deprioritized by g2_1, then g2_1 and g2_2 deprioritized by t1→t2.
    # Only g1_2 survives.
    result_ids = {m.guideline.id for m in result.matches}
    assert result_ids == {g1_2.id}


async def test_that_tag_priority_deprioritizes_all_guidelines_of_target_tag(
    container: Container,
) -> None:
    """
    Tests that tag-level prioritization filters out all guidelines of the target tag:
    - t1 prioritizes over t2
    - g1_1, g1_2 tagged with t1; g2_1, g2_2 tagged with t2
    - After resolution only g1_1 and g1_2 remain (t2 guidelines are deprioritized).
    """
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    tag_store = container[TagStore]
    resolver = container[RelationalResolver]

    t1 = await tag_store.create_tag(name="t1")
    t2 = await tag_store.create_tag(name="t2")

    g1_1 = await guideline_store.create_guideline(condition="a", action="g1_1 action")
    g1_2 = await guideline_store.create_guideline(condition="b", action="g1_2 action")
    g2_1 = await guideline_store.create_guideline(condition="c", action="g2_1 action")
    g2_2 = await guideline_store.create_guideline(condition="d", action="g2_2 action")

    await guideline_store.upsert_tag(g1_1.id, t1.id)
    await guideline_store.upsert_tag(g1_2.id, t1.id)
    await guideline_store.upsert_tag(g2_1.id, t2.id)
    await guideline_store.upsert_tag(g2_2.id, t2.id)

    g1_1 = await guideline_store.read_guideline(g1_1.id)
    g1_2 = await guideline_store.read_guideline(g1_2.id)
    g2_1 = await guideline_store.read_guideline(g2_1.id)
    g2_2 = await guideline_store.read_guideline(g2_2.id)

    # t1 prioritizes over t2
    await relationship_store.create_relationship(
        source=RelationshipEntity(id=t1.id, kind=RelationshipEntityKind.TAG),
        target=RelationshipEntity(id=t2.id, kind=RelationshipEntityKind.TAG),
        kind=RelationshipKind.PRIORITY,
    )

    result = await resolver.resolve(
        [g1_1, g1_2, g2_1, g2_2],
        [
            GuidelineMatch(guideline=g1_1, score=10, rationale=""),
            GuidelineMatch(guideline=g1_2, score=10, rationale=""),
            GuidelineMatch(guideline=g2_1, score=10, rationale=""),
            GuidelineMatch(guideline=g2_2, score=10, rationale=""),
        ],
        journeys=[],
    )

    result_ids = {m.guideline.id for m in result.matches}
    assert result_ids == {g1_1.id, g1_2.id}


async def test_that_journey_priority_deprioritizes_all_guidelines_of_target_tag(
    container: Container,
) -> None:
    """
    Tests that a journey prioritizing over a custom tag filters out all
    guidelines tagged with that tag:
    - Journey J (with j_cond) prioritizes over t1
    - g1, g2 tagged with t1
    - After resolution only j_cond remains (t1 guidelines are deprioritized).
    """
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    tag_store = container[TagStore]
    journey_store = container[JourneyStore]
    resolver = container[RelationalResolver]

    t1 = await tag_store.create_tag(name="t1")

    g1 = await guideline_store.create_guideline(condition="a", action="g1 action")
    g2 = await guideline_store.create_guideline(condition="b", action="g2 action")

    await guideline_store.upsert_tag(g1.id, t1.id)
    await guideline_store.upsert_tag(g2.id, t1.id)
    g1 = await guideline_store.read_guideline(g1.id)
    g2 = await guideline_store.read_guideline(g2.id)

    j_cond = await guideline_store.create_guideline(condition="c", action="journey action")
    journey = await journey_store.create_journey(
        title="J",
        description="A journey",
        conditions=[j_cond.id],
    )

    # Tag condition guideline with its journey tag (as the real projection does)
    await guideline_store.upsert_tag(j_cond.id, Tag.for_journey_id(journey.id))
    j_cond = await guideline_store.read_guideline(j_cond.id)

    # Journey J prioritizes over t1
    await relationship_store.create_relationship(
        source=RelationshipEntity(
            id=Tag.for_journey_id(journey.id), kind=RelationshipEntityKind.TAG
        ),
        target=RelationshipEntity(id=t1.id, kind=RelationshipEntityKind.TAG),
        kind=RelationshipKind.PRIORITY,
    )

    result = await resolver.resolve(
        [g1, g2, j_cond],
        [
            GuidelineMatch(guideline=g1, score=10, rationale=""),
            GuidelineMatch(guideline=g2, score=10, rationale=""),
            GuidelineMatch(guideline=j_cond, score=10, rationale=""),
        ],
        journeys=[journey],
    )

    result_ids = {m.guideline.id for m in result.matches}
    assert result_ids == {j_cond.id}


async def test_that_journey_priority_deprioritizes_target_journey(
    container: Container,
) -> None:
    """
    Tests that a journey prioritizing over another journey filters out the
    target journey's node guidelines:
    - Journey J1 prioritizes over Journey J2
    - j1_g and j2_g are node guidelines (with journey_node metadata)
    - After resolution only j1_g remains (j2_g is deprioritized).
    """
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    journey_store = container[JourneyStore]
    resolver = container[RelationalResolver]

    j1 = await journey_store.create_journey(title="J1", description="Journey 1", conditions=[])
    j2 = await journey_store.create_journey(title="J2", description="Journey 2", conditions=[])

    j1_g = await guideline_store.create_guideline(
        condition="a",
        action="j1 action",
        metadata={"journey_node": {"journey_id": j1.id}},
    )
    j2_g = await guideline_store.create_guideline(
        condition="b",
        action="j2 action",
        metadata={"journey_node": {"journey_id": j2.id}},
    )

    # J1 prioritizes over J2
    await relationship_store.create_relationship(
        source=RelationshipEntity(id=Tag.for_journey_id(j1.id), kind=RelationshipEntityKind.TAG),
        target=RelationshipEntity(id=Tag.for_journey_id(j2.id), kind=RelationshipEntityKind.TAG),
        kind=RelationshipKind.PRIORITY,
    )

    result = await resolver.resolve(
        [j1_g, j2_g],
        [
            GuidelineMatch(guideline=j1_g, score=10, rationale=""),
            GuidelineMatch(guideline=j2_g, score=10, rationale=""),
        ],
        journeys=[j1, j2],
    )

    result_ids = {m.guideline.id for m in result.matches}
    assert result_ids == {j1_g.id}


async def test_that_tag_priority_deprioritizes_target_journey(
    container: Container,
) -> None:
    """
    Tests that a custom tag prioritizing over a journey filters out the
    journey's node guidelines:
    - t1 (with g1, g2) prioritizes over Journey J (with j_g node guideline)
    - After resolution g1 and g2 remain, j_g is deprioritized.
    """
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    tag_store = container[TagStore]
    journey_store = container[JourneyStore]
    resolver = container[RelationalResolver]

    t1 = await tag_store.create_tag(name="t1")

    g1 = await guideline_store.create_guideline(condition="a", action="g1 action")
    g2 = await guideline_store.create_guideline(condition="b", action="g2 action")

    await guideline_store.upsert_tag(g1.id, t1.id)
    await guideline_store.upsert_tag(g2.id, t1.id)
    g1 = await guideline_store.read_guideline(g1.id)
    g2 = await guideline_store.read_guideline(g2.id)

    journey = await journey_store.create_journey(
        title="J",
        description="A journey",
        conditions=[],
    )

    j_g = await guideline_store.create_guideline(
        condition="c",
        action="journey action",
        metadata={"journey_node": {"journey_id": journey.id}},
    )

    # t1 prioritizes over Journey J
    await relationship_store.create_relationship(
        source=RelationshipEntity(id=t1.id, kind=RelationshipEntityKind.TAG),
        target=RelationshipEntity(
            id=Tag.for_journey_id(journey.id), kind=RelationshipEntityKind.TAG
        ),
        kind=RelationshipKind.PRIORITY,
    )

    result = await resolver.resolve(
        [g1, g2, j_g],
        [
            GuidelineMatch(guideline=g1, score=10, rationale=""),
            GuidelineMatch(guideline=g2, score=10, rationale=""),
            GuidelineMatch(guideline=j_g, score=10, rationale=""),
        ],
        journeys=[journey],
    )

    result_ids = {m.guideline.id for m in result.matches}
    assert result_ids == {g1.id, g2.id}


# ── Tag-level dependency tests ──────────────────────────────────────────────


async def test_that_tag_dependency_deactivates_tagged_guidelines_when_target_guideline_not_met(
    container: Container,
) -> None:
    """
    t1 depends on g2. g1 tagged t1, g2 untagged, g3 untagged.
    g2 NOT matched → t1 dependency unmet → g1 deactivated.
    Result: {g3}
    """
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    tag_store = container[TagStore]
    resolver = container[RelationalResolver]

    t1 = await tag_store.create_tag(name="t1")

    g1 = await guideline_store.create_guideline(condition="a", action="g1 action", tags=[t1.id])
    g2 = await guideline_store.create_guideline(condition="b", action="g2 action")
    g3 = await guideline_store.create_guideline(condition="c", action="g3 action")

    # t1 depends on g2
    await relationship_store.create_relationship(
        source=RelationshipEntity(id=t1.id, kind=RelationshipEntityKind.TAG),
        target=RelationshipEntity(id=g2.id, kind=RelationshipEntityKind.GUIDELINE),
        kind=RelationshipKind.DEPENDENCY,
    )

    result = await resolver.resolve(
        [g1, g2, g3],
        [
            GuidelineMatch(guideline=g1, score=10, rationale=""),
            # g2 NOT matched
            GuidelineMatch(guideline=g3, score=10, rationale=""),
        ],
        journeys=[],
    )

    result_ids = {m.guideline.id for m in result.matches}
    assert result_ids == {g3.id}


async def test_that_tag_dependency_deactivates_tagged_guidelines_when_target_tag_not_met(
    container: Container,
) -> None:
    """
    t1 depends on t2. g1 tagged t1, g2 tagged t2, g3 untagged.
    g2 is NOT matched → t2 dependency unmet → g1 deactivated.
    Result: {g3}
    """
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    tag_store = container[TagStore]
    resolver = container[RelationalResolver]

    t1 = await tag_store.create_tag(name="t1")
    t2 = await tag_store.create_tag(name="t2")

    g1 = await guideline_store.create_guideline(condition="a", action="g1 action", tags=[t1.id])
    g2 = await guideline_store.create_guideline(condition="b", action="g2 action", tags=[t2.id])
    g3 = await guideline_store.create_guideline(condition="c", action="g3 action")

    # t1 depends on t2
    await relationship_store.create_relationship(
        source=RelationshipEntity(id=t1.id, kind=RelationshipEntityKind.TAG),
        target=RelationshipEntity(id=t2.id, kind=RelationshipEntityKind.TAG),
        kind=RelationshipKind.DEPENDENCY,
    )

    result = await resolver.resolve(
        [g1, g2, g3],
        [
            GuidelineMatch(guideline=g1, score=10, rationale=""),
            # g2 NOT matched
            GuidelineMatch(guideline=g3, score=10, rationale=""),
        ],
        journeys=[],
    )

    result_ids = {m.guideline.id for m in result.matches}
    assert result_ids == {g3.id}


async def test_that_journey_dependency_deactivates_node_guidelines_when_target_tag_not_met(
    container: Container,
) -> None:
    """
    Journey j1 depends on t1. j1_g is a j1 node guideline, g1 tagged t1, g_extra untagged.
    g1 NOT matched → t1 dependency unmet → j1_g deactivated.
    Result: {g_extra}
    """
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    tag_store = container[TagStore]
    journey_store = container[JourneyStore]
    resolver = container[RelationalResolver]

    t1 = await tag_store.create_tag(name="t1")

    g1 = await guideline_store.create_guideline(condition="a", action="g1 action", tags=[t1.id])

    j1 = await journey_store.create_journey(title="J1", description="Journey 1", conditions=[])
    j1_g = await guideline_store.create_guideline(
        condition="b",
        action="j1 action",
        metadata={"journey_node": {"journey_id": j1.id}},
    )

    g_extra = await guideline_store.create_guideline(condition="c", action="extra action")

    # j1 depends on t1
    await relationship_store.create_relationship(
        source=RelationshipEntity(id=Tag.for_journey_id(j1.id), kind=RelationshipEntityKind.TAG),
        target=RelationshipEntity(id=t1.id, kind=RelationshipEntityKind.TAG),
        kind=RelationshipKind.DEPENDENCY,
    )

    result = await resolver.resolve(
        [g1, j1_g, g_extra],
        [
            # g1 NOT matched
            GuidelineMatch(guideline=j1_g, score=10, rationale=""),
            GuidelineMatch(guideline=g_extra, score=10, rationale=""),
        ],
        journeys=[j1],
    )

    result_ids = {m.guideline.id for m in result.matches}
    assert result_ids == {g_extra.id}


async def test_that_tag_dependency_deactivates_tagged_guidelines_when_target_journey_not_active(
    container: Container,
) -> None:
    """
    t1 depends on journey j1. g1 tagged t1, g_extra untagged.
    j1 NOT in active journeys → t1 dependency unmet → g1 deactivated.
    Result: {g_extra}
    """
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    tag_store = container[TagStore]
    journey_store = container[JourneyStore]
    resolver = container[RelationalResolver]

    t1 = await tag_store.create_tag(name="t1")

    g1 = await guideline_store.create_guideline(condition="a", action="g1 action", tags=[t1.id])
    g_extra = await guideline_store.create_guideline(condition="b", action="extra action")

    j1 = await journey_store.create_journey(title="J1", description="Journey 1", conditions=[])

    # t1 depends on j1
    await relationship_store.create_relationship(
        source=RelationshipEntity(id=t1.id, kind=RelationshipEntityKind.TAG),
        target=RelationshipEntity(id=Tag.for_journey_id(j1.id), kind=RelationshipEntityKind.TAG),
        kind=RelationshipKind.DEPENDENCY,
    )

    result = await resolver.resolve(
        [g1, g_extra],
        [
            GuidelineMatch(guideline=g1, score=10, rationale=""),
            GuidelineMatch(guideline=g_extra, score=10, rationale=""),
        ],
        journeys=[],  # j1 NOT active
    )

    result_ids = {m.guideline.id for m in result.matches}
    assert result_ids == {g_extra.id}


async def test_that_journey_dependency_deactivates_node_guidelines_when_target_journey_not_active(
    container: Container,
) -> None:
    """
    Journey j1 depends on journey j2. j1_g is a j1 node guideline, g_extra untagged.
    j2 NOT in active journeys → j1 dependency unmet → j1_g deactivated.
    Result: {g_extra}
    """
    relationship_store = container[RelationshipStore]
    guideline_store = container[GuidelineStore]
    journey_store = container[JourneyStore]
    resolver = container[RelationalResolver]

    j1 = await journey_store.create_journey(title="J1", description="Journey 1", conditions=[])
    j2 = await journey_store.create_journey(title="J2", description="Journey 2", conditions=[])

    j1_g = await guideline_store.create_guideline(
        condition="a",
        action="j1 action",
        metadata={"journey_node": {"journey_id": j1.id}},
    )

    g_extra = await guideline_store.create_guideline(condition="b", action="extra action")

    # j1 depends on j2
    await relationship_store.create_relationship(
        source=RelationshipEntity(id=Tag.for_journey_id(j1.id), kind=RelationshipEntityKind.TAG),
        target=RelationshipEntity(id=Tag.for_journey_id(j2.id), kind=RelationshipEntityKind.TAG),
        kind=RelationshipKind.DEPENDENCY,
    )

    result = await resolver.resolve(
        [j1_g, g_extra],
        [
            GuidelineMatch(guideline=j1_g, score=10, rationale=""),
            GuidelineMatch(guideline=g_extra, score=10, rationale=""),
        ],
        journeys=[j1],  # j2 NOT active
    )

    result_ids = {m.guideline.id for m in result.matches}
    assert result_ids == {g_extra.id}
