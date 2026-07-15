# Changelog

All notable changes to the Solar System Balance Protocol are documented in this file.

The format is based on Keep a Changelog.

The project uses candidate versions while the first protocol arc is being reviewed and stabilized.

## [Unreleased]

### Planned

* cross-record referential validation
* reusable schema definitions
* multi-record scenario examples
* machine-generated balance reports
* formal orbital transition records
* policy simulation support
* lifecycle conformance profiles
* interoperability mappings
* first stable `v1.0.0` review

---

## [0.5.0-candidate] - 2026-07-15

### Added

* Life-Cycle Balance Loop JSON Schema
* complete stagnation-recovery lifecycle example
* five mandatory lifecycle phases:

  * expansion
  * exploration
  * consolidation
  * restoration
  * re-expansion
* explicit phase sequence numbering
* phase status tracking
* phase entry conditions
* phase exit conditions
* bounded phase actions
* phase output references
* measurable phase metrics
* evidence-linked phase evaluation
* chronological transition records
* transition conditions
* next-cycle transition binding
* lifecycle duration budget
* per-phase duration budgets
* minimum restoration duration
* distributed autonomy floor
* maximum core-pressure limit
* loop closure record
* preserved-route declarations
* retired-route declarations
* unresolved-risk declarations
* next-cycle authorization
* next-cycle seed references
* cycle lineage identifiers
* No Skipped Restoration safeguard
* No Permanent Expansion safeguard
* No Permanent Consolidation safeguard
* lifecycle Trace continuity requirement

### Validation

Added semantic validation for:

* exact lifecycle phase order
* exact sequence numbering
* duplicate phase detection
* active phase and loop-state consistency
* phase timestamp requirements
* phase chronology
* phase-duration limits
* completed-phase output requirements
* duplicate phase metric identifiers
* calculated phase metric results
* evidence requirements for phase metrics
* mandatory restoration
* minimum restoration duration
* total cycle-duration limit
* lifecycle transition order
* transition-count consistency
* transition timestamp chronology
* completed transition conditions
* transition evidence continuity
* final next-cycle transition binding
* completed-loop phase completion
* completed-loop closure state
* completed-loop next-cycle authorization
* required next-cycle seed references
* unresolved-risk and success-state consistency
* preserved-route and retired-route overlap
* lifecycle human-review consistency
* completed-loop approval
* expansion termination before closure
* consolidation termination before closure
* self-referencing previous and next cycle identifiers

### Design principles

* A breathing response is incomplete until restoration has occurred.
* Restoration is a mandatory lifecycle phase.
* Expansion must not become a permanent topology.
* Consolidation must not become permanent centralized control.
* A completed cycle must pass a bounded, traceable seed into the next cycle.
* Temporary exploration structures must not be inherited as permanent authority.
* The lifecycle must preserve discoveries without preserving capture.

---

## [0.4.0-candidate] - 2026-07-15

### Added

* Breathing Trigger Policy JSON Schema
* stagnation-trigger example
* seven trigger types:

  * load
  * risk
  * innovation
  * crisis
  * stagnation
  * manual
  * other
* measurable trigger metrics
* trigger comparison operators:

  * greater than
  * greater than or equal
  * less than
  * less than or equal
  * equal
  * not equal
* `all` and `any` condition modes
* observation windows
* minimum occurrence requirements
* evidence-before-activation policy
* matched metric recording
* current-state references
* cooldown detection
* activation decisions
* hold decisions
* escalation decisions
* rejection decisions
* six response modes:

  * selective expansion
  * selective contraction
  * system expansion
  * system contraction
  * rebalance
  * hold
