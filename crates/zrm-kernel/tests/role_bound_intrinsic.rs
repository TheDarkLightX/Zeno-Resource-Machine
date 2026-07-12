//! Public-boundary tests for intrinsic-body role and ordinal binding.

use zrm_codec::{ResourceWireDecodeError, ResourceWireV1, decode_resource_wire_v1};
use zrm_kernel::{
    CanonicalResourceRolesV1, IntrinsicResourceErrorV1, IntrinsicResourceV1,
    IntrinsicRoleBindingErrorV1, ResourceRoleListsCandidateV1, ResourceRolePartitionErrorV1,
    ResourceRoleV1,
};
use zrm_policy::PolicyLimitsV1;
use zrm_types::{ResourceId, ZeroValueError};

const ABSENT_VECTOR: &[u8; 595] = include_bytes!("../../../vectors/resource_wire_v1_absent.bin");
const PRESENT_VECTOR: &[u8; 603] = include_bytes!("../../../vectors/resource_wire_v1_present.bin");

#[derive(Debug)]
enum TestError {
    Decode,
    Intrinsic,
    Partition,
    Binding,
    Zero,
    MissingExpectedOrdinal,
    MissingOrdinalCeilingFixture,
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

impl From<ResourceRolePartitionErrorV1> for TestError {
    fn from(_: ResourceRolePartitionErrorV1) -> Self {
        Self::Partition
    }
}

impl From<IntrinsicRoleBindingErrorV1> for TestError {
    fn from(_: IntrinsicRoleBindingErrorV1) -> Self {
        Self::Binding
    }
}

impl From<ZeroValueError> for TestError {
    fn from(_: ZeroValueError) -> Self {
        Self::Zero
    }
}

fn fixture() -> ResourceWireV1 {
    ResourceWireV1 {
        machine_id: [1; 32],
        domain_id: [2; 32],
        application_id: [3; 32],
        resource_kind_id: [4; 32],
        resource_logic_id: [5; 32],
        logic_profile_id: [6; 32],
        resource_kind_policy_id: [7; 32],
        unit_id: [8; 32],
        quantity_atoms: 9,
        label_root: [10; 32],
        value_root: [11; 32],
        controller_root: [12; 32],
        policy_root: [13; 32],
        provenance_root: [14; 32],
        nonce: [15; 32],
        created_epoch: 1,
        expiry_epoch: Some(2),
        flags: 0,
    }
}

fn role_lists<'a>(
    consumed: &'a [ResourceId],
    referenced: &'a [ResourceId],
    created: &'a [ResourceId],
) -> ResourceRoleListsCandidateV1<'a> {
    ResourceRoleListsCandidateV1 {
        consumed,
        referenced,
        created,
    }
}

fn bind_in_role(resource: &IntrinsicResourceV1, role: ResourceRoleV1) -> Result<(), TestError> {
    let target = resource.resource_id();
    let low = ResourceId::try_from([1; 32])?;
    let high = ResourceId::try_from([0xff; 32])?;
    let candidates = [high, target, low];
    let empty = [];
    let (consumed, referenced, created) = match role {
        ResourceRoleV1::Consumed => (candidates.as_slice(), empty.as_slice(), empty.as_slice()),
        ResourceRoleV1::Referenced => (empty.as_slice(), candidates.as_slice(), empty.as_slice()),
        ResourceRoleV1::Created => (empty.as_slice(), empty.as_slice(), candidates.as_slice()),
    };
    let roles = CanonicalResourceRolesV1::try_new(
        role_lists(consumed, referenced, created),
        PolicyLimitsV1::strict_default(),
    )?;
    let bound = roles.bind_intrinsic(resource)?;
    let mut canonical = candidates;
    canonical.sort();
    let expected_ordinal = canonical
        .iter()
        .position(|resource_id| *resource_id == target)
        .and_then(|ordinal| u32::try_from(ordinal).ok())
        .ok_or(TestError::MissingExpectedOrdinal)?;

    assert_eq!(bound.resource(), resource);
    assert_eq!(bound.resource_id(), resource.resource_id());
    assert_eq!(bound.role(), role);
    assert_eq!(bound.ordinal(), expected_ordinal);
    assert_eq!(bound.position().resource_id(), resource.resource_id());
    assert_eq!(bound.position().role(), role);
    assert_eq!(bound.position().ordinal(), expected_ordinal);
    Ok(())
}

#[test]
fn exact_wp1_vectors_bind_in_every_structural_role() -> Result<(), TestError> {
    let absent = IntrinsicResourceV1::try_from(decode_resource_wire_v1(ABSENT_VECTOR)?)?;
    let present = IntrinsicResourceV1::try_from(decode_resource_wire_v1(PRESENT_VECTOR)?)?;
    for role in [
        ResourceRoleV1::Consumed,
        ResourceRoleV1::Referenced,
        ResourceRoleV1::Created,
    ] {
        bind_in_role(&absent, role)?;
        bind_in_role(&present, role)?;
    }
    Ok(())
}

