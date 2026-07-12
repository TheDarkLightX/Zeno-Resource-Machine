//! Implementation-side finite atlas for resource-kind quantity and unit validation.

use zrm_policy::{
    AccountingModeV1, DataAvailabilityRequirementV1, PolicyValidationErrorV1,
    ResourceDimensionErrorV1, ResourceKindPolicyCandidateV1, ResourceKindPolicyV1,
};
use zrm_types::{QuantityAtoms, UnitId, ZeroValueError};

#[derive(Clone, Copy, Eq, PartialEq)]
enum UnitRelation {
    Matching,
    Mismatched,
}

fn nonzero<T>(byte: u8) -> Result<T, ZeroValueError>
where
    T: TryFrom<[u8; 32], Error = ZeroValueError>,
{
    T::try_from([byte; 32])
}

fn policy_candidate(
    accounting_mode: AccountingModeV1,
    quantity_maximum: u128,
) -> Result<ResourceKindPolicyCandidateV1, ZeroValueError> {
    Ok(ResourceKindPolicyCandidateV1 {
        schema_version: 1,
        policy_id: nonzero(1)?,
        machine_id: nonzero(2)?,
        domain_id: nonzero(3)?,
        application_id: nonzero(4)?,
        resource_kind_id: nonzero(5)?,
        unit_id: nonzero(6)?,
        accounting_mode,
        quantity_max: QuantityAtoms::new(quantity_maximum),
        allowed_logic_set_root: nonzero(7)?,
        allowed_logic_profile_set_root: nonzero(8)?,
        allowed_transformation_set_root: nonzero(9)?,
        controller_policy_root: nonzero(10)?,
        mint_authority_root: nonzero(11)?,
        burn_authority_root: nonzero(12)?,
        data_availability: DataAvailabilityRequirementV1::Optional,
        validity_start_epoch: 10,
        validity_end_epoch: 20,
    })
}

fn accounting_modes() -> [AccountingModeV1; 5] {
    [
        AccountingModeV1::ConservedFungible,
        AccountingModeV1::AuthorityMintableFungible,
        AccountingModeV1::LifecycleNonFungible,
        AccountingModeV1::Transformable,
        AccountingModeV1::EvidenceOnly,
    ]
}

fn expected_dimension_result(
    accounting_mode: AccountingModeV1,
    unit_relation: UnitRelation,
    quantity: u128,
    quantity_maximum: u128,
) -> Result<(), ResourceDimensionErrorV1> {
    if unit_relation == UnitRelation::Mismatched {
        return Err(ResourceDimensionErrorV1::UnitMismatch);
    }
    if accounting_mode == AccountingModeV1::LifecycleNonFungible && quantity != 1 {
        return Err(ResourceDimensionErrorV1::LifecycleQuantityMustBeOne { actual: quantity });
    }
    if quantity == 0 {
        return Err(ResourceDimensionErrorV1::ZeroQuantityForbidden);
    }
    if quantity > quantity_maximum {
        return Err(ResourceDimensionErrorV1::QuantityExceedsMaximum {
            actual: quantity,
            maximum: quantity_maximum,
        });
    }
    Ok(())
}

fn actual_unit(expected: UnitId, unit_relation: UnitRelation) -> Result<UnitId, ZeroValueError> {
    match unit_relation {
        UnitRelation::Matching => Ok(expected),
        UnitRelation::Mismatched => nonzero(250),
    }
}

#[test]
fn resource_dimension_boundary_atlas_matches_explicit_predicate() -> Result<(), ZeroValueError> {
    let maxima = [0, 1, 2, u128::MAX];

    for accounting_mode in accounting_modes() {
        for quantity_maximum in maxima {
            assert_constructor_case(accounting_mode, quantity_maximum)?;
        }
    }
    Ok(())
}