* gravity-axis adjustment plans
* maximum gravity-delta boundaries
* outer-orbit activation
* contrarian-node activation
* comet-node activation
* dormant-node activation
* inward orbital movement
* outward orbital movement
* synchronization adjustment
* route diversification
* route restriction
* temporary node isolation
* previous-orbit restoration
* tidal-action preparation
* lifecycle phase hints
* activation delays
* maximum response duration
* response decay modes
* distributed autonomy safeguards
* crisis expiry requirement
* stagnation diversity requirement
* blocked-action declarations
* mandatory rollback policy
* rollback target core state
* measurable rollback conditions
* rollback actions
* maximum response-retention period
* rollback status
* No Permanent Breathing Capture principle

### Validation

Added semantic validation for:

* duplicate trigger metric identifiers
* metric comparison evaluation
* calculated trigger-condition results
* declared trigger-condition results
* matched metric accuracy
* required evidence references
* activation during cooldown
* gravity deltas exceeding policy limits
* invalid hold responses
* target-scope and target-node consistency
* local-cluster targeting consistency
* orbital movement target requirements
* invalid same-orbit movement
* tidal interaction-family consistency
* tidal source and target overlap
* manual-trigger reason requirements
* risk-trigger audit adjustment
* crisis human-review requirements
* crisis expiry requirements
* crisis emergency-authority adjustment
* innovation lifecycle direction
* stagnation diversity requirements
* stagnation gravity release
* review-status consistency
* rollback completeness
* rollback retention coverage
* trace coverage for current core states
* trace coverage for current orbital definitions
* trace coverage for current tidal interactions
* policy evaluation chronology

### Design principles

* A living balance system must know when and how to breathe.
* Structural changes must be triggered by measurable conditions.
* Only necessary gravity axes should be adjusted.
* Risk may strengthen audit without eliminating distributed creativity.
* Crisis coordination must remain temporary.
* Stagnation is a structural risk.
* Stagnation should activate diversity rather than strengthen dominance.
* Every breathing response must define a return path.
* Temporary breathing must never become permanent topology.

---

## [0.3.0-candidate] - 2026-07-15

### Added

* Tidal Interaction Record JSON Schema
* local analyst-conflict example
* source node references
* target node references
* mediator node references
* interaction directionality
* interaction intensity
* core-mediation status
* local-resolution status
* interaction start and end timestamps
* interaction status
* attractive interaction family:

  * resonance
  * resource pull
  * synchronization
* repulsive interaction family:

  * conflict
  * repulsion
* exchange interaction family:

  * evidence exchange
  * trace handoff
* evidence references
* Trace references
* resource references
* synchronization scope
* resource requests
* route effects:

  * none
  * prefer
  * divert
  * isolate
* source autonomy delta
* target autonomy delta
* peer-binding delta
* gravity-axis adjustments
* orbital-change requests
* peer-to-peer resolution
* local-cluster resolution
* core-mediated resolution
* human-gate resolution
* unresolved status
* escalation targets
* interaction expiry
* bounded-effect safeguard
* maximum interaction intensity
* No Silent Override safeguard
* No Permanent Tidal Capture safeguard
* interaction consent model
* interaction consent status
* high-intensity human-review threshold

### Validation

Added semantic validation for:

* duplicate source and target nodes
* duplicate mediator nodes
* mediator overlap with primary participants
* interaction type and family consistency
* maximum interaction-intensity enforcement
* interaction chronology
* required end time for completed or expired interactions
* evidence requirements for conflict and repulsion
* audit requirements for conflict and repulsion
* Trace requirements for trace handoff
* evidence requirements for evidence exchange
* resource requirements for resource pull
* synchronization-scope requirements
* human review for high-intensity interactions
* human-review status consistency
* consent-model consistency
* rejected-consent completion prevention
* core-mediation consistency
* local-resolution consistency
* orbit-change target requirements
* orbit-change reason requirements
* orbit-change return conditions
* invalid same-orbit transition requests
* route-diversion return conditions
* route-isolation return conditions
* route-effect expiry requirements
* participant orbital-definition Trace coverage

### Design principles

* Horizontal interaction is a first-class balancing mechanism.
* The core is not the only source of order.
* Repulsion is a normal balancing force rather than an automatic failure.
* Safe conflicts should be resolved locally before core escalation.
* Tidal effects must remain bounded, traceable, and reversible.
* Temporary interaction must not become permanent orbital capture.

