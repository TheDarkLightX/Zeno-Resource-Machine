//! Deterministic verifier-cost validation and local quote calculation.
//!
//! This module implements only the pre-RFC in-memory arithmetic from the
//! normative logical policy schema. It defines no canonical bytes, hashes,
//! registry authority, verifier dispatch, or verified-fact capability.

use core::fmt;

use zrm_types::{BackendFamilyId, VerifierCostRowsRoot};

use crate::VerifierPolicyV1;

/// The only verifier-cost-model schema version supported by this pre-RFC API.
pub const VERIFIER_COST_MODEL_SCHEMA_V1: u16 = 1;

/// Public, non-authoritative candidate for one verifier-cost row.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct VerifierCostRowCandidateV1 {
    /// Backend family covered by this row.
    pub backend_family_id: BackendFamilyId,
    /// Fixed units charged for every dispatch.
    pub base_units: u64,
    /// Units charged per exact artifact byte.
    pub artifact_byte_units: u64,
    /// Units charged per canonical statement byte.
    pub statement_byte_units: u64,
    /// Units charged per reserved public-output byte.
    pub reserved_output_byte_units: u64,
}

/// One locally checked verifier-cost-row value.
///
/// The private fields prevent callers from changing a validated row after it
/// enters local quote calculation. Coefficients are nonnegative fixed-width values;
/// zero is permitted. Construction performs no allocation, I/O, or authority
/// transition and is constant time and panic-free.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct VerifierCostRowV1 {
    backend_family_id: BackendFamilyId,
    base_units: u64,
    artifact_byte_units: u64,
    statement_byte_units: u64,
    reserved_output_byte_units: u64,
}

impl VerifierCostRowV1 {
    /// Creates one inert, candidate-selected cost-row value.
    ///
    /// The backend identifier has already enforced its local nonzero
    /// representation invariant. This constructor performs no hashing,
    /// registration, allocation, or verifier dispatch.
    #[must_use]
    pub const fn new(candidate: VerifierCostRowCandidateV1) -> Self {
        Self {
            backend_family_id: candidate.backend_family_id,
            base_units: candidate.base_units,
            artifact_byte_units: candidate.artifact_byte_units,
            statement_byte_units: candidate.statement_byte_units,
            reserved_output_byte_units: candidate.reserved_output_byte_units,
        }
    }

    /// Returns the backend family selected by this row.
    #[must_use]
    pub const fn backend_family_id(&self) -> BackendFamilyId {
        self.backend_family_id
    }

    /// Returns the fixed charge applied to every verification attempt.
    #[must_use]
    pub const fn base_units(&self) -> u64 {
        self.base_units
    }

    /// Returns the charge per exact artifact byte.
    #[must_use]
    pub const fn artifact_byte_units(&self) -> u64 {
        self.artifact_byte_units
    }

    /// Returns the charge per canonical statement byte.
    #[must_use]
    pub const fn statement_byte_units(&self) -> u64 {
        self.statement_byte_units
    }

    /// Returns the charge per reserved public-output byte.
    #[must_use]
    pub const fn reserved_output_byte_units(&self) -> u64 {
        self.reserved_output_byte_units
    }
}

/// Public, non-authoritative candidate for a verifier cost model.
///
/// Conversion validates only the supported schema version. This pre-RFC module
/// establishes no row encoding, ordering, root derivation, or authentication.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct VerifierCostModelCandidateV1 {
    /// Candidate schema version. Version one is the only supported value.
    pub schema_version: u16,
    /// Opaque future cost-row-root candidate.
    pub rows_root: VerifierCostRowsRoot,
    /// Maximum charge allowed for any one row under this model.
    pub max_charge_units: u64,
}

/// Validated in-memory verifier cost model.
///
/// The value establishes local schema-version consistency only. It is not a
/// policy hash, registry capability, or proof that the rows root is governed.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct VerifierCostModelV1 {
    schema_version: u16,
    rows_root: VerifierCostRowsRoot,
    max_charge_units: u64,
}

impl VerifierCostModelV1 {
    /// Returns the validated schema version.
    #[must_use]
    pub const fn schema_version(&self) -> u16 {
        self.schema_version
    }

    /// Returns the opaque rows-root candidate.
    #[must_use]
    pub const fn rows_root(&self) -> VerifierCostRowsRoot {
        self.rows_root
    }

    /// Returns this model's per-verification charge cap.
    #[must_use]
    pub const fn max_charge_units(&self) -> u64 {
        self.max_charge_units
    }

