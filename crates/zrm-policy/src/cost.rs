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
mod tests {
    use super::{
        VERIFIER_COST_MODEL_SCHEMA_V1, VerifierCostErrorV1, VerifierCostModelCandidateV1,
        VerifierCostModelV1, VerifierCostQuoteRequestV1, VerifierCostRowCandidateV1,
        VerifierCostRowV1,
    };
    use zrm_types::{BackendFamilyId, VerifierCostRowsRoot, ZeroValueError};

    #[derive(Debug)]
    enum TestError {
        InvalidFixture,
        Cost,
    }

    impl From<ZeroValueError> for TestError {
        fn from(_: ZeroValueError) -> Self {
            Self::InvalidFixture
        }
    }

    impl From<VerifierCostErrorV1> for TestError {
        fn from(_: VerifierCostErrorV1) -> Self {
            Self::Cost
        }
    }

    fn backend(byte: u8) -> Result<BackendFamilyId, TestError> {
        BackendFamilyId::try_from([byte; 32]).map_err(TestError::from)
    }

    fn model(max_charge_units: u64) -> Result<VerifierCostModelV1, TestError> {
        let candidate = VerifierCostModelCandidateV1 {
            schema_version: VERIFIER_COST_MODEL_SCHEMA_V1,
            rows_root: VerifierCostRowsRoot::try_from([0x51; 32])?,
            max_charge_units,
        };
        VerifierCostModelV1::try_from(candidate).map_err(TestError::from)
    }

    fn row(backend_family_id: BackendFamilyId, coefficients: [u64; 4]) -> VerifierCostRowV1 {
        let [
            base_units,
            artifact_byte_units,
            statement_byte_units,
            reserved_output_byte_units,
        ] = coefficients;
        VerifierCostRowV1::new(VerifierCostRowCandidateV1 {
            backend_family_id,
            base_units,
            artifact_byte_units,
            statement_byte_units,
            reserved_output_byte_units,
        })
    }

    fn request(
        expected_backend_family_id: BackendFamilyId,
        lengths: [u64; 3],
        max_verifier_cost_units: u64,
    ) -> VerifierCostQuoteRequestV1 {
        let [
            artifact_len,
            canonical_statement_len,
            reserved_output_byte_maximum,
        ] = lengths;
        VerifierCostQuoteRequestV1::from_test_parts(
            expected_backend_family_id,
            [artifact_len, canonical_statement_len],
            [
                artifact_len,
                canonical_statement_len,
                reserved_output_byte_maximum,
                max_verifier_cost_units,
            ],
        )
    }

    #[test]
    fn model_candidate_accepts_only_schema_version_one() -> Result<(), TestError> {
        let rows_root = VerifierCostRowsRoot::try_from([0x51; 32])?;
        let supported = VerifierCostModelV1::try_from(VerifierCostModelCandidateV1 {
            schema_version: 1,
            rows_root,
            max_charge_units: 99,
        })?;
        assert_eq!(supported.schema_version(), 1);
        assert_eq!(supported.rows_root(), rows_root);
        assert_eq!(supported.max_charge_units(), 99);

        let unsupported = VerifierCostModelV1::try_from(VerifierCostModelCandidateV1 {
            schema_version: 2,
            rows_root,
            max_charge_units: 99,
        });
        assert_eq!(
            unsupported,
            Err(VerifierCostErrorV1::UnsupportedModelSchema)
        );
        Ok(())
    }

    #[test]
    fn charge_includes_each_of_the_four_terms() -> Result<(), TestError> {
        let backend = backend(1)?;
        let model = model(u64::MAX)?;
        let cases = [
            (row(backend, [7, 0, 0, 0]), 7),
            (row(backend, [0, 3, 0, 0]), 12),
            (row(backend, [0, 0, 3, 0]), 15),
            (row(backend, [0, 0, 0, 3]), 18),
        ];
        let charge_request = request(backend, [4, 5, 6], u64::MAX);
        for (row, expected) in cases {
            assert_eq!(
                model.compute_quote(&row, &charge_request)?.units(),
                expected
            );
        }
        let all_terms = row(backend, [7, 3, 3, 3]);
        assert_eq!(
            model.compute_quote(&all_terms, &charge_request)?.units(),
            52
        );
        Ok(())
    }

