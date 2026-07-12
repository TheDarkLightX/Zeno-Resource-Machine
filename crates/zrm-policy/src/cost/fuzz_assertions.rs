use super::{
    VerifierCostErrorV1, VerifierCostModelCandidateV1, VerifierCostModelV1,
    VerifierCostRowCandidateV1, VerifierCostRowV1,
};
use crate::{ProofModeV1, VerifierPolicyCandidateV1, VerifierPolicyV1};
use zrm_types::{BackendFamilyId, VerifierCostRowsRoot};

const REQUIRED_BYTES: usize = 88;

struct CostFuzzCase {
    model: VerifierCostModelV1,
    row: VerifierCostRowV1,
    policy: VerifierPolicyV1,
    lengths: [u64; 2],
    bounds: [u64; 4],
}

fn read_u64(data: &[u8], offset: usize) -> Option<u64> {
    let end = offset.checked_add(8)?;
    let bytes: [u8; 8] = data.get(offset..end)?.try_into().ok()?;
    Some(u64::from_be_bytes(bytes))
}

fn nonzero<T>(byte: u8) -> Option<T>
where
    T: TryFrom<[u8; 32]>,
{
    T::try_from([byte; 32]).ok()
}

fn fixed_cost_identities() -> Option<(BackendFamilyId, VerifierCostRowsRoot)> {
    Some((
        BackendFamilyId::try_from([1; 32]).ok()?,
        VerifierCostRowsRoot::try_from([2; 32]).ok()?,
    ))
}

fn cost_row(backend_family_id: BackendFamilyId, coefficients: [u64; 4]) -> VerifierCostRowV1 {
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

fn verifier_policy(
    backend_family_id: BackendFamilyId,
    maxima: [u64; 4],
) -> Option<VerifierPolicyV1> {
    let [
        max_artifact_bytes,
        max_public_input_bytes,
        max_public_output_bytes,
        max_cost,
    ] = maxima;
    VerifierPolicyV1::try_from(VerifierPolicyCandidateV1 {
        schema_version: 1,
        verifier_policy_id: nonzero(3)?,
        machine_id: nonzero(4)?,
        domain_id: nonzero(5)?,
        backend_family_id,
        verifier_id: nonzero(6)?,
        program_or_key_digest: nonzero(7)?,
        artifact_codec_id: nonzero(8)?,
        statement_schema_root: nonzero(9)?,
        journal_schema_root: nonzero(10)?,
        proof_parameter_root: nonzero(11)?,
        proof_mode: ProofModeV1::Production,
        coverage_claims_root: nonzero(12)?,
        non_claims_root: nonzero(13)?,
        trusted_computing_base_root: nonzero(14)?,
        verifier_cost_model_id: nonzero(15)?,
        max_verifier_cost_units: max_cost,
        max_artifact_bytes,
        max_public_input_bytes,
        max_public_output_bytes,
        validity_start_epoch: 0,
        validity_end_epoch: u64::MAX,
    })
    .ok()
}

/// Asserts invariants over quarantined candidate arithmetic without returning a quote.
///
/// The function is publicly re-exported only under `cfg(fuzzing)`. Its sole
/// observable result is success or an assertion failure. It constructs no
/// capability and discloses no calculated cost.
///
/// # Panics
///
/// Panics only when a checked internal invariant is falsified. Cargo Fuzz
/// treats that panic as a discovered counterexample.
///
/// # Side effects and complexity
///
/// The function performs no I/O, allocation, persistence, verifier dispatch,
/// or authority transition. It reads at most the first 88 bytes and performs a
/// fixed number of checked integer operations, so its time and memory use are
/// `O(1)` in the input length.
pub fn fuzz_assert_untrusted_candidate_cost_invariants(data: &[u8]) {
    let Some(case) = cost_fuzz_case(data) else {
        return;
    };
    assert_candidate_results(&case);
}

fn cost_fuzz_case(data: &[u8]) -> Option<CostFuzzCase> {
    let values = read_values(data)?;
    let (backend, rows_root) = fixed_cost_identities()?;
    let [
        base,
        artifact_units,
        statement_units,
        output_units,
        artifact_max,
        statement_max,
        output_max,
        model_cap,
        verifier_cap,
        artifact_len,
        statement_len,
    ] = values;

    let row = cost_row(
        backend,
        [base, artifact_units, statement_units, output_units],
    );
    let model = VerifierCostModelV1::try_from(VerifierCostModelCandidateV1 {
        schema_version: 1,
        rows_root,
        max_charge_units: model_cap,
    })
    .ok()?;
    let policy = verifier_policy(
        backend,
        [artifact_max, statement_max, output_max, verifier_cap],
    )?;
    Some(CostFuzzCase {
        model,
        row,
        policy,
        lengths: [artifact_len, statement_len],
        bounds: [artifact_max, statement_max, model_cap, verifier_cap],
    })
}

fn read_values(data: &[u8]) -> Option<[u64; 11]> {
    if data.len() < REQUIRED_BYTES {
        return None;
    }
    Some([
        read_u64(data, 0)?,
        read_u64(data, 8)?,
        read_u64(data, 16)?,
        read_u64(data, 24)?,
        read_u64(data, 32)?,
        read_u64(data, 40)?,
        read_u64(data, 48)?,
        read_u64(data, 56)?,
        read_u64(data, 64)?,
        read_u64(data, 72)?,
        read_u64(data, 80)?,
    ])
}

fn assert_candidate_results(case: &CostFuzzCase) {
    let [artifact_len, statement_len] = case.lengths;
    let [artifact_max, statement_max, model_cap, verifier_cap] = case.bounds;
    let raw_request = case
        .policy
        .candidate_cost_quote_request(artifact_len, statement_len);
    let first = case
        .model
        .compute_untrusted_candidate_quote(&case.row, &raw_request);
    let second = case
        .model
        .compute_untrusted_candidate_quote(&case.row, &raw_request);
    assert_eq!(first, second);
    if artifact_len > artifact_max {
        assert_eq!(first, Err(VerifierCostErrorV1::ArtifactBytesExceeded));
    } else if statement_len > statement_max {
        assert_eq!(first, Err(VerifierCostErrorV1::PublicInputBytesExceeded));
    }

    let bounded_request = case.policy.candidate_cost_quote_request(
        artifact_len.min(artifact_max),
        statement_len.min(statement_max),
    );
    let reservation_request = case.policy.candidate_admission_reservation_request();
    let bounded = case
        .model
        .compute_untrusted_candidate_quote(&case.row, &bounded_request);
    let reservation = case
        .model
        .compute_untrusted_candidate_quote(&case.row, &reservation_request);
    if let (Ok(actual), Ok(reserved)) = (bounded, reservation) {
        assert!(actual.units() <= reserved.units());
        assert!(actual.units() <= model_cap);
        assert!(actual.units() <= verifier_cap);
    }
}
