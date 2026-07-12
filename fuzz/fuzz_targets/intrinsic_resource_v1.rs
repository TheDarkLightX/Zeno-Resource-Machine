#![no_main]

use libfuzzer_sys::fuzz_target;
use zrm_codec::ResourceWireV1;
use zrm_kernel::{IntrinsicResourceErrorV1, IntrinsicResourceFieldV1, IntrinsicResourceV1};

const DEFECT_MASKS: [u16; 16] = [
    0x0001, 0x0002, 0x0004, 0x0008, 0x0010, 0x0020, 0x0040, 0x0080, 0x0100, 0x0200, 0x0400, 0x0800,
    0x1000, 0x2000, 0x4000, 0x8000,
];

fn defect_mask(data: &[u8]) -> u16 {
    data.iter().zip(DEFECT_MASKS).fold(
        0_u16,
        |mask, (byte, defect)| {
            if byte & 1 == 1 { mask | defect } else { mask }
        },
    )
}

fn quantity(data: &[u8]) -> u128 {
    let Some(bytes) = data.get(16..32) else {
        return 0;
    };
    let Ok(bytes) = <[u8; 16]>::try_from(bytes) else {
        return 0;
    };
    u128::from_be_bytes(bytes)
}

fn valid_wire(quantity_atoms: u128) -> ResourceWireV1 {
    ResourceWireV1 {
        machine_id: [1; 32],
        domain_id: [2; 32],
        application_id: [3; 32],
        resource_kind_id: [4; 32],
        resource_logic_id: [5; 32],
        logic_profile_id: [6; 32],
        resource_kind_policy_id: [7; 32],
        unit_id: [8; 32],
        quantity_atoms,
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

fn apply_defects(wire: &mut ResourceWireV1, mask: u16) {
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
    if has_defect(mask, 14) {
        wire.created_epoch = 2;
    }
    if has_defect(mask, 15) {
        wire.flags = 0x8000_0001;
    }
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

fuzz_target!(|data: &[u8]| {
    let mask = defect_mask(data);
    let mut wire = valid_wire(quantity(data));
    apply_defects(&mut wire, mask);
    let expected = expected_error(mask);
    let actual = IntrinsicResourceV1::try_from_wire(&wire);
    match (actual, expected) {
        (Ok(resource), None) => {
            assert_eq!(wire.resource_id(), Ok(resource.resource_id()));
            assert_eq!(resource.quantity_atoms().get(), wire.quantity_atoms);
            assert_eq!(resource.created_epoch(), wire.created_epoch);
            assert_eq!(resource.expiry_epoch(), wire.expiry_epoch);
            assert_eq!(resource.flags().bits(), wire.flags);
        }
        (Err(actual), Some(expected)) => assert_eq!(actual, expected),
        (actual, expected) => {
            panic!("intrinsic resource oracle mismatch: {actual:?} != {expected:?}")
        }
    }
});