    /// Computes one deterministic local verifier-cost quote.
    ///
    /// Validation order is stable: backend-family equality, artifact bound,
    /// statement bound, checked `u128` arithmetic, `u64` fit, model cap, then
    /// per-verifier cap. Byte-bound failures therefore occur before any cost
    /// arithmetic. The four charged terms are the base, exact artifact bytes,
    /// exact canonical statement bytes, and reserved output maximum.
    ///
    /// # Errors
    ///
    /// Returns a typed [`VerifierCostErrorV1`] for the first failed check in the
    /// order above.
    ///
    /// # Panics
    ///
    /// This function does not panic.
    ///
    /// # Side effects and complexity
    ///
    /// The calculation is allocation-free, deterministic, side-effect-free,
    /// and constant time in input size.
    pub fn compute_quote(
        &self,
        row: &VerifierCostRowV1,
        request: &VerifierCostQuoteRequestV1,
    ) -> Result<VerifierCostQuoteV1, VerifierCostErrorV1> {
        if row.backend_family_id != request.expected_backend_family_id {
            return Err(VerifierCostErrorV1::BackendFamilyMismatch);
        }
        if request.artifact_len > request.max_artifact_bytes {
            return Err(VerifierCostErrorV1::ArtifactBytesExceeded);
        }
        if request.canonical_statement_len > request.max_public_input_bytes {
            return Err(VerifierCostErrorV1::PublicInputBytesExceeded);
        }

        let mut charge = 0_u128;
        charge = checked_add(charge, u128::from(row.base_units))?;
        charge = checked_add(
            charge,
            checked_multiply(row.artifact_byte_units, request.artifact_len)?,
        )?;
        charge = checked_add(
            charge,
            checked_multiply(row.statement_byte_units, request.canonical_statement_len)?,
        )?;
        charge = checked_add(
            charge,
            checked_multiply(
                row.reserved_output_byte_units,
                request.reserved_output_byte_maximum,
            )?,
        )?;

        let units = u64::try_from(charge).map_err(|_| VerifierCostErrorV1::ChargeDoesNotFitU64)?;
        if units > self.max_charge_units {
            return Err(VerifierCostErrorV1::ModelChargeLimitExceeded);
        }
        if units > request.max_verifier_cost_units {
            return Err(VerifierCostErrorV1::VerifierChargeLimitExceeded);
        }
        Ok(VerifierCostQuoteV1 { units })
    }
}

impl TryFrom<VerifierCostModelCandidateV1> for VerifierCostModelV1 {
    type Error = VerifierCostErrorV1;

    /// Validates the supported in-memory verifier-cost-model version.
    ///
    /// # Errors
    ///
    /// Returns [`VerifierCostErrorV1::UnsupportedModelSchema`] unless the
    /// candidate declares schema version one.
    fn try_from(candidate: VerifierCostModelCandidateV1) -> Result<Self, Self::Error> {
        if candidate.schema_version != VERIFIER_COST_MODEL_SCHEMA_V1 {
            return Err(VerifierCostErrorV1::UnsupportedModelSchema);
        }
        Ok(Self {
            schema_version: candidate.schema_version,
            rows_root: candidate.rows_root,
            max_charge_units: candidate.max_charge_units,
        })
    }
}

/// Policy-derived inputs for one deterministic verifier-cost quote.
///
/// Callers may choose only the two actual byte lengths. The backend family,
/// candidate maxima, reserved output maximum, and per-verifier cap are copied
/// from a locally validated [`VerifierPolicyV1`]. Private fields prevent callers
/// from substituting weaker bounds after construction. The request remains
/// inert data and carries no registry, verifier, or governance authority.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct VerifierCostQuoteRequestV1 {
    /// Backend family copied from the locally validated verifier policy.
    expected_backend_family_id: BackendFamilyId,
    /// Exact bounded artifact byte length presented to the verifier wrapper.
    artifact_len: u64,
    /// Exact canonical statement byte length presented to the wrapper.
    canonical_statement_len: u64,
    /// Verifier-policy maximum artifact byte length.
    max_artifact_bytes: u64,
    /// Verifier-policy maximum canonical public-input byte length.
    max_public_input_bytes: u64,
    /// Verifier-policy maximum output length reserved before dispatch.
    reserved_output_byte_maximum: u64,
    /// Maximum cost permitted by the selected verifier policy.
    max_verifier_cost_units: u64,
}

impl VerifierCostQuoteRequestV1 {
    /// Copies all policy-selected bounds around the two caller-supplied lengths.
    pub(crate) const fn from_policy(
        policy: &VerifierPolicyV1,
        artifact_len: u64,
        canonical_statement_len: u64,
    ) -> Self {
        Self {
            expected_backend_family_id: policy.backend_family_id(),
            artifact_len,
            canonical_statement_len,
            max_artifact_bytes: policy.max_artifact_bytes(),
            max_public_input_bytes: policy.max_public_input_bytes(),
            reserved_output_byte_maximum: policy.max_public_output_bytes(),
            max_verifier_cost_units: policy.max_verifier_cost_units(),
        }
    }

