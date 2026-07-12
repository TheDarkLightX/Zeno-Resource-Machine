//! Unit tests for exceptional local construction paths.

use super::{IntrinsicResourceErrorV1, IntrinsicResourceFieldV1, construct_intrinsic_resource};
use zrm_codec::{ResourceIdDerivationError, ResourceWireEncodeError, ResourceWireV1};

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
        quantity_atoms: 9,
        label_root: [10; 32],
        value_root: [11; 32],
        controller_root: [12; 32],
        policy_root: [13; 32],
        provenance_root: [14; 32],
        nonce: [15; 32],
        created_epoch: 16,
        expiry_epoch: Some(17),
        flags: 0,
    }
}

#[test]
fn deterministic_semantic_reject_precedes_injected_derivation_failure() {
    let mut wire = valid_wire();
    wire.machine_id = [0; 32];
    let actual = construct_intrinsic_resource(&wire, |_| {
        Err(ResourceIdDerivationError::Encode(
            ResourceWireEncodeError::AllocationFailed,
        ))
    });
    assert_eq!(
        actual,
        Err(IntrinsicResourceErrorV1::ZeroField {
            field: IntrinsicResourceFieldV1::MachineId,
        })
    );
}

#[test]
fn derivation_failure_is_typed_after_intrinsic_success() {
    let source = ResourceIdDerivationError::Encode(ResourceWireEncodeError::AllocationFailed);
    let wire = valid_wire();
    let actual = construct_intrinsic_resource(&wire, |_| Err(source));
    assert_eq!(
        actual,
        Err(IntrinsicResourceErrorV1::ResourceIdDerivation(source))
    );
}

fn assert_zero_field_diagnostics() {
    let fields = [
        (IntrinsicResourceFieldV1::MachineId, "machine_id"),
        (IntrinsicResourceFieldV1::DomainId, "domain_id"),
        (IntrinsicResourceFieldV1::ApplicationId, "application_id"),
        (IntrinsicResourceFieldV1::ResourceKindId, "resource_kind_id"),
        (
            IntrinsicResourceFieldV1::ResourceLogicId,
            "resource_logic_id",
        ),
        (IntrinsicResourceFieldV1::LogicProfileId, "logic_profile_id"),
        (
            IntrinsicResourceFieldV1::ResourceKindPolicyId,
            "resource_kind_policy_id",
        ),
        (IntrinsicResourceFieldV1::UnitId, "unit_id"),
        (IntrinsicResourceFieldV1::LabelRoot, "label_root"),
        (IntrinsicResourceFieldV1::ValueRoot, "value_root"),
        (IntrinsicResourceFieldV1::ControllerRoot, "controller_root"),
        (IntrinsicResourceFieldV1::PolicyRoot, "policy_root"),
        (IntrinsicResourceFieldV1::ProvenanceRoot, "provenance_root"),
        (IntrinsicResourceFieldV1::Nonce, "nonce"),
    ];
    for (field, label) in fields {
        assert_eq!(
            std::format!("{}", IntrinsicResourceErrorV1::ZeroField { field }),
            std::format!("zero intrinsic resource field: {label}")
        );
    }
}

#[test]
fn every_local_error_has_a_bounded_diagnostic() {
    assert_zero_field_diagnostics();
    assert_eq!(
        std::format!(
            "{}",
            IntrinsicResourceErrorV1::ExpiryBeforeCreation {
                created_epoch: 2,
                expiry_epoch: 1,
            }
        ),
        "resource expiry precedes creation"
    );
    assert_eq!(
        std::format!(
            "{}",
            IntrinsicResourceErrorV1::UnknownFlags { bits: 0x8000_0001 }
        ),
        "unknown ResourceFlagsV1 bits: 0x80000001"
    );
    assert_eq!(
        std::format!(
            "{}",
            IntrinsicResourceErrorV1::ResourceIdDerivation(ResourceIdDerivationError::Encode(
                ResourceWireEncodeError::LengthOverflow
            ))
        ),
        "resource ID derivation failed: resource encoding failed: canonical resource field length overflow"
    );
}