fn assert_constructor_case(
    accounting_mode: AccountingModeV1,
    quantity_maximum: u128,
) -> Result<(), ZeroValueError> {
    let candidate = policy_candidate(accounting_mode, quantity_maximum)?;
    let construction = ResourceKindPolicyV1::try_from(candidate);
    if accounting_mode == AccountingModeV1::LifecycleNonFungible && quantity_maximum != 1 {
        assert_eq!(
            construction,
            Err(PolicyValidationErrorV1::LifecycleQuantityMaximumMustBeOne {
                actual: quantity_maximum,
            })
        );
        return Ok(());
    }

    assert!(construction.is_ok());
    if let Ok(policy) = construction {
        assert_eq!(policy.as_candidate(), candidate);
        return assert_policy_dimension_cases(
            &policy,
            &candidate,
            accounting_mode,
            quantity_maximum,
        );
    }
    Ok(())
}

fn assert_policy_dimension_cases(
    policy: &ResourceKindPolicyV1,
    candidate: &ResourceKindPolicyCandidateV1,
    accounting_mode: AccountingModeV1,
    quantity_maximum: u128,
) -> Result<(), ZeroValueError> {
    for unit_relation in [UnitRelation::Mismatched, UnitRelation::Matching] {
        for quantity in [0, 1, 2, quantity_maximum, u128::MAX] {
            let unit_id = actual_unit(candidate.unit_id, unit_relation)?;
            let expected = expected_dimension_result(
                accounting_mode,
                unit_relation,
                quantity,
                quantity_maximum,
            );
            let first = policy.validate_dimensions(unit_id, QuantityAtoms::new(quantity));
            let second = policy.validate_dimensions(unit_id, QuantityAtoms::new(quantity));
            assert_eq!(first, expected);
            assert_eq!(second, expected);
        }
    }
    Ok(())
}

#[test]
fn evidence_only_does_not_imply_zero_quantity_marker_permission() -> Result<(), ZeroValueError> {
    // ZRM01-MUT-ZERO-GUARD-OMIT: removing the general zero guard must fail here.
    let candidate = policy_candidate(AccountingModeV1::EvidenceOnly, 1)?;
    let policy = ResourceKindPolicyV1::try_from(candidate);
    assert!(policy.is_ok());
    if let Ok(policy) = policy {
        assert_eq!(
            policy.validate_dimensions(candidate.unit_id, QuantityAtoms::new(0)),
            Err(ResourceDimensionErrorV1::ZeroQuantityForbidden)
        );
    }
    Ok(())
}

#[test]
fn resource_dimension_reject_precedence_is_unit_lifecycle_zero_then_maximum()
-> Result<(), ZeroValueError> {
    let lifecycle_candidate = policy_candidate(AccountingModeV1::LifecycleNonFungible, 1)?;
    let lifecycle = ResourceKindPolicyV1::try_from(lifecycle_candidate);
    assert!(lifecycle.is_ok());
    if let Ok(lifecycle) = lifecycle {
        assert_eq!(
            lifecycle.validate_dimensions(nonzero(250)?, QuantityAtoms::new(0)),
            Err(ResourceDimensionErrorV1::UnitMismatch)
        );
        assert_eq!(
            lifecycle.validate_dimensions(lifecycle_candidate.unit_id, QuantityAtoms::new(0)),
            Err(ResourceDimensionErrorV1::LifecycleQuantityMustBeOne { actual: 0 })
        );
    }

    let fungible_candidate = policy_candidate(AccountingModeV1::ConservedFungible, 1)?;
    let fungible = ResourceKindPolicyV1::try_from(fungible_candidate);
    assert!(fungible.is_ok());
    if let Ok(fungible) = fungible {
        assert_eq!(
            fungible.validate_dimensions(fungible_candidate.unit_id, QuantityAtoms::new(0)),
            Err(ResourceDimensionErrorV1::ZeroQuantityForbidden)
        );
        assert_eq!(
            fungible.validate_dimensions(fungible_candidate.unit_id, QuantityAtoms::new(2)),
            Err(ResourceDimensionErrorV1::QuantityExceedsMaximum {
                actual: 2,
                maximum: 1,
            })
        );
    }
    Ok(())
}
