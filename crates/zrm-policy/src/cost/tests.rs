use super::{
    VERIFIER_COST_MODEL_SCHEMA_V1, VerifierCostErrorV1, VerifierCostModelCandidateV1,
    VerifierCostModelV1, VerifierCostQuoteRequestV1, VerifierCostRowCandidateV1, VerifierCostRowV1,
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
    let reservation_request = request(backend, [artifact_max, statement_max, output_max], u64::MAX);
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
