#![no_main]

use libfuzzer_sys::fuzz_target;
use zrm_policy::{
    AccountingModeV1, DataAvailabilityRequirementV1, PolicyValidationErrorV1,
    ResourceDimensionErrorV1, ResourceKindPolicyCandidateV1, ResourceKindPolicyV1,
};
use zrm_types::{QuantityAtoms, UnitId};

const REQUIRED_BYTES: usize = 34;

#[derive(Clone, Copy, Eq, PartialEq)]
enum UnitRelation {
    Matching,
    Mismatched,
}

fn read_u128(data: &[u8], offset: usize) -> Option<u128> {
    let end = offset.checked_add(16)?;
    let bytes: [u8; 16] = data.get(offset..end)?.try_into().ok()?;
    Some(u128::from_be_bytes(bytes))
}

fn nonzero<T>(byte: u8) -> Option<T>
where
    T: TryFrom<[u8; 32]>,
{
    T::try_from([byte; 32]).ok()
}

fn accounting_mode(selector: u8) -> AccountingModeV1 {
    match selector % 5 {
        0 => AccountingModeV1::ConservedFungible,
        1 => AccountingModeV1::AuthorityMintableFungible,
        2 => AccountingModeV1::LifecycleNonFungible,
        3 => AccountingModeV1::Transformable,
        _ => AccountingModeV1::EvidenceOnly,
    }
}

fn policy_candidate(
    accounting_mode: AccountingModeV1,
    quantity_maximum: u128,
) -> Option<ResourceKindPolicyCandidateV1> {
    Some(ResourceKindPolicyCandidateV1 {
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
        validity_start_epoch: 0,
        validity_end_epoch: u64::MAX,
    })
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

fuzz_target!(|data: &[u8]| {
    if data.len() < REQUIRED_BYTES {
        return;
    }
    let accounting_mode = accounting_mode(data[0]);
    let unit_relation = if data[1] & 1 == 0 {
        UnitRelation::Matching
    } else {
        UnitRelation::Mismatched
    };
    let Some(quantity) = read_u128(data, 2) else {
        return;
    };
    let Some(quantity_maximum) = read_u128(data, 18) else {
        return;
    };
    let Some(candidate) = policy_candidate(accounting_mode, quantity_maximum) else {
        return;
    };

    let construction = ResourceKindPolicyV1::try_from(candidate);
    if accounting_mode == AccountingModeV1::LifecycleNonFungible && quantity_maximum != 1 {
        assert_eq!(
            construction,
            Err(PolicyValidationErrorV1::LifecycleQuantityMaximumMustBeOne {
                actual: quantity_maximum,
            })
        );
        return;
    }
    assert!(construction.is_ok());
    let Ok(policy) = construction else {
        return;
    };

    let unit_id = match unit_relation {
        UnitRelation::Matching => candidate.unit_id,
        UnitRelation::Mismatched => {
            let Some(unit_id) = nonzero::<UnitId>(250) else {
                return;
            };
            unit_id
        }
    };
    let expected =
        expected_dimension_result(accounting_mode, unit_relation, quantity, quantity_maximum);
    let first = policy.validate_dimensions(unit_id, QuantityAtoms::new(quantity));
    let second = policy.validate_dimensions(unit_id, QuantityAtoms::new(quantity));
    assert_eq!(first, expected);
    assert_eq!(second, expected);
});