    #[test]
    fn cost_row_getters_preserve_every_candidate_coefficient() -> Result<(), TestError> {
        let backend = backend(1)?;
        let row = row(backend, [7, 3, 5, 11]);
        assert_eq!(row.backend_family_id(), backend);
        assert_eq!(row.base_units(), 7);
        assert_eq!(row.artifact_byte_units(), 3);
        assert_eq!(row.statement_byte_units(), 5);
        assert_eq!(row.reserved_output_byte_units(), 11);
        Ok(())
    }

    #[test]
    fn backend_mismatch_precedes_byte_bounds_and_arithmetic() -> Result<(), TestError> {
        let row_backend = backend(1)?;
        let expected_backend = backend(2)?;
        let row = row(row_backend, [u64::MAX; 4]);
        let charge_request = VerifierCostQuoteRequestV1::from_test_parts(
            expected_backend,
            [u64::MAX, u64::MAX],
            [0, 0, u64::MAX, u64::MAX],
        );
        assert_eq!(
            model(u64::MAX)?.compute_quote(&row, &charge_request),
            Err(VerifierCostErrorV1::BackendFamilyMismatch)
        );
        Ok(())
    }

    #[test]
    fn artifact_bound_precedes_statement_bound_and_arithmetic() -> Result<(), TestError> {
        let backend = backend(1)?;
        let row = row(backend, [u64::MAX; 4]);
        let charge_request = VerifierCostQuoteRequestV1::from_test_parts(
            backend,
            [11, 11],
            [10, 10, u64::MAX, u64::MAX],
        );
        assert_eq!(
            model(u64::MAX)?.compute_quote(&row, &charge_request),
            Err(VerifierCostErrorV1::ArtifactBytesExceeded)
        );
        Ok(())
    }

    #[test]
    fn public_input_bound_precedes_arithmetic() -> Result<(), TestError> {
        let backend = backend(1)?;
        let row = row(backend, [u64::MAX; 4]);
        let charge_request = VerifierCostQuoteRequestV1::from_test_parts(
            backend,
            [10, 11],
            [10, 10, u64::MAX, u64::MAX],
        );
        assert_eq!(
            model(u64::MAX)?.compute_quote(&row, &charge_request),
            Err(VerifierCostErrorV1::PublicInputBytesExceeded)
        );
        Ok(())
    }

    #[test]
    fn exact_byte_and_charge_limits_are_accepted() -> Result<(), TestError> {
        let backend = backend(1)?;
        let row = row(backend, [4, 1, 1, 1]);
        let charge_request =
            VerifierCostQuoteRequestV1::from_test_parts(backend, [2, 3], [2, 3, 1, 10]);
        assert_eq!(model(10)?.compute_quote(&row, &charge_request)?.units(), 10);
        Ok(())
    }

    #[test]
    fn checked_sum_rejects_u128_overflow() -> Result<(), TestError> {
        let backend = backend(1)?;
        let row = row(backend, [u64::MAX; 4]);
        let charge_request = request(backend, [u64::MAX; 3], u64::MAX);
        assert_eq!(
            model(u64::MAX)?.compute_quote(&row, &charge_request),
            Err(VerifierCostErrorV1::ArithmeticOverflow)
        );
        Ok(())
    }

    #[test]
    fn charge_must_fit_u64() -> Result<(), TestError> {
        let backend = backend(1)?;
        let row = row(backend, [1, 1, 0, 0]);
        let charge_request = request(backend, [u64::MAX, 0, 0], u64::MAX);
        assert_eq!(
            model(u64::MAX)?.compute_quote(&row, &charge_request),
            Err(VerifierCostErrorV1::ChargeDoesNotFitU64)
        );
        Ok(())
    }