---

## [0.2.0-candidate] - 2026-07-15

### Added

* Orbital Node Definition JSON Schema
* Comet Orbit long-term memory example
* supported node types:

  * Agent
  * Wing
  * service
  * cluster
  * replica
  * memory node
  * human gate
  * other
* five orbital classes:

  * inner
  * middle
  * outer
  * comet
  * dormant
* structural distance from the core
* core-binding strength
* node autonomy level
* interaction frequency
* orbital phase
* node operational state
* capability declarations
* ownership boundaries
* core-bound functions
* locally governed functions
* prohibited core overrides
* audit-visibility modes
* routing-authority modes
* peer-interaction strength
* local-cluster binding
* allowed tidal-interaction types
* preferred handoff targets
* core-resource dependency
* local-resource capacity
* fallback resource sources
* orbital transition policy
* permitted target orbits
* approach triggers
* departure triggers
* return conditions
* maximum inner-orbit duration
* orbital cooldown period
* Comet Orbit activation profile
* Dormant Orbit wake profile

### Validation

Added semantic validation for:

* overlap between core-bound and locally governed functions
* invalid current-orbit transition targets
* interaction mode and interval consistency
* Inner Orbit distance limits
* Inner Orbit binding requirements
* Middle Orbit distance range
* Outer Orbit distance requirements
* Outer Orbit autonomy requirements
* Comet Orbit event-driven interaction
* Comet Orbit activation profile
* Comet Orbit active-window requirements
* Comet Orbit inward approach path
* Comet Orbit departure triggers
* Comet Orbit return conditions
* Dormant Orbit operational-state restrictions
* Dormant Orbit interaction restrictions
* Dormant Orbit hibernation requirement
* Dormant Orbit peer-interaction limit
* Dormant Orbit wake profile
* transition-enabled node requirements
* transition-disabled node restrictions

### Design principles

* Orbit represents structural relationship rather than hierarchy.
* Distance represents governance and dependency distance rather than only physical distance.
* Binding and autonomy are independent values.
* A node may retain strong audit binding and high domain autonomy simultaneously.
* Comet Agents must return after completing temporary missions.
* Dormant nodes remain available without consuming continuous coordination.
* The core must not silently override declared local boundaries.

---

## [0.1.0-candidate] - 2026-07-15

### Added

* initial repository structure
* Solar Core State Record JSON Schema
* Solar Core State YAML example
* multidimensional solar-gravity axes:

  * coordination strength
  * audit strength
  * routing strength
  * resource control
  * emergency authority
* solar core modes:

  * near distributed
  * weak coordination
  * balanced
  * strong coordination
  * emergency
* weighted aggregate breathing index
* aggregate weighting model
* distributed autonomy floor
* function-specific centrality scope
* strengthened-function declarations
* preserved-distributed-function declarations
* restricted-function declarations
* trigger context
* evidence references
* reversibility policy
* expiry time
* return conditions
* human-review boundary
* previous-state target
* parent record references
* related-protocol references
* decision-authority Trace
* No Permanent Emergency Gravity principle
* initial validation script
* GitHub Actions validation workflow
* Python dependency declaration

### Validation

Added semantic validation for:

* aggregate weight totals
* weighted breathing-index calculation
* centrality-scope overlap
* observation-window chronology
* state-expiry chronology
* emergency reversibility
* emergency human-review requirement
* emergency expiry requirement
* emergency return-condition requirement

### Design principles

* Centrality is a dynamically adjustable field rather than a permanent topology.
* A system should not be forced into a binary centralized-or-distributed state.
* Audit, routing, resources, coordination, and emergency authority may be adjusted independently.
* Aggregate values are used for observation.
* Individual gravity axes are used for control.
* Temporary emergency concentration must remain reversible.
* Every increase in emergency authority must include an expiry and a return path.
