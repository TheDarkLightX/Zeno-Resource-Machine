use super::{
    AccountingModeV1, DataAvailabilityRequirementV1, ResourceKindPolicyCandidateV1,
    ResourceKindPolicyV1,
};
use crate::{PolicyValidationErrorV1, ResourceDimensionErrorV1};
use zrm_types::{
    AllowedLogicProfileSetRoot, AllowedLogicSetRoot, AllowedTransformationSetRoot, ApplicationId,
    BurnAuthorityRoot, ControllerPolicyRoot, DomainId, MachineId, MintAuthorityRoot, PolicyId,
    QuantityAtoms, ResourceKindId, UnitId,
};

#[derive(Clone, Copy, Eq, PartialEq)]
enum UnitRelation {
    Matching,
    Mismatched,
}

fn nonzero<T>(byte: u8) -> T
where
    T: TryFrom<[u8; 32]>,
    <T as TryFrom<[u8; 32]>>::Error: core::fmt::Debug,
{
    T::try_from([byte; 32]).expect("fixed Kani identifier fixture is nonzero")
}

fn accounting_mode(selector: u8) -> AccountingModeV1 {
    match selector {
        0 => AccountingModeV1::ConservedFungible,
        1 => AccountingModeV1::AuthorityMintableFungible,
        2 => AccountingModeV1::LifecycleNonFungible,
        3 => AccountingModeV1::Transformable,
        _ => AccountingModeV1::EvidenceOnly,
    }
}

fn candidate(
    accounting_mode: AccountingModeV1,
    quantity_maximum: u128,
) -> ResourceKindPolicyCandidateV1 {
    ResourceKindPolicyCandidateV1 {
        schema_version: 1,
        policy_id: nonzero::<PolicyId>(1),
        machine_id: nonzero::<MachineId>(2),
        domain_id: nonzero::<DomainId>(3),
        application_id: nonzero::<ApplicationId>(4),
        resource_kind_id: nonzero::<ResourceKindId>(5),
        unit_id: nonzero::<UnitId>(6),
        accounting_mode,
        quantity_max: QuantityAtoms::new(quantity_maximum),
        allowed_logic_set_root: nonzero::<AllowedLogicSetRoot>(7),
        allowed_logic_profile_set_root: nonzero::<AllowedLogicProfileSetRoot>(8),
        allowed_transformation_set_root: nonzero::<AllowedTransformationSetRoot>(9),
        controller_policy_root: nonzero::<ControllerPolicyRoot>(10),
        mint_authority_root: nonzero::<MintAuthorityRoot>(11),
        burn_authority_root: nonzero::<BurnAuthorityRoot>(12),
        data_availability: DataAvailabilityRequirementV1::Optional,
        validity_start_epoch: 0,
        validity_end_epoch: u64::MAX,
    }
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

#[kani::proof]
fn lifecycle_policy_construction_accepts_exactly_maximum_one() {
    let selector: u8 = kani::any();
    kani::assume(selector < 5);
    let accounting_mode = accounting_mode(selector);
    let quantity_maximum: u128 = kani::any();
    let result = ResourceKindPolicyV1::try_from(candidate(accounting_mode, quantity_maximum));
    let expected =
        accounting_mode != AccountingModeV1::LifecycleNonFungible || quantity_maximum == 1;
    assert_eq!(result.is_ok(), expected);
    if !expected {
        assert_eq!(
            result,
            Err(PolicyValidationErrorV1::LifecycleQuantityMaximumMustBeOne {
                actual: quantity_maximum,
            })
        );
    }
    kani::cover!(result.is_ok());
    kani::cover!(result.is_err());
}

#[kani::proof]
fn full_width_resource_dimensions_match_the_explicit_predicate() {
    let selector: u8 = kani::any();
    kani::assume(selector < 5);
    let accounting_mode = accounting_mode(selector);
    let quantity_maximum: u128 = kani::any();
    if accounting_mode == AccountingModeV1::LifecycleNonFungible {
        kani::assume(quantity_maximum == 1);
    }
    let candidate = candidate(accounting_mode, quantity_maximum);
    let policy = ResourceKindPolicyV1::try_from(candidate);
    assert!(policy.is_ok());
    let Ok(policy) = policy else {
        return;
    };

    let quantity: u128 = kani::any();
    let unit_relation = if kani::any() {
        UnitRelation::Matching
    } else {
        UnitRelation::Mismatched
    };
    let unit_id = match unit_relation {
        UnitRelation::Matching => candidate.unit_id,
        UnitRelation::Mismatched => nonzero::<UnitId>(250),
    };
    let result = policy.validate_dimensions(unit_id, QuantityAtoms::new(quantity));
    let expected =
        expected_dimension_result(accounting_mode, unit_relation, quantity, quantity_maximum);
    assert_eq!(result, expected);
    cover_dimension_results(result);
}

fn cover_dimension_results(result: Result<(), ResourceDimensionErrorV1>) {
    kani::cover!(result.is_ok());
    kani::cover!(matches!(
        result,
        Err(ResourceDimensionErrorV1::UnitMismatch)
    ));
    kani::cover!(matches!(
        result,
        Err(ResourceDimensionErrorV1::LifecycleQuantityMustBeOne { .. })
    ));
    kani::cover!(matches!(
        result,
        Err(ResourceDimensionErrorV1::ZeroQuantityForbidden)
    ));
    kani::cover!(matches!(
        result,
        Err(ResourceDimensionErrorV1::QuantityExceedsMaximum { .. })
    ));
}