#[test]
fn absent_resource_rejects_without_changing_either_input() -> Result<(), TestError> {
    let resource = IntrinsicResourceV1::try_from(fixture())?;
    let other = ResourceId::try_from([0xa5; 32])?;
    let roles = CanonicalResourceRolesV1::try_new(
        role_lists(&[other], &[], &[]),
        PolicyLimitsV1::strict_default(),
    )?;
    let resource_snapshot = resource;
    let role_snapshot = roles.consumed().to_vec();

    assert_eq!(
        roles.bind_intrinsic(&resource),
        Err(IntrinsicRoleBindingErrorV1::ResourceAbsentFromRoles)
    );
    assert_eq!(resource, resource_snapshot);
    assert_eq!(roles.consumed(), role_snapshot);
    Ok(())
}

fn valid_field_mutations(base: &ResourceWireV1) -> Vec<ResourceWireV1> {
    let mut variants = Vec::new();
    let mut push = |mutate: fn(&mut ResourceWireV1)| {
        let mut variant = base.clone();
        mutate(&mut variant);
        variants.push(variant);
    };
    push(|wire| wire.machine_id = [21; 32]);
    push(|wire| wire.domain_id = [22; 32]);
    push(|wire| wire.application_id = [23; 32]);
    push(|wire| wire.resource_kind_id = [24; 32]);
    push(|wire| wire.resource_logic_id = [25; 32]);
    push(|wire| wire.logic_profile_id = [26; 32]);
    push(|wire| wire.resource_kind_policy_id = [27; 32]);
    push(|wire| wire.unit_id = [28; 32]);
    push(|wire| wire.quantity_atoms = 10);
    push(|wire| wire.label_root = [30; 32]);
    push(|wire| wire.value_root = [31; 32]);
    push(|wire| wire.controller_root = [32; 32]);
    push(|wire| wire.policy_root = [33; 32]);
    push(|wire| wire.provenance_root = [34; 32]);
    push(|wire| wire.nonce = [35; 32]);
    push(|wire| wire.created_epoch = 2);
    push(|wire| wire.expiry_epoch = None);
    variants
}

#[test]
fn every_valid_body_field_mutation_rejects_against_the_stale_partition() -> Result<(), TestError> {
    let base_wire = fixture();
    let base = IntrinsicResourceV1::try_from_wire(&base_wire)?;
    let roles = CanonicalResourceRolesV1::try_new(
        role_lists(&[base.resource_id()], &[], &[]),
        PolicyLimitsV1::strict_default(),
    )?;

    let variants = valid_field_mutations(&base_wire);
    assert_eq!(variants.len(), 17);
    for variant in variants {
        let changed = IntrinsicResourceV1::try_from(variant)?;
        assert_ne!(changed.resource_id(), base.resource_id());
        assert_eq!(
            roles.bind_intrinsic(&changed),
            Err(IntrinsicRoleBindingErrorV1::ResourceAbsentFromRoles)
        );
    }
    Ok(())
}

#[test]
fn role_local_permutation_cannot_change_the_binding() -> Result<(), TestError> {
    let target = IntrinsicResourceV1::try_from(fixture())?;
    let one = ResourceId::try_from([1; 32])?;
    let high = ResourceId::try_from([0xff; 32])?;
    let first_order = [target.resource_id(), high, one];
    let second_order = [one, target.resource_id(), high];
    let first = CanonicalResourceRolesV1::try_new(
        role_lists(&[], &first_order, &[]),
        PolicyLimitsV1::strict_default(),
    )?;
    let second = CanonicalResourceRolesV1::try_new(
        role_lists(&[], &second_order, &[]),
        PolicyLimitsV1::strict_default(),
    )?;

    assert_eq!(first, second);
    assert_eq!(
        first.bind_intrinsic(&target)?,
        second.bind_intrinsic(&target)?
    );
    Ok(())
}

#[test]
fn wrapper_preserves_the_role_local_ordinal_ceiling() -> Result<(), TestError> {
    let target = (1_u128..=1024)
        .find_map(|quantity_atoms| {
            let mut candidate = fixture();
            candidate.quantity_atoms = quantity_atoms;
            let resource = IntrinsicResourceV1::try_from(candidate).ok()?;
            (resource.resource_id().as_bytes()[0] != 0).then_some(resource)
        })
        .ok_or(TestError::MissingOrdinalCeilingFixture)?;

    let mut lower_ids = Vec::with_capacity(255);
    for suffix in 1_u8..=u8::MAX {
        let mut bytes = [0_u8; 32];
        bytes[31] = suffix;
        lower_ids.push(ResourceId::try_from(bytes)?);
    }
    lower_ids.push(target.resource_id());
    let roles = CanonicalResourceRolesV1::try_new(
        role_lists(&lower_ids, &[], &[]),
        PolicyLimitsV1::protocol_ceiling(),
    )?;

    let bound = roles.bind_intrinsic(&target)?;
    assert_eq!(bound.role(), ResourceRoleV1::Consumed);
    assert_eq!(bound.ordinal(), 255);
    assert_eq!(bound.position().ordinal(), 255);
    Ok(())
}
