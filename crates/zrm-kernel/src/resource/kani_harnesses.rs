//! Bounded checks for the production intrinsic-field validator.
//!
//! These harnesses exclude canonical encoding, allocation, SHA-256, and final
//! policy validity. Ordinary exact-vector tests cover the body-to-ID handoff.

use super::{IntrinsicResourceErrorV1, IntrinsicResourceFieldV1, validate_intrinsic_fields};
use zrm_codec::ResourceWireV1;

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
        quantity_atoms: u128::MAX,
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

fn zero_identity_field(
    wire: &mut ResourceWireV1,
    selector: u8,
) -> Option<IntrinsicResourceFieldV1> {
    match selector {
        0 => {
            wire.machine_id = [0; 32];
            Some(IntrinsicResourceFieldV1::MachineId)
        }
        1 => {
            wire.domain_id = [0; 32];
            Some(IntrinsicResourceFieldV1::DomainId)
        }
        2 => {
            wire.application_id = [0; 32];
            Some(IntrinsicResourceFieldV1::ApplicationId)
        }
        3 => {
            wire.resource_kind_id = [0; 32];
            Some(IntrinsicResourceFieldV1::ResourceKindId)
        }
        4 => {
            wire.resource_logic_id = [0; 32];
            Some(IntrinsicResourceFieldV1::ResourceLogicId)
        }
        5 => {
            wire.logic_profile_id = [0; 32];
            Some(IntrinsicResourceFieldV1::LogicProfileId)
        }
        6 => {
            wire.resource_kind_policy_id = [0; 32];
            Some(IntrinsicResourceFieldV1::ResourceKindPolicyId)
        }
        7 => {
            wire.unit_id = [0; 32];
            Some(IntrinsicResourceFieldV1::UnitId)
        }
        _ => None,
    }
}

fn zero_commitment_field(wire: &mut ResourceWireV1, selector: u8) -> IntrinsicResourceFieldV1 {
    match selector {
        8 => {
            wire.label_root = [0; 32];
            IntrinsicResourceFieldV1::LabelRoot
        }
        9 => {
            wire.value_root = [0; 32];
            IntrinsicResourceFieldV1::ValueRoot
        }
        10 => {
            wire.controller_root = [0; 32];
            IntrinsicResourceFieldV1::ControllerRoot
        }
        11 => {
            wire.policy_root = [0; 32];
            IntrinsicResourceFieldV1::PolicyRoot
        }
        12 => {
            wire.provenance_root = [0; 32];
            IntrinsicResourceFieldV1::ProvenanceRoot
        }
        _ => {
            wire.nonce = [0; 32];
            IntrinsicResourceFieldV1::Nonce
        }
    }
}

fn zero_selected_field(wire: &mut ResourceWireV1, selector: u8) -> IntrinsicResourceFieldV1 {
    if let Some(field) = zero_identity_field(wire, selector) {
        field
    } else {
        zero_commitment_field(wire, selector)
    }
}

#[kani::proof]
#[kani::unwind(40)]
fn every_selected_zero_field_has_exact_identity() {
    let selector: u8 = kani::any();
    kani::assume(selector < 14);
    let mut wire = valid_wire();
    let field = zero_selected_field(&mut wire, selector);
    let actual = validate_intrinsic_fields(&wire).map(|_| ());
    assert_eq!(actual, Err(IntrinsicResourceErrorV1::ZeroField { field }));
    kani::cover!(selector == 0);
    kani::cover!(selector == 7);
    kani::cover!(selector == 13);
}

#[kani::proof]
#[kani::unwind(40)]
fn every_zero_field_pair_uses_canonical_order() {
    let first: u8 = kani::any();
    let second: u8 = kani::any();
    kani::assume(first < 14);
    kani::assume(second < 14);
    let mut wire = valid_wire();
    let first_field = zero_selected_field(&mut wire, first);
    let second_field = zero_selected_field(&mut wire, second);
    let expected_field = if first <= second {
        first_field
    } else {
        second_field
    };
    assert_eq!(
        validate_intrinsic_fields(&wire).map(|_| ()),
        Err(IntrinsicResourceErrorV1::ZeroField {
            field: expected_field,
        })
    );
    kani::cover!(first < second);
    kani::cover!(first == second);
    kani::cover!(first > second);
}

#[kani::proof]
#[kani::unwind(40)]
fn epoch_error_precedes_unknown_flags() {
    let invalid_epoch: bool = kani::any();
    let invalid_flags: bool = kani::any();
    let mut wire = valid_wire();
    if invalid_epoch {
        wire.created_epoch = 2;
    }
    if invalid_flags {
        wire.flags = u32::MAX;
    }
    let actual = validate_intrinsic_fields(&wire).map(|_| ());
    let expected = if invalid_epoch {
        Err(IntrinsicResourceErrorV1::ExpiryBeforeCreation {
            created_epoch: 2,
            expiry_epoch: 1,
        })
    } else if invalid_flags {
        Err(IntrinsicResourceErrorV1::UnknownFlags { bits: u32::MAX })
    } else {
        Ok(())
    };
    assert_eq!(actual, expected);
    kani::cover!(actual.is_ok());
    kani::cover!(matches!(
        actual,
        Err(IntrinsicResourceErrorV1::ExpiryBeforeCreation { .. })
    ));
    kani::cover!(matches!(
        actual,
        Err(IntrinsicResourceErrorV1::UnknownFlags { .. })
    ));
}

#[kani::proof]
#[kani::unwind(40)]
fn successful_validation_preserves_symbolic_widths() {
    let quantity_atoms: u128 = kani::any();
    let created_epoch: u64 = kani::any();
    let has_expiry: bool = kani::any();
    let expiry_epoch = has_expiry.then_some(created_epoch);
    let mut wire = valid_wire();
    wire.quantity_atoms = quantity_atoms;
    wire.created_epoch = created_epoch;
    wire.expiry_epoch = expiry_epoch;

    match validate_intrinsic_fields(&wire) {
        Ok(fields) => {
            assert_eq!(fields.quantity_atoms.get(), quantity_atoms);
            assert_eq!(fields.created_epoch, created_epoch);
            assert_eq!(fields.expiry_epoch, expiry_epoch);
        }
        Err(_) => assert!(false),
    }
    kani::cover!(has_expiry);
    kani::cover!(!has_expiry);
}

#[kani::proof]
#[kani::unwind(40)]
fn every_nonzero_flag_pattern_preserves_exact_bits() {
    let bits: u32 = kani::any();
    kani::assume(bits != 0);
    let mut wire = valid_wire();
    wire.flags = bits;
    assert_eq!(
        validate_intrinsic_fields(&wire).map(|_| ()),
        Err(IntrinsicResourceErrorV1::UnknownFlags { bits })
    );
    kani::cover!(bits == 1);
    kani::cover!(bits == u32::MAX);
}
