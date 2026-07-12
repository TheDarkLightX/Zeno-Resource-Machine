//! Independent structure-preserving reject-order atlas for `WP3b`.

use zrm_codec::ResourceWireV1;
use zrm_kernel::{IntrinsicResourceErrorV1, IntrinsicResourceFieldV1, IntrinsicResourceV1};

const DEFECT_COUNT: usize = 16;
const DEFECT_MASKS: [u16; DEFECT_COUNT] = [
    0x0001, 0x0002, 0x0004, 0x0008, 0x0010, 0x0020, 0x0040, 0x0080, 0x0100, 0x0200, 0x0400, 0x0800,
    0x1000, 0x2000, 0x4000, 0x8000,
];

fn valid_wire() -> ResourceWireV1 {
    ResourceWireV1 {
        machine_id: [1; 32],
        domain_id: [2; 32],
        application_id: [3; 32],
        resource_kind_id: [4; 32],
        resource_logic_id: [5; 32],
        logic_profile_id: [6; 32],
        resource_kind_policy_id: [7; 32],
        unit_id: [8; 32],
        quantity_atoms: 0,
        label_root: [10; 32],
        value_root: [11; 32],
        controller_root: [12; 32],
        policy_root: [13; 32],
        provenance_root: [14; 32],
        nonce: [15; 32],
        created_epoch: 1,
        expiry_epoch: Some(1),
        flags: 0,
    }
}

fn has_defect(mask: u16, index: usize) -> bool {
    DEFECT_MASKS
        .get(index)
        .is_some_and(|defect| mask & defect != 0)
}

const fn zero_field_index(field: IntrinsicResourceFieldV1) -> usize {
    match field {
        IntrinsicResourceFieldV1::MachineId => 0,
        IntrinsicResourceFieldV1::DomainId => 1,
        IntrinsicResourceFieldV1::ApplicationId => 2,
        IntrinsicResourceFieldV1::ResourceKindId => 3,
        IntrinsicResourceFieldV1::ResourceLogicId => 4,
        IntrinsicResourceFieldV1::LogicProfileId => 5,
        IntrinsicResourceFieldV1::ResourceKindPolicyId => 6,
        IntrinsicResourceFieldV1::UnitId => 7,
        IntrinsicResourceFieldV1::LabelRoot => 8,
        IntrinsicResourceFieldV1::ValueRoot => 9,
        IntrinsicResourceFieldV1::ControllerRoot => 10,
        IntrinsicResourceFieldV1::PolicyRoot => 11,
        IntrinsicResourceFieldV1::ProvenanceRoot => 12,
        IntrinsicResourceFieldV1::Nonce => 13,
    }
}

fn apply_identity_defects(wire: &mut ResourceWireV1, mask: u16) {
    if has_defect(mask, 0) {
        wire.machine_id = [0; 32];
    }
    if has_defect(mask, 1) {
        wire.domain_id = [0; 32];
    }
    if has_defect(mask, 2) {
        wire.application_id = [0; 32];
    }
    if has_defect(mask, 3) {
        wire.resource_kind_id = [0; 32];
    }
    if has_defect(mask, 4) {
        wire.resource_logic_id = [0; 32];
    }
    if has_defect(mask, 5) {
        wire.logic_profile_id = [0; 32];
    }
    if has_defect(mask, 6) {
        wire.resource_kind_policy_id = [0; 32];
    }
    if has_defect(mask, 7) {
        wire.unit_id = [0; 32];
    }
}

fn apply_commitment_defects(wire: &mut ResourceWireV1, mask: u16) {
    if has_defect(mask, 8) {
        wire.label_root = [0; 32];
    }
    if has_defect(mask, 9) {
        wire.value_root = [0; 32];
    }
    if has_defect(mask, 10) {
        wire.controller_root = [0; 32];
    }
    if has_defect(mask, 11) {
        wire.policy_root = [0; 32];
    }
    if has_defect(mask, 12) {
        wire.provenance_root = [0; 32];
    }
    if has_defect(mask, 13) {
        wire.nonce = [0; 32];
    }
}

fn apply_tail_defects(wire: &mut ResourceWireV1, mask: u16) {
    if has_defect(mask, 14) {
        wire.created_epoch = 2;
        wire.expiry_epoch = Some(1);
    }
    if has_defect(mask, 15) {
        wire.flags = 0x8000_0001;
    }
}

fn apply_defects(wire: &mut ResourceWireV1, mask: u16) {
    apply_identity_defects(wire, mask);
    apply_commitment_defects(wire, mask);
    apply_tail_defects(wire, mask);
}

fn expected_error(mask: u16) -> Option<IntrinsicResourceErrorV1> {
    let zero_fields = [
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
    for (index, field) in zero_fields.into_iter().enumerate() {
        if has_defect(mask, index) {
            return Some(IntrinsicResourceErrorV1::ZeroField { field });
        }
    }
    if has_defect(mask, 14) {
        return Some(IntrinsicResourceErrorV1::ExpiryBeforeCreation {
            created_epoch: 2,
            expiry_epoch: 1,
        });
    }
    if has_defect(mask, 15) {
        return Some(IntrinsicResourceErrorV1::UnknownFlags { bits: 0x8000_0001 });
    }
    None
}

#[test]
fn all_defect_masks_match_the_independent_first_error_oracle() {
    let mut reached = [false; DEFECT_COUNT + 1];
    for mask in 0_u16..=u16::MAX {
        let mut wire = valid_wire();
        apply_defects(&mut wire, mask);
        let retained_snapshot = wire.clone();
        let expected = expected_error(mask);
        let actual = IntrinsicResourceV1::try_from_wire(&wire).map(|_| ()).err();
        assert_eq!(actual, expected);
        assert_eq!(wire, retained_snapshot);

        let reached_index = expected.map_or(DEFECT_COUNT, |error| match error {
            IntrinsicResourceErrorV1::ZeroField { field } => zero_field_index(field),
            IntrinsicResourceErrorV1::ExpiryBeforeCreation { .. } => 14,
            IntrinsicResourceErrorV1::UnknownFlags { .. } => 15,
            IntrinsicResourceErrorV1::ResourceIdDerivation(_) => DEFECT_COUNT,
        });
        if let Some(slot) = reached.get_mut(reached_index) {
            *slot = true;
        }
    }
    assert!(reached.into_iter().all(|outcome| outcome));
}