    #[test]
    fn model_charge_cap_is_enforced_before_verifier_cap() -> Result<(), TestError> {
        let backend = backend(1)?;
        let row = row(backend, [10, 0, 0, 0]);
        let charge_request = request(backend, [0, 0, 0], 8);
        assert_eq!(
            model(9)?.compute_quote(&row, &charge_request),
            Err(VerifierCostErrorV1::ModelChargeLimitExceeded)
        );
        Ok(())
    }

    #[test]
    fn verifier_policy_charge_cap_is_enforced() -> Result<(), TestError> {
        let backend = backend(1)?;
        let row = row(backend, [10, 0, 0, 0]);
        let charge_request = request(backend, [0, 0, 0], 9);
        assert_eq!(
            model(10)?.compute_quote(&row, &charge_request),
            Err(VerifierCostErrorV1::VerifierChargeLimitExceeded)
        );
        Ok(())
    }

    #[test]
    fn charge_is_monotone_in_every_billed_length() -> Result<(), TestError> {
        let backend = backend(1)?;
        let row = row(backend, [7, 3, 5, 11]);
        let model = model(u64::MAX)?;
        let baseline = model
            .compute_quote(&row, &request(backend, [4, 5, 6], u64::MAX))?
            .units();
        let artifact_increased = model
            .compute_quote(&row, &request(backend, [5, 5, 6], u64::MAX))?
            .units();
        let statement_increased = model
            .compute_quote(&row, &request(backend, [4, 6, 6], u64::MAX))?
            .units();
        let output_increased = model
            .compute_quote(&row, &request(backend, [4, 5, 7], u64::MAX))?
            .units();
        assert!(artifact_increased >= baseline);
        assert!(statement_increased >= baseline);
        assert!(output_increased >= baseline);
        Ok(())
    }

    #[test]
    fn reservation_dominates_every_sampled_bounded_actual_charge() -> Result<(), TestError> {
        let backend = backend(1)?;
        let row = row(backend, [7, 3, 5, 11]);
        let model = model(u64::MAX)?;
        let artifact_max = 100;
        let statement_max = 80;
        let output_max = 40;
        let reservation_request =
            request(backend, [artifact_max, statement_max, output_max], u64::MAX);
        let reservation = model.compute_quote(&row, &reservation_request)?.units();

        for artifact_len in [0, 1, artifact_max] {
            for canonical_statement_len in [0, 1, statement_max] {
                let actual_request = VerifierCostQuoteRequestV1::from_test_parts(
                    backend,
                    [artifact_len, canonical_statement_len],
                    [artifact_max, statement_max, output_max, u64::MAX],
                );
                let actual = model.compute_quote(&row, &actual_request)?.units();
                assert!(actual <= reservation);
            }
        }
        Ok(())
    }

    #[test]
    fn local_error_labels_are_bounded() {
        let cases = [
            (
                VerifierCostErrorV1::UnsupportedModelSchema,
                "zrm.policy.verifier_cost_model_schema",
            ),
            (
                VerifierCostErrorV1::BackendFamilyMismatch,
                "zrm.policy.verifier_cost_backend_mismatch",
            ),
            (
                VerifierCostErrorV1::ArtifactBytesExceeded,
                "zrm.bounds.verifier_artifact_bytes",
            ),
            (
                VerifierCostErrorV1::PublicInputBytesExceeded,
                "zrm.bounds.verifier_public_input_bytes",
            ),
            (
                VerifierCostErrorV1::ArithmeticOverflow,
                "zrm.policy.verifier_cost_arithmetic_overflow",
            ),
            (
                VerifierCostErrorV1::ChargeDoesNotFitU64,
                "zrm.policy.verifier_cost_u64_overflow",
            ),
            (
                VerifierCostErrorV1::ModelChargeLimitExceeded,
                "zrm.policy.verifier_cost_model_limit",
            ),
            (
                VerifierCostErrorV1::VerifierChargeLimitExceeded,
                "zrm.policy.verifier_cost_policy_limit",
            ),
        ];
        for (error, label) in cases {
            assert_eq!(error.label(), label);
            assert_eq!(std::format!("{error}"), label);
        }
    }
}

