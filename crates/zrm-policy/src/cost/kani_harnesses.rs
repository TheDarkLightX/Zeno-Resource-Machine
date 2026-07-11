use super::{
    VERIFIER_COST_MODEL_SCHEMA_V1, VerifierCostModelCandidateV1, VerifierCostModelV1,
    VerifierCostQuoteRequestV1, VerifierCostRowCandidateV1, VerifierCostRowV1,
};
use zrm_types::{BackendFamilyId, VerifierCostRowsRoot};

fn fixed_backend() -> BackendFamilyId {
    BackendFamilyId::try_from([1; 32]).expect("fixed backend fixture is nonzero")
}

fn model(max_charge_units: u64) -> VerifierCostModelV1 {
    let rows_root =
        VerifierCostRowsRoot::try_from([2; 32]).expect("fixed rows-root fixture is nonzero");
    VerifierCostModelV1::try_from(VerifierCostModelCandidateV1 {
        schema_version: VERIFIER_COST_MODEL_SCHEMA_V1,
        rows_root,
        max_charge_units,
    })
    .expect("version-one cost-model fixture is valid")
}

fn standard_row(backend_family_id: BackendFamilyId) -> VerifierCostRowV1 {
    VerifierCostRowV1::new(VerifierCostRowCandidateV1 {
        backend_family_id,
        base_units: 7,
        artifact_byte_units: 3,
        statement_byte_units: 5,
        reserved_output_byte_units: 11,
    })
}

fn request(
    backend_family_id: BackendFamilyId,
    lengths: [u64; 2],
    policy_bounds: [u64; 4],
) -> VerifierCostQuoteRequestV1 {
    VerifierCostQuoteRequestV1::from_test_parts(backend_family_id, lengths, policy_bounds)
}

#[kani::proof]
fn successful_charge_obeys_both_caps() {
    let backend = fixed_backend();
    let model_cap: u64 = kani::any();
    let verifier_cap: u64 = kani::any();
    let model = model(model_cap);
    let row = standard_row(backend);
    let artifact_len = u64::from(kani::any::<u8>());
    let statement_len = u64::from(kani::any::<u8>());
    let quote = model.compute_quote(
        &row,
        &request(
            backend,
            [artifact_len, statement_len],
            [
                artifact_len,
                statement_len,
                u64::from(kani::any::<u8>()),
                verifier_cap,
            ],
        ),
    );
    kani::cover!(quote.is_ok());
    kani::assume(quote.is_ok());
    let quote = quote.expect("the harness constrains this path to successful quotes");
    assert!(quote.units() <= model_cap);
    assert!(quote.units() <= verifier_cap);
}

#[kani::proof]
fn reservation_dominates_bounded_actual_charge() {
    let backend = fixed_backend();
    let model = model(u64::MAX);
    let row = standard_row(backend);
    let artifact_max = kani::any::<u8>();
    let statement_max = kani::any::<u8>();
    let artifact_len = kani::any::<u8>();
    let statement_len = kani::any::<u8>();
    kani::assume(artifact_len <= artifact_max);
    kani::assume(statement_len <= statement_max);
    let bounds = [
        u64::from(artifact_max),
        u64::from(statement_max),
        u64::from(kani::any::<u8>()),
        u64::MAX,
    ];
    let reservation = model
        .compute_quote(
            &row,
            &request(
                backend,
                [u64::from(artifact_max), u64::from(statement_max)],
                bounds,
            ),
        )
        .expect("bounded reservation fixture has no failing quote path");
    let actual = model
        .compute_quote(
            &row,
            &request(
                backend,
                [u64::from(artifact_len), u64::from(statement_len)],
                bounds,
            ),
        )
        .expect("bounded actual fixture has no failing quote path");
    kani::cover!(actual.units() < reservation.units());
    assert!(actual.units() <= reservation.units());
}
