//! Public-boundary tests for policy-independent resource construction.

use zrm_codec::{ResourceWireDecodeError, ResourceWireV1, decode_resource_wire_v1};
use zrm_kernel::{IntrinsicResourceErrorV1, IntrinsicResourceFieldV1, IntrinsicResourceV1};

const ABSENT_VECTOR: &[u8; 595] = include_bytes!("../../../vectors/resource_wire_v1_absent.bin");
const PRESENT_VECTOR: &[u8; 603] = include_bytes!("../../../vectors/resource_wire_v1_present.bin");
const ABSENT_RESOURCE_ID: [u8; 32] = [
    0x41, 0x94, 0x23, 0x6e, 0x9f, 0x6b, 0xf4, 0xb2, 0x7f, 0x2e, 0x06, 0x21, 0x8a, 0xa6, 0x9b, 0x8c,
    0x4a, 0x58, 0xa2, 0xd6, 0x9b, 0xfa, 0xc5, 0xda, 0xeb, 0x72, 0x57, 0x40, 0x20, 0x86, 0xe8, 0xc5,
];
const PRESENT_RESOURCE_ID: [u8; 32] = [
    0x83, 0x58, 0x6e, 0x47, 0x0f, 0x24, 0x59, 0x99, 0xda, 0x41, 0x63, 0xf7, 0x53, 0x41, 0x0c, 0xf4,
    0x66, 0x06, 0xaf, 0xe4, 0xfc, 0x3a, 0x15, 0xb2, 0xc2, 0x0a, 0x61, 0x59, 0xd1, 0x3f, 0x57, 0xb8,
];

#[derive(Debug)]
enum TestError {
    Decode,
    Intrinsic,
}

impl From<ResourceWireDecodeError> for TestError {
    fn from(_: ResourceWireDecodeError) -> Self {
        Self::Decode
    }
}

impl From<IntrinsicResourceErrorV1> for TestError {
    fn from(_: IntrinsicResourceErrorV1) -> Self {
        Self::Intrinsic
    }
}

fn fixture(expiry_epoch: Option<u64>) -> ResourceWireV1 {
    ResourceWireV1 {
        machine_id: [0x01; 32],
        domain_id: [0x02; 32],
        application_id: [0x03; 32],
        resource_kind_id: [0x04; 32],
        resource_logic_id: [0x05; 32],
        logic_profile_id: [0x06; 32],
        resource_kind_policy_id: [0x07; 32],
        unit_id: [0x08; 32],
        quantity_atoms: 0x0102_0304_0506_0708_090a_0b0c_0d0e_0f10,
        label_root: [0x0a; 32],
        value_root: [0x0b; 32],
        controller_root: [0x0c; 32],
        policy_root: [0x0d; 32],
        provenance_root: [0x0e; 32],
        nonce: [0x0f; 32],
        created_epoch: 0x0102_0304_0506_0708,
        expiry_epoch,
        flags: 0,
    }
}

fn set_zero(wire: &mut ResourceWireV1, field: IntrinsicResourceFieldV1) {
    match field {
        IntrinsicResourceFieldV1::MachineId => wire.machine_id = [0; 32],
        IntrinsicResourceFieldV1::DomainId => wire.domain_id = [0; 32],
        IntrinsicResourceFieldV1::ApplicationId => wire.application_id = [0; 32],
        IntrinsicResourceFieldV1::ResourceKindId => wire.resource_kind_id = [0; 32],
        IntrinsicResourceFieldV1::ResourceLogicId => wire.resource_logic_id = [0; 32],
        IntrinsicResourceFieldV1::LogicProfileId => wire.logic_profile_id = [0; 32],
        IntrinsicResourceFieldV1::ResourceKindPolicyId => {
            wire.resource_kind_policy_id = [0; 32];
        }
        IntrinsicResourceFieldV1::UnitId => wire.unit_id = [0; 32],
        IntrinsicResourceFieldV1::LabelRoot => wire.label_root = [0; 32],
        IntrinsicResourceFieldV1::ValueRoot => wire.value_root = [0; 32],
        IntrinsicResourceFieldV1::ControllerRoot => wire.controller_root = [0; 32],
        IntrinsicResourceFieldV1::PolicyRoot => wire.policy_root = [0; 32],
        IntrinsicResourceFieldV1::ProvenanceRoot => wire.provenance_root = [0; 32],
        IntrinsicResourceFieldV1::Nonce => wire.nonce = [0; 32],
    }
}

const ZERO_FIELDS: [IntrinsicResourceFieldV1; 14] = [
    IntrinsicResourceFieldV1::MachineId,
    IntrinsicResourceFieldV1::DomainId,
    IntrinsicResourceFieldV1::ApplicationId,
    IntrinsicResourceFieldV1::ResourceKindId,
    IntrinsicResourceFieldV1::ResourceLogicId,
    IntrinsicResourceFieldV1::LogicProfileId,
    IntrinsicResourceFieldV1::ResourceKindPolicyId,
    IntrinsicResourceFieldV1::UnitId,
    IntrinsicResourceFieldV1::LabelRoot,
    IntrinsicResourceFieldV1::ValueRoot,
    IntrinsicResourceFieldV1::ControllerRoot,
    IntrinsicResourceFieldV1::PolicyRoot,
    IntrinsicResourceFieldV1::ProvenanceRoot,
    IntrinsicResourceFieldV1::Nonce,
];