#[cfg(kani)]
mod kani_harnesses {
    use super::{
        VERIFIER_COST_MODEL_SCHEMA_V1, VerifierCostModelCandidateV1, VerifierCostModelV1,
        VerifierCostQuoteRequestV1, VerifierCostRowCandidateV1, VerifierCostRowV1,
    };
    use zrm_types::{BackendFamilyId, VerifierCostRowsRoot};

    fn fixed_backend() -> Option<BackendFamilyId> {
        BackendFamilyId::try_from([1; 32]).ok()
    }

    fn model(max_charge_units: u64) -> Option<VerifierCostModelV1> {
        let rows_root = VerifierCostRowsRoot::try_from([2; 32]).ok()?;
        VerifierCostModelV1::try_from(VerifierCostModelCandidateV1 {
            schema_version: VERIFIER_COST_MODEL_SCHEMA_V1,
            rows_root,
            max_charge_units,
        })
        .ok()
    }

    #[kani::proof]
    fn successful_charge_obeys_both_caps() {
        let Some(backend) = fixed_backend() else {
            return;
        };
        let model_cap: u64 = kani::any();
        let verifier_cap: u64 = kani::any();
        let Some(model) = model(model_cap) else {
            return;
        };
        let row = VerifierCostRowV1::new(VerifierCostRowCandidateV1 {
            backend_family_id: backend,
            base_units: 7,
            artifact_byte_units: 3,
            statement_byte_units: 5,
            reserved_output_byte_units: 11,
        });
        let artifact_len = u64::from(kani::any::<u8>());
        let statement_len = u64::from(kani::any::<u8>());
        let request = VerifierCostQuoteRequestV1::from_test_parts(
            backend,
            [artifact_len, statement_len],
            [
                artifact_len,
                statement_len,
                u64::from(kani::any::<u8>()),
                verifier_cap,
            ],
        );
        if let Ok(quote) = model.compute_quote(&row, &request) {
            assert!(quote.units() <= model_cap);
            assert!(quote.units() <= verifier_cap);
        }
    }

    #[kani::proof]
    fn reservation_dominates_bounded_actual_charge() {
        let Some(backend) = fixed_backend() else {
            return;
        };
        let Some(model) = model(u64::MAX) else {
            return;
        };
        let row = VerifierCostRowV1::new(VerifierCostRowCandidateV1 {
            backend_family_id: backend,
            base_units: 7,
            artifact_byte_units: 3,
            statement_byte_units: 5,
            reserved_output_byte_units: 11,
        });
        let artifact_max = kani::any::<u8>();
        let statement_max = kani::any::<u8>();
        let artifact_len = kani::any::<u8>();
        let statement_len = kani::any::<u8>();
        kani::assume(artifact_len <= artifact_max);
        kani::assume(statement_len <= statement_max);
        let reserved_output_byte_maximum = u64::from(kani::any::<u8>());
        let policy_bounds = [
            u64::from(artifact_max),
            u64::from(statement_max),
            reserved_output_byte_maximum,
            u64::MAX,
        ];
        let reservation_request = VerifierCostQuoteRequestV1::from_test_parts(
            backend,
            [u64::from(artifact_max), u64::from(statement_max)],
            policy_bounds,
        );
        let actual_request = VerifierCostQuoteRequestV1::from_test_parts(
            backend,
            [u64::from(artifact_len), u64::from(statement_len)],
            policy_bounds,
        );
        let reservation = model.compute_quote(&row, &reservation_request);
        let actual = model.compute_quote(&row, &actual_request);
        assert!(reservation.is_ok());
        assert!(actual.is_ok());
        if let (Ok(reservation), Ok(actual)) = (reservation, actual) {
            assert!(actual.units() <= reservation.units());
        }
    }
}
