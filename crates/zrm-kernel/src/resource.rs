//! Policy-independent construction of a typed version-one resource body.

use zrm_codec::{ResourceIdDerivationError, ResourceWireV1};
use zrm_types::{
    ApplicationId, Commitment, ControllerRoot, DomainId, LogicProfileId, MachineId, PolicyId,
    ProvenanceRoot, QuantityAtoms, ResourceFlagsV1, ResourceId, ResourceKindId, ResourceLogicId,
    ResourceNonce, UnitId, ZeroValueError,
};

mod error;

pub use error::{IntrinsicResourceErrorV1, IntrinsicResourceFieldV1};

#[cfg(kani)]
mod kani_harnesses;

#[cfg(test)]
mod tests;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct ResourceIdentityV1 {
    machine: MachineId,
    domain: DomainId,
    application: ApplicationId,
    resource_kind: ResourceKindId,
    resource_logic: ResourceLogicId,
    logic_profile: LogicProfileId,
    resource_kind_policy: PolicyId,
    unit: UnitId,
}

impl ResourceIdentityV1 {
    fn try_from_wire(wire: &ResourceWireV1) -> Result<Self, IntrinsicResourceErrorV1> {
        Ok(Self {
            machine: require_nonzero(wire.machine_id, IntrinsicResourceFieldV1::MachineId)?,
            domain: require_nonzero(wire.domain_id, IntrinsicResourceFieldV1::DomainId)?,
            application: require_nonzero(
                wire.application_id,
                IntrinsicResourceFieldV1::ApplicationId,
            )?,
            resource_kind: require_nonzero(
                wire.resource_kind_id,
                IntrinsicResourceFieldV1::ResourceKindId,
            )?,
            resource_logic: require_nonzero(
                wire.resource_logic_id,
                IntrinsicResourceFieldV1::ResourceLogicId,
            )?,
            logic_profile: require_nonzero(
                wire.logic_profile_id,
                IntrinsicResourceFieldV1::LogicProfileId,
            )?,
            resource_kind_policy: require_nonzero(
                wire.resource_kind_policy_id,
                IntrinsicResourceFieldV1::ResourceKindPolicyId,
            )?,
            unit: require_nonzero(wire.unit_id, IntrinsicResourceFieldV1::UnitId)?,
        })
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct ResourceCommitmentsV1 {
    label: Commitment,
    value: Commitment,
    controller: ControllerRoot,
    policy: Commitment,
    provenance: ProvenanceRoot,
}

impl ResourceCommitmentsV1 {
    fn try_from_wire(wire: &ResourceWireV1) -> Result<Self, IntrinsicResourceErrorV1> {
        Ok(Self {
            label: require_nonzero(wire.label_root, IntrinsicResourceFieldV1::LabelRoot)?,
            value: require_nonzero(wire.value_root, IntrinsicResourceFieldV1::ValueRoot)?,
            controller: require_nonzero(
                wire.controller_root,
                IntrinsicResourceFieldV1::ControllerRoot,
            )?,
            policy: require_nonzero(wire.policy_root, IntrinsicResourceFieldV1::PolicyRoot)?,
            provenance: require_nonzero(
                wire.provenance_root,
                IntrinsicResourceFieldV1::ProvenanceRoot,
            )?,
        })
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct IntrinsicResourceFieldsV1 {
    identity: ResourceIdentityV1,
    quantity_atoms: QuantityAtoms,
    commitments: ResourceCommitmentsV1,
    nonce: ResourceNonce,
    created_epoch: u64,
    expiry_epoch: Option<u64>,
    flags: ResourceFlagsV1,
}

/// A sealed, policy-independent version-one resource body.
///
/// Construction validates only intrinsic nonzero, epoch-order, flag, and
/// canonical body-to-ID invariants. In particular, a zero quantity remains an
/// unresolved candidate because the active resource-kind policy must decide
/// whether it represents an allowed marker resource.
///
/// Fields are private, and the public constructor never accepts a
/// caller-provided [`ResourceId`]:
///
/// ```compile_fail
/// use zrm_kernel::IntrinsicResourceV1;
/// use zrm_types::ResourceId;
///
/// let Ok(injected) = ResourceId::try_from([1_u8; 32]) else { return };
/// // error[E0451]: `resource_id` is private; no public field accepts an ID.
/// let _forged = IntrinsicResourceV1 { resource_id: injected };
/// ```
///
/// This type establishes no authenticated policy, state membership, role,
/// logic authorization, transition validity, or commit authority.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[must_use = "intrinsic resource validation has no effect unless its result is used"]
pub struct IntrinsicResourceV1 {
    resource_id: ResourceId,
    fields: IntrinsicResourceFieldsV1,
}

impl IntrinsicResourceV1 {
    /// Borrows a version-one wire candidate and validates intrinsic facts.
    ///
    /// The version-specific input fixes the v1 field set and canonical encoder
    /// but establishes no strict-decoder provenance or authentication. This
    /// constructor checks local semantic invariants in canonical field order,
    /// then derives the exact resource commitment from the complete original
    /// wire value.
    ///
    /// # Errors
    ///
    /// Returns the first local [`IntrinsicResourceErrorV1`]. The error order is
    /// deterministic within this staged boundary but is not the final stable
    /// resource-reject taxonomy.
    ///
    /// # Complexity and side effects
    ///
    /// The constructor performs fixed work over eighteen fields, encodes at
    /// most 603 bytes, allocates one bounded buffer, and computes one SHA-256
    /// resource commitment. It performs no I/O and mutates no caller or global
    /// state.
    ///
    /// # Panics
    ///
    /// This constructor has no intentional panic path. Allocation and hash
    /// construction failures are returned as typed errors.
    pub fn try_from_wire(wire: &ResourceWireV1) -> Result<Self, IntrinsicResourceErrorV1> {
        construct_intrinsic_resource(wire, ResourceWireV1::resource_id)
    }

    /// Returns the exact identifier derived from the complete canonical wire value.
    #[must_use]
    pub const fn resource_id(&self) -> ResourceId {
        self.resource_id
    }

    /// Returns the locally nonzero machine identifier candidate.
    #[must_use]
    pub const fn machine_id(&self) -> MachineId {
        self.fields.identity.machine
    }

    /// Returns the locally nonzero domain identifier candidate.
    #[must_use]
    pub const fn domain_id(&self) -> DomainId {
        self.fields.identity.domain
    }

    /// Returns the locally nonzero application identifier candidate.
    #[must_use]
    pub const fn application_id(&self) -> ApplicationId {
        self.fields.identity.application
    }

    /// Returns the locally nonzero resource-kind identifier candidate.
    #[must_use]
    pub const fn resource_kind_id(&self) -> ResourceKindId {
        self.fields.identity.resource_kind
    }

    /// Returns the locally nonzero resource-logic identifier candidate.
    #[must_use]
    pub const fn resource_logic_id(&self) -> ResourceLogicId {
        self.fields.identity.resource_logic
    }

    /// Returns the locally nonzero logic-profile identifier candidate.
    #[must_use]
    pub const fn logic_profile_id(&self) -> LogicProfileId {
        self.fields.identity.logic_profile
    }

    /// Returns the locally nonzero resource-kind-policy identifier candidate.
    #[must_use]
    pub const fn resource_kind_policy_id(&self) -> PolicyId {
        self.fields.identity.resource_kind_policy
    }

    /// Returns the locally nonzero quantity-unit identifier candidate.
    #[must_use]
    pub const fn unit_id(&self) -> UnitId {
        self.fields.identity.unit
    }

    /// Returns the exact nonnegative quantity candidate.
    ///
    /// This getter makes no claim that zero or any other value is admitted by
    /// an active resource-kind policy.
    #[must_use]
    pub const fn quantity_atoms(&self) -> QuantityAtoms {
        self.fields.quantity_atoms
    }

    /// Returns the locally nonzero label commitment candidate.
    #[must_use]
    pub const fn label_root(&self) -> Commitment {
        self.fields.commitments.label
    }

    /// Returns the locally nonzero value commitment candidate.
    #[must_use]
    pub const fn value_root(&self) -> Commitment {
        self.fields.commitments.value
    }

    /// Returns the locally nonzero controller-root candidate.
    #[must_use]
    pub const fn controller_root(&self) -> ControllerRoot {
        self.fields.commitments.controller
    }

    /// Returns the locally nonzero resource policy-root candidate.
    #[must_use]
    pub const fn policy_root(&self) -> Commitment {
        self.fields.commitments.policy
    }

    /// Returns the locally nonzero provenance-root candidate.
    #[must_use]
    pub const fn provenance_root(&self) -> ProvenanceRoot {
        self.fields.commitments.provenance
    }

    /// Returns the locally nonzero resource nonce candidate.
    ///
    /// Intrinsic construction establishes neither freshness nor uniqueness.
    #[must_use]
    pub const fn nonce(&self) -> ResourceNonce {
        self.fields.nonce
    }

    /// Returns the exact candidate creation epoch.
    #[must_use]
    pub const fn created_epoch(&self) -> u64 {
        self.fields.created_epoch
    }

    /// Returns the candidate expiry epoch after local ordering validation.
    #[must_use]
    pub const fn expiry_epoch(&self) -> Option<u64> {
        self.fields.expiry_epoch
    }

    /// Returns the validated version-one flags.
    #[must_use]
    pub const fn flags(&self) -> ResourceFlagsV1 {
        self.fields.flags
    }
}

impl TryFrom<ResourceWireV1> for IntrinsicResourceV1 {
    type Error = IntrinsicResourceErrorV1;

    fn try_from(wire: ResourceWireV1) -> Result<Self, Self::Error> {
        Self::try_from_wire(&wire)
    }
}

fn require_nonzero<T>(
    bytes: [u8; 32],
    field: IntrinsicResourceFieldV1,
) -> Result<T, IntrinsicResourceErrorV1>
where
    T: TryFrom<[u8; 32], Error = ZeroValueError>,
{
    T::try_from(bytes).map_err(|_| IntrinsicResourceErrorV1::ZeroField { field })
}

fn validate_intrinsic_fields(
    wire: &ResourceWireV1,
) -> Result<IntrinsicResourceFieldsV1, IntrinsicResourceErrorV1> {
    let identity = ResourceIdentityV1::try_from_wire(wire)?;
    let quantity_atoms = QuantityAtoms::new(wire.quantity_atoms);
    let commitments = ResourceCommitmentsV1::try_from_wire(wire)?;
    let nonce = require_nonzero(wire.nonce, IntrinsicResourceFieldV1::Nonce)?;
    validate_epoch_order(wire.created_epoch, wire.expiry_epoch)?;
    let flags = ResourceFlagsV1::try_from_bits(wire.flags)
        .map_err(|error| IntrinsicResourceErrorV1::UnknownFlags { bits: error.bits() })?;
    Ok(IntrinsicResourceFieldsV1 {
        identity,
        quantity_atoms,
        commitments,
        nonce,
        created_epoch: wire.created_epoch,
        expiry_epoch: wire.expiry_epoch,
        flags,
    })
}

fn validate_epoch_order(
    created_epoch: u64,
    expiry_epoch: Option<u64>,
) -> Result<(), IntrinsicResourceErrorV1> {
    if let Some(expiry_epoch) = expiry_epoch {
        if expiry_epoch < created_epoch {
            return Err(IntrinsicResourceErrorV1::ExpiryBeforeCreation {
                created_epoch,
                expiry_epoch,
            });
        }
    }
    Ok(())
}

fn construct_intrinsic_resource<F>(
    wire: &ResourceWireV1,
    derive_resource_id: F,
) -> Result<IntrinsicResourceV1, IntrinsicResourceErrorV1>
where
    F: FnOnce(&ResourceWireV1) -> Result<ResourceId, ResourceIdDerivationError>,
{
    let fields = validate_intrinsic_fields(wire)?;
    let resource_id =
        derive_resource_id(wire).map_err(IntrinsicResourceErrorV1::ResourceIdDerivation)?;
    Ok(IntrinsicResourceV1 {
        resource_id,
        fields,
    })
}