fn assert_identity_fields(resource: &IntrinsicResourceV1) {
    assert_eq!(resource.machine_id().into_bytes(), [0x01; 32]);
    assert_eq!(resource.domain_id().into_bytes(), [0x02; 32]);
    assert_eq!(resource.application_id().into_bytes(), [0x03; 32]);
    assert_eq!(resource.resource_kind_id().into_bytes(), [0x04; 32]);
    assert_eq!(resource.resource_logic_id().into_bytes(), [0x05; 32]);
    assert_eq!(resource.logic_profile_id().into_bytes(), [0x06; 32]);
    assert_eq!(resource.resource_kind_policy_id().into_bytes(), [0x07; 32]);
    assert_eq!(resource.unit_id().into_bytes(), [0x08; 32]);
}

fn assert_commitment_fields(resource: &IntrinsicResourceV1) {
    assert_eq!(resource.label_root().into_bytes(), [0x0a; 32]);
    assert_eq!(resource.value_root().into_bytes(), [0x0b; 32]);
    assert_eq!(resource.controller_root().into_bytes(), [0x0c; 32]);
    assert_eq!(resource.policy_root().into_bytes(), [0x0d; 32]);
    assert_eq!(resource.provenance_root().into_bytes(), [0x0e; 32]);
    assert_eq!(resource.nonce().into_bytes(), [0x0f; 32]);
}

fn assert_scalar_fields(resource: &IntrinsicResourceV1) {
    assert_eq!(
        resource.quantity_atoms().get(),
        0x0102_0304_0506_0708_090a_0b0c_0d0e_0f10
    );
    assert_eq!(resource.created_epoch(), 0x0102_0304_0506_0708);
    assert_eq!(resource.expiry_epoch(), None);
    assert_eq!(resource.flags().bits(), 0);
}

#[test]
fn exact_absent_vector_constructs_and_preserves_every_field() -> Result<(), TestError> {
    let wire = decode_resource_wire_v1(ABSENT_VECTOR)?;
    let resource = IntrinsicResourceV1::try_from_wire(&wire)?;
    assert_eq!(resource.resource_id().into_bytes(), ABSENT_RESOURCE_ID);
    assert_identity_fields(&resource);
    assert_commitment_fields(&resource);
    assert_scalar_fields(&resource);
    Ok(())
}

#[test]
fn exact_present_vector_constructs_through_try_from() -> Result<(), TestError> {
    let wire = decode_resource_wire_v1(PRESENT_VECTOR)?;
    let resource = IntrinsicResourceV1::try_from(wire)?;
    assert_eq!(resource.resource_id().into_bytes(), PRESENT_RESOURCE_ID);
    assert_eq!(resource.expiry_epoch(), Some(0x1112_1314_1516_1718));
    Ok(())
}

#[test]
fn each_zero_field_rejects_with_exact_local_identity() {
    for field in ZERO_FIELDS {
        let mut wire = fixture(None);
        set_zero(&mut wire, field);
        assert_eq!(
            IntrinsicResourceV1::try_from_wire(&wire),
            Err(IntrinsicResourceErrorV1::ZeroField { field })
        );
    }
}

#[test]
fn quantity_values_remain_exact_unresolved_candidates() -> Result<(), TestError> {
    for quantity in [0, 1, u128::MAX] {
        let mut wire = fixture(None);
        wire.quantity_atoms = quantity;
        let resource = IntrinsicResourceV1::try_from_wire(&wire)?;
        assert_eq!(resource.quantity_atoms().get(), quantity);
    }
    Ok(())
}

#[test]
fn expiry_boundaries_are_exact() -> Result<(), TestError> {
    let mut absent = fixture(None);
    absent.created_epoch = u64::MAX;
    assert_eq!(
        IntrinsicResourceV1::try_from_wire(&absent)?.expiry_epoch(),
        None
    );

    let mut equal = fixture(Some(u64::MAX));
    equal.created_epoch = u64::MAX;
    assert_eq!(
        IntrinsicResourceV1::try_from_wire(&equal)?.expiry_epoch(),
        Some(u64::MAX)
    );

    let mut earlier = fixture(Some(u64::MAX - 1));
    earlier.created_epoch = u64::MAX;
    assert_eq!(
        IntrinsicResourceV1::try_from_wire(&earlier),
        Err(IntrinsicResourceErrorV1::ExpiryBeforeCreation {
            created_epoch: u64::MAX,
            expiry_epoch: u64::MAX - 1,
        })
    );
    Ok(())
}

#[test]
fn representative_nonzero_flag_patterns_reject_with_exact_bits() {
    for bits in [1, 0x8000_0000, u32::MAX] {
        let mut wire = fixture(None);
        wire.flags = bits;
        assert_eq!(
            IntrinsicResourceV1::try_from_wire(&wire),
            Err(IntrinsicResourceErrorV1::UnknownFlags { bits })
        );
    }
}

fn assert_reject_preserves_wire(wire: &ResourceWireV1) {
    let retained_snapshot = wire.clone();
    assert!(IntrinsicResourceV1::try_from_wire(wire).is_err());
    assert_eq!(*wire, retained_snapshot);
}

#[test]
fn every_public_semantic_reject_family_leaves_borrowed_wire_unchanged() {
    for field in ZERO_FIELDS {
        let mut wire = fixture(None);
        set_zero(&mut wire, field);
        assert_reject_preserves_wire(&wire);
    }

    let mut invalid_epoch = fixture(Some(1));
    invalid_epoch.created_epoch = 2;
    assert_reject_preserves_wire(&invalid_epoch);

    let mut invalid_flags = fixture(None);
    invalid_flags.flags = 1;
    assert_reject_preserves_wire(&invalid_flags);
}