    #[cfg(any(test, kani))]
    const fn from_test_parts(
        expected_backend_family_id: BackendFamilyId,
        lengths: [u64; 2],
        policy_bounds: [u64; 4],
    ) -> Self {
        let [artifact_len, canonical_statement_len] = lengths;
        let [
            max_artifact_bytes,
            max_public_input_bytes,
            reserved_output_byte_maximum,
            max_verifier_cost_units,
        ] = policy_bounds;
        Self {
            expected_backend_family_id,
            artifact_len,
            canonical_statement_len,
            max_artifact_bytes,
            max_public_input_bytes,
            reserved_output_byte_maximum,
            max_verifier_cost_units,
        }
    }

    /// Returns the exact artifact length supplied by the caller.
    #[must_use]
    pub const fn artifact_len(&self) -> u64 {
        self.artifact_len
    }

    /// Returns the exact canonical-statement length supplied by the caller.
    #[must_use]
    pub const fn canonical_statement_len(&self) -> u64 {
        self.canonical_statement_len
    }
}

/// A checked deterministic cost quote for one possible verifier dispatch.
///
/// Private construction ensures the quoted arithmetic passed the bounds copied
/// from one locally validated policy and both local caps. The model, row, and
/// policy are still unauthenticated pre-RFC data, so this value is not a
/// governed charge and carries no verifier, registry, proof, or commit authority.
#[must_use]
#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct VerifierCostQuoteV1 {
    units: u64,
}

impl VerifierCostQuoteV1 {
    /// Returns the checked local quote in the candidate model's cost units.
    #[must_use]
    pub const fn units(self) -> u64 {
        self.units
    }
}

/// Bounded typed failures for verifier-cost validation and calculation.
///
/// Variants intentionally expose no proof, policy, or backend internals. Their
/// labels are local pre-RFC diagnostics, may change before ABI freeze, and do
/// not allocate.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum VerifierCostErrorV1 {
    /// The cost-model candidate uses an unsupported schema version.
    UnsupportedModelSchema,
    /// The selected row belongs to a different backend family.
    BackendFamilyMismatch,
    /// The exact artifact length exceeds its verifier-policy maximum.
    ArtifactBytesExceeded,
    /// The exact canonical statement length exceeds its policy maximum.
    PublicInputBytesExceeded,
    /// Checked `u128` multiplication or addition overflowed.
    ArithmeticOverflow,
    /// The checked `u128` charge does not fit the required `u64` result.
    ChargeDoesNotFitU64,
    /// The quote exceeds the candidate cost model's per-charge cap.
    ModelChargeLimitExceeded,
    /// The charge exceeds the selected verifier policy's cap.
    VerifierChargeLimitExceeded,
}

impl VerifierCostErrorV1 {
    /// Returns a bounded local diagnostic label.
    #[must_use]
    pub const fn label(self) -> &'static str {
        match self {
            Self::UnsupportedModelSchema => "zrm.policy.verifier_cost_model_schema",
            Self::BackendFamilyMismatch => "zrm.policy.verifier_cost_backend_mismatch",
            Self::ArtifactBytesExceeded => "zrm.bounds.verifier_artifact_bytes",
            Self::PublicInputBytesExceeded => "zrm.bounds.verifier_public_input_bytes",
            Self::ArithmeticOverflow => "zrm.policy.verifier_cost_arithmetic_overflow",
            Self::ChargeDoesNotFitU64 => "zrm.policy.verifier_cost_u64_overflow",
            Self::ModelChargeLimitExceeded => "zrm.policy.verifier_cost_model_limit",
            Self::VerifierChargeLimitExceeded => "zrm.policy.verifier_cost_policy_limit",
        }
    }
}

impl fmt::Display for VerifierCostErrorV1 {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.label())
    }
}

fn checked_multiply(coefficient: u64, amount: u64) -> Result<u128, VerifierCostErrorV1> {
    u128::from(coefficient)
        .checked_mul(u128::from(amount))
        .ok_or(VerifierCostErrorV1::ArithmeticOverflow)
}

fn checked_add(left: u128, right: u128) -> Result<u128, VerifierCostErrorV1> {
    left.checked_add(right)
        .ok_or(VerifierCostErrorV1::ArithmeticOverflow)
}

#[cfg(test)]
#[path = "cost/tests.rs"]
mod tests;

#[cfg(kani)]
#[path = "cost/kani_harnesses.rs"]
mod kani_harnesses;
