//! Version-one resource-kind policy and dimension checks.

#[cfg(kani)]
mod kani_harnesses;

use zrm_types::{
    AllowedLogicProfileSetRoot, AllowedLogicSetRoot, AllowedTransformationSetRoot, ApplicationId,
    BurnAuthorityRoot, ControllerPolicyRoot, DomainId, MachineId, MintAuthorityRoot, PolicyId,
    QuantityAtoms, ResourceKindId, UnitId,
};

use crate::{
    POLICY_SCHEMA_VERSION_V1, PolicyObjectV1, PolicyValidationErrorV1, ResourceDimensionErrorV1,
    ValidityWindowV1,
};

/// Closed accounting mode selected by resource-kind policy.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AccountingModeV1 {
    /// Same-kind fungible quantities must conserve without mint or burn.
    ConservedFungible,
    /// Fungible mint or burn requires explicit governed authority.
    AuthorityMintableFungible,
    /// Lifecycle object with quantity fixed to one.
    LifecycleNonFungible,
    /// Cross-kind unmatched deltas require an allowed transformation.
    Transformable,
    /// Evidence resource without implicit monetary semantics.
    EvidenceOnly,
}

/// Whether resource-kind policy requires authenticated data availability.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum DataAvailabilityRequirementV1 {
    /// Data availability is not required by this local policy value.
    Optional,
    /// A later verifier boundary must authenticate data availability.
    Required,
}

/// Public, non-authoritative logical resource-kind-policy candidate.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ResourceKindPolicyCandidateV1 {
    /// Candidate logical schema version.
    pub schema_version: u16,
    /// Externally governed policy identifier.
    pub policy_id: PolicyId,
    /// Machine identity.
    pub machine_id: MachineId,
    /// Replay and authority domain.
    pub domain_id: DomainId,
    /// Application identity.
    pub application_id: ApplicationId,
    /// Governed resource-kind identity.
    pub resource_kind_id: ResourceKindId,
    /// Exact opaque unit required for this resource kind.
    pub unit_id: UnitId,
    /// Policy-selected accounting mode.
    pub accounting_mode: AccountingModeV1,
    /// Maximum nonnegative atom count.
    pub quantity_max: QuantityAtoms,
    /// Root of allowed resource logics.
    pub allowed_logic_set_root: AllowedLogicSetRoot,
    /// Root of allowed logic profiles.
    pub allowed_logic_profile_set_root: AllowedLogicProfileSetRoot,
    /// Root of allowed transformation rules.
    pub allowed_transformation_set_root: AllowedTransformationSetRoot,
    /// Root of controller policy.
    pub controller_policy_root: ControllerPolicyRoot,
    /// Root of governed mint authority.
    pub mint_authority_root: MintAuthorityRoot,
    /// Root of governed burn authority.
    pub burn_authority_root: BurnAuthorityRoot,
    /// Data-availability requirement.
    pub data_availability: DataAvailabilityRequirementV1,
    /// Inclusive first valid logical epoch.
    pub validity_start_epoch: u64,
    /// Inclusive final valid logical epoch.
    pub validity_end_epoch: u64,
}

/// Locally validated version-one logical resource-kind policy.
///
/// Opaque roots remain unauthenticated data until later set-membership and
/// verifier boundaries check them. This type does not authorize mint, burn,
/// transformation, controller action, or data availability.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ResourceKindPolicyV1 {
    candidate: ResourceKindPolicyCandidateV1,
    validity: ValidityWindowV1,
}

impl ResourceKindPolicyV1 {
    /// Returns the exact unit required by this policy.
    #[must_use]
    pub const fn unit_id(&self) -> UnitId {
        self.candidate.unit_id
    }

    /// Returns the policy's maximum quantity.
    #[must_use]
    pub const fn quantity_max(&self) -> QuantityAtoms {
        self.candidate.quantity_max
    }

    /// Returns the closed accounting mode.
    #[must_use]
    pub const fn accounting_mode(&self) -> AccountingModeV1 {
        self.candidate.accounting_mode
    }

    /// Returns whether the inclusive validity window contains `epoch`.
    #[must_use]
    pub const fn is_valid_at(&self, epoch: u64) -> bool {
        self.validity.contains(epoch)
    }

    /// Checks one resource's exact unit and quantity constraints.
    ///
    /// Unit mismatch is selected first. Lifecycle non-fungibles then require
    /// exactly one atom. Every other zero quantity rejects because this schema
    /// has no explicit marker-resource permission. The general quantity
    /// maximum is checked last. No conversion, rounding, floating point, or
    /// arithmetic across different units occurs.
    ///
    /// # Errors
    ///
    /// Returns the first typed dimension error in the order above.
    pub fn validate_dimensions(
        &self,
        unit_id: UnitId,
        quantity: QuantityAtoms,
    ) -> Result<(), ResourceDimensionErrorV1> {
        if unit_id != self.candidate.unit_id {
            return Err(ResourceDimensionErrorV1::UnitMismatch);
        }
        if self.candidate.accounting_mode == AccountingModeV1::LifecycleNonFungible
            && quantity.get() != 1
        {
            return Err(ResourceDimensionErrorV1::LifecycleQuantityMustBeOne {
                actual: quantity.get(),
            });
        }
        if quantity.get() == 0 {
            return Err(ResourceDimensionErrorV1::ZeroQuantityForbidden);
        }
        if quantity > self.candidate.quantity_max {
            return Err(ResourceDimensionErrorV1::QuantityExceedsMaximum {
                actual: quantity.get(),
                maximum: self.candidate.quantity_max.get(),
            });
        }
        Ok(())
    }

    /// Returns a copy of the validated logical data.
    ///
    /// The returned candidate carries no governance or verifier authority.
    #[must_use]
    pub const fn as_candidate(&self) -> ResourceKindPolicyCandidateV1 {
        self.candidate
    }
}

impl TryFrom<ResourceKindPolicyCandidateV1> for ResourceKindPolicyV1 {
    type Error = PolicyValidationErrorV1;

    /// Validates schema, inclusive validity, and accounting-mode invariants.
    ///
    /// # Errors
    ///
    /// Returns the first local policy error in the order above.
    fn try_from(candidate: ResourceKindPolicyCandidateV1) -> Result<Self, Self::Error> {
        if candidate.schema_version != POLICY_SCHEMA_VERSION_V1 {
            return Err(PolicyValidationErrorV1::UnsupportedSchemaVersion {
                object: PolicyObjectV1::ResourceKindPolicy,
                actual: candidate.schema_version,
            });
        }
        let validity = ValidityWindowV1::try_new(
            PolicyObjectV1::ResourceKindPolicy,
            candidate.validity_start_epoch,
            candidate.validity_end_epoch,
        )?;
        if candidate.accounting_mode == AccountingModeV1::LifecycleNonFungible
            && candidate.quantity_max.get() != 1
        {
            return Err(PolicyValidationErrorV1::LifecycleQuantityMaximumMustBeOne {
                actual: candidate.quantity_max.get(),
            });
        }
        Ok(Self {
            candidate,
            validity,
        })
    }
}
